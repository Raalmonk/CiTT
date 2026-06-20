from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.models.circuit_ir import CircuitProblem, Component, is_op_amp_type
from app.models.lab import (
    LabAppliedModification,
    LabComparison,
    LabCounterfactual,
    LabObservation,
    LabScenario,
    LabSensitivityPoint,
    LabSensitivitySweep,
    LabSimulationRequest,
    LabSimulationResponse,
)
from app.models.solution_packet import ComplexQuantityValue, QuantityValue, SolutionPacket
from app.services.mna_solver import nonideal_output_window
from app.services.pipeline import solve_circuit


@dataclass(frozen=True)
class ScalarOutput:
    id: str
    label: str
    source: str
    value: float
    unit: str


@dataclass(frozen=True)
class SweepSelection:
    id: str
    label: str
    x_label: str
    x_unit: str
    values: list[float]
    kind: str
    target: str | None = None


def simulate_lab(request: LabSimulationRequest) -> LabSimulationResponse:
    baseline_packet = request.baseline_packet or solve_circuit(
        request.circuit_ir,
        parser_used=request.parser_used,
    )
    applied: list[LabAppliedModification] = []
    lab_circuit = _build_lab_circuit(request.circuit_ir, request.scenario, applied)
    lab_packet = solve_circuit(lab_circuit, parser_used="lab_simulator")
    comparisons = _build_comparisons(
        baseline_packet,
        lab_packet,
        request.scenario,
    )
    observations = _build_observations(
        lab_circuit=lab_circuit,
        baseline_packet=baseline_packet,
        lab_packet=lab_packet,
        scenario=request.scenario,
        applied=applied,
        comparisons=comparisons,
    )
    sensitivity_sweeps = _build_sensitivity_sweeps(
        request.circuit_ir,
        baseline_packet,
        request.scenario,
    )
    counterfactuals = _build_counterfactuals(
        request.circuit_ir,
        baseline_packet,
        request.scenario,
        comparisons,
    )

    return LabSimulationResponse(
        baseline_packet=baseline_packet,
        lab_packet=lab_packet,
        lab_circuit=lab_circuit,
        applied_modifications=applied,
        comparisons=comparisons,
        observations=observations,
        sensitivity_sweeps=sensitivity_sweeps,
        counterfactuals=counterfactuals,
        teaching_script=_teaching_script(request.scenario, comparisons),
        warnings=[*baseline_packet.warnings, *lab_packet.warnings],
    )


def _build_lab_circuit(
    circuit: CircuitProblem,
    scenario: LabScenario,
    applied: list[LabAppliedModification],
) -> CircuitProblem:
    lab = circuit.model_copy(deep=True)
    lab.assumptions = [
        *lab.assumptions,
        "Lab scenario: component, source, op-amp, breadboard, and readout errors are explicit model inputs.",
    ]

    _apply_component_errors(lab, scenario, applied)
    _apply_source_generation_errors(lab, scenario, applied)
    _apply_op_amp_nonidealities(lab, scenario, applied)
    if scenario.enable_bias_compensation:
        _add_bias_compensation_resistors(lab, applied)
    _add_breadboard_parasitics(lab, scenario, applied)
    _record_readout_model(scenario, applied)

    return CircuitProblem.model_validate(lab.model_dump())


def _apply_component_errors(
    circuit: CircuitProblem,
    scenario: LabScenario,
    applied: list[LabAppliedModification],
) -> None:
    for component in circuit.components:
        percent: float | None = None
        if component.type == "resistor":
            percent = scenario.resistor_tolerance_percent
        elif component.type == "capacitor":
            percent = scenario.capacitor_tolerance_percent
        elif component.type == "inductor":
            percent = scenario.inductor_tolerance_percent

        if component.id in scenario.component_value_error_percent:
            specific = scenario.component_value_error_percent[component.id]
            percent = (percent or 0.0) + specific

        if percent is None or abs(percent) < 1e-15:
            continue
        if component.type not in {"resistor", "capacitor", "inductor"}:
            continue

        before = component.value
        after = before * (1.0 + percent / 100.0)
        if after <= 0 or not math.isfinite(after):
            raise ValueError(
                f"{component.id} would become an invalid {component.type} value after {percent:g}% error."
            )
        component.value = after
        applied.append(
            LabAppliedModification(
                id=f"value_error_{component.id}",
                kind="component_value",
                target=component.id,
                before_value=before,
                after_value=after,
                unit=component.unit,
                note=f"{component.id} {component.type} value shifted by {percent:g}%.",
            )
        )


def _apply_source_generation_errors(
    circuit: CircuitProblem,
    scenario: LabScenario,
    applied: list[LabAppliedModification],
) -> None:
    percent = scenario.source_amplitude_error_percent
    offset = scenario.source_dc_offset_v or 0.0
    if (percent is None or abs(percent) < 1e-15) and abs(offset) < 1e-15:
        return

    for component in circuit.components:
        if component.type not in {"voltage_source", "current_source"}:
            continue
        before = component.value
        after = before
        if percent is not None:
            after *= 1.0 + percent / 100.0
            if component.ac_magnitude is not None:
                component.ac_magnitude *= 1.0 + percent / 100.0
        if component.type == "voltage_source":
            after += offset
        component.value = after
        applied.append(
            LabAppliedModification(
                id=f"source_error_{component.id}",
                kind="source_generation",
                target=component.id,
                before_value=before,
                after_value=after,
                unit=component.unit,
                note=(
                    f"{component.id} source generated with "
                    f"{0.0 if percent is None else percent:g}% gain error"
                    + (f" and {offset:g} V DC offset." if component.type == "voltage_source" else ".")
                ),
            )
        )


def _apply_op_amp_nonidealities(
    circuit: CircuitProblem,
    scenario: LabScenario,
    applied: list[LabAppliedModification],
) -> None:
    op_amp_fields_requested = any(
        value is not None
        for value in [
            scenario.op_amp_input_bias_current_a,
            scenario.op_amp_input_offset_voltage_v,
            scenario.op_amp_open_loop_gain,
            scenario.supply_positive_v,
            scenario.supply_negative_v,
            scenario.output_swing_margin_v,
            scenario.slew_rate_v_per_s,
        ]
    )
    if not op_amp_fields_requested:
        return

    for component in circuit.components:
        if not is_op_amp_type(component.type):
            continue
        before_gain = component.open_loop_gain
        if component.type in {"op_amp_ideal", "ideal_op_amp"}:
            component.type = "nonideal_op_amp"
            component.unit = "model"
        if component.open_loop_gain is None:
            component.open_loop_gain = scenario.op_amp_open_loop_gain or 100_000.0
        elif scenario.op_amp_open_loop_gain is not None:
            component.open_loop_gain = scenario.op_amp_open_loop_gain

        if scenario.op_amp_input_bias_current_a is not None:
            component.input_bias_current_a = scenario.op_amp_input_bias_current_a
        if scenario.op_amp_input_offset_voltage_v is not None:
            component.input_offset_voltage_v = scenario.op_amp_input_offset_voltage_v
        if scenario.supply_positive_v is not None:
            component.supply_positive_v = scenario.supply_positive_v
        if scenario.supply_negative_v is not None:
            component.supply_negative_v = scenario.supply_negative_v
        if scenario.output_swing_margin_v is not None:
            component.output_swing_margin_v = scenario.output_swing_margin_v
        if scenario.slew_rate_v_per_s is not None:
            component.slew_rate_v_per_s = scenario.slew_rate_v_per_s

        applied.append(
            LabAppliedModification(
                id=f"opamp_nonideal_{component.id}",
                kind="op_amp_nonideality",
                target=component.id,
                before_value=before_gain,
                after_value=component.open_loop_gain,
                unit="V/V",
                note=(
                    f"{component.id} solved as a finite-gain nonideal op-amp"
                    + (
                        f" with {component.input_bias_current_a:g} A input bias current."
                        if component.input_bias_current_a is not None
                        else "."
                    )
                ),
            )
        )


def _add_bias_compensation_resistors(
    circuit: CircuitProblem,
    applied: list[LabAppliedModification],
) -> None:
    existing_ids = {component.id for component in circuit.components}
    additions: list[Component] = []
    for op_amp in [component for component in circuit.components if is_op_amp_type(component.type)]:
        if len(op_amp.nodes) != 4:
            continue
        vp, vm, _out, ref = op_amp.nodes
        resistance = _parallel_resistance_touching_node(circuit, vm)
        if resistance is None:
            continue
        component_id = _unique_component_id(f"RB_{op_amp.id}_bias", existing_ids)
        existing_ids.add(component_id)
        additions.append(
            Component(
                id=component_id,
                type="resistor",
                nodes=[vp, ref],
                value=resistance,
                unit="ohm",
                label=f"{op_amp.id} input-bias balance resistor",
                current_reference={"from_node": vp, "to_node": ref},
                voltage_reference={"positive_node": vp, "negative_node": ref},
            )
        )
        applied.append(
            LabAppliedModification(
                id=f"bias_comp_{op_amp.id}",
                kind="bias_compensation",
                target=op_amp.id,
                before_value=None,
                after_value=resistance,
                unit="ohm",
                note=(
                    f"Added {component_id} = {resistance:.6g} ohm from the non-inverting "
                    f"input to reference to match the resistance seen by the inverting input."
                ),
            )
        )
    circuit.components.extend(additions)


def _parallel_resistance_touching_node(
    circuit: CircuitProblem,
    node: str,
) -> float | None:
    conductance = 0.0
    for component in circuit.components:
        if component.type != "resistor" or node not in component.nodes or component.value <= 0:
            continue
        conductance += 1.0 / component.value
    if conductance <= 0:
        return None
    return 1.0 / conductance


def _add_breadboard_parasitics(
    circuit: CircuitProblem,
    scenario: LabScenario,
    applied: list[LabAppliedModification],
) -> None:
    leakage = scenario.breadboard_leakage_ohm
    shunt_capacitance = scenario.breadboard_shunt_capacitance_f
    if leakage is None and shunt_capacitance is None:
        return

    existing_ids = {component.id for component in circuit.components}
    additions: list[Component] = []
    for node in circuit.nodes:
        if node == circuit.ground_node:
            continue
        safe_node = _safe_id(node)
        if leakage is not None:
            component_id = _unique_component_id(f"RBB_{safe_node}", existing_ids)
            existing_ids.add(component_id)
            additions.append(
                Component(
                    id=component_id,
                    type="resistor",
                    nodes=[node, circuit.ground_node],
                    value=leakage,
                    unit="ohm",
                    label=f"Breadboard leakage from {node}",
                    current_reference={"from_node": node, "to_node": circuit.ground_node},
                    voltage_reference={
                        "positive_node": node,
                        "negative_node": circuit.ground_node,
                    },
                )
            )
        if shunt_capacitance is not None:
            component_id = _unique_component_id(f"CBB_{safe_node}", existing_ids)
            existing_ids.add(component_id)
            additions.append(
                Component(
                    id=component_id,
                    type="capacitor",
                    nodes=[node, circuit.ground_node],
                    value=shunt_capacitance,
                    unit="F",
                    label=f"Breadboard shunt capacitance at {node}",
                )
            )
    circuit.components.extend(additions)
    if leakage is not None:
        applied.append(
            LabAppliedModification(
                id="breadboard_leakage",
                kind="breadboard_parasitic",
                target="all non-ground nodes",
                after_value=leakage,
                unit="ohm",
                note=f"Added leakage resistors from every non-ground node to ground ({leakage:.6g} ohm each).",
            )
        )
    if shunt_capacitance is not None:
        applied.append(
            LabAppliedModification(
                id="breadboard_capacitance",
                kind="breadboard_parasitic",
                target="all non-ground nodes",
                after_value=shunt_capacitance,
                unit="F",
                note=(
                    "Added shunt capacitance from every non-ground node to ground "
                    f"({shunt_capacitance:.6g} F each)."
                ),
            )
        )


def _record_readout_model(
    scenario: LabScenario,
    applied: list[LabAppliedModification],
) -> None:
    gain = scenario.readout_gain_error_percent
    offset = scenario.readout_offset_v
    if (gain is None or abs(gain) < 1e-15) and (offset is None or abs(offset) < 1e-15):
        return
    applied.append(
        LabAppliedModification(
            id="measurement_readout",
            kind="measurement_readout",
            target="displayed measurements",
            after_value=gain,
            unit="%",
            note=(
                f"Readout model applies {0.0 if gain is None else gain:g}% gain error"
                + (f" and {offset:g} V offset to voltage displays." if offset else ".")
            ),
        )
    )


def _build_comparisons(
    baseline_packet: SolutionPacket,
    lab_packet: SolutionPacket,
    scenario: LabScenario,
) -> list[LabComparison]:
    baseline_outputs = {output.id: output for output in _scalar_outputs(baseline_packet)}
    lab_outputs = {output.id: output for output in _scalar_outputs(lab_packet)}
    comparisons: list[LabComparison] = []
    for output_id, baseline in baseline_outputs.items():
        lab = lab_outputs.get(output_id)
        if lab is None:
            continue
        measured = _measured_value(lab.value, lab.unit, scenario)
        delta = lab.value - baseline.value
        relative = None
        if abs(baseline.value) > 1e-15:
            relative = delta / baseline.value * 100.0
        comparisons.append(
            LabComparison(
                id=output_id,
                label=baseline.label,
                source=baseline.source,  # type: ignore[arg-type]
                unit=baseline.unit,
                baseline_value=baseline.value,
                lab_value=lab.value,
                measured_value=measured,
                delta=delta,
                relative_error_percent=relative,
                note=_comparison_note(baseline, lab, measured),
            )
        )
        if len(comparisons) >= 10:
            break
    return comparisons


def _scalar_outputs(packet: SolutionPacket) -> list[ScalarOutput]:
    outputs: list[ScalarOutput] = []
    outputs.extend(
        _quantity_outputs(
            values=packet.requested_answers,
            label_prefix="Requested",
            source="requested_answer",
        )
    )
    outputs.extend(
        _complex_outputs(
            values=packet.ac_requested_answers,
            label_prefix="Requested magnitude",
            source="ac_requested_answer",
        )
    )

    if not outputs:
        outputs.extend(
            ScalarOutput(
                id=f"node_{node}",
                label=f"Node {node}",
                source="node_voltage",
                value=value,
                unit="V",
            )
            for node, value in sorted(packet.node_voltages.items())
        )
        outputs.extend(
            ScalarOutput(
                id=f"ac_node_{node}",
                label=f"Node {node} magnitude",
                source="ac_node_voltage",
                value=value.magnitude,
                unit=value.unit,
            )
            for node, value in sorted(packet.ac_node_voltages.items())
        )

    if packet.transient_response is not None:
        response = packet.transient_response
        outputs.append(
            ScalarOutput(
                id="transient_final_voltage",
                label="Transient final voltage",
                source="transient",
                value=response.final_voltage_v,
                unit="V",
            )
        )
        outputs.append(
            ScalarOutput(
                id="transient_time_constant",
                label="Transient time constant",
                source="transient",
                value=response.time_constant_s,
                unit="s",
            )
        )

    # Add a few node voltages even when requested answers exist, because lab
    # debugging often starts by asking which internal node moved.
    if packet.node_voltages and len(outputs) < 6:
        existing = {output.id for output in outputs}
        for node, value in sorted(packet.node_voltages.items()):
            output_id = f"node_{node}"
            if output_id in existing:
                continue
            outputs.append(
                ScalarOutput(
                    id=output_id,
                    label=f"Node {node}",
                    source="node_voltage",
                    value=value,
                    unit="V",
                )
            )
            if len(outputs) >= 6:
                break
    return outputs


def _quantity_outputs(
    values: dict[str, QuantityValue],
    label_prefix: str,
    source: str,
) -> list[ScalarOutput]:
    return [
        ScalarOutput(
            id=output_id,
            label=f"{label_prefix} {output_id}",
            source=source,
            value=value.value,
            unit=value.unit,
        )
        for output_id, value in values.items()
    ]


def _complex_outputs(
    values: dict[str, ComplexQuantityValue],
    label_prefix: str,
    source: str,
) -> list[ScalarOutput]:
    return [
        ScalarOutput(
            id=output_id,
            label=f"{label_prefix} {output_id}",
            source=source,
            value=value.magnitude,
            unit=value.unit,
        )
        for output_id, value in values.items()
    ]


def _measured_value(value: float, unit: str, scenario: LabScenario) -> float:
    measured = value
    gain = scenario.readout_gain_error_percent
    if gain is not None:
        measured *= 1.0 + gain / 100.0
    if unit == "V" and scenario.readout_offset_v is not None:
        measured += scenario.readout_offset_v
    return measured


def _comparison_note(
    baseline: ScalarOutput,
    lab: ScalarOutput,
    measured: float,
) -> str:
    if abs(measured - lab.value) > max(1e-12, abs(lab.value) * 1e-9):
        return "Measured includes instrument readout error; lab value is the circuit truth."
    if abs(lab.value - baseline.value) > max(1e-12, abs(baseline.value) * 1e-9):
        return "Lab value changed because the circuit model was perturbed."
    return "No visible scalar shift for this output under the current scenario."


def _build_sensitivity_sweeps(
    circuit: CircuitProblem,
    baseline_packet: SolutionPacket,
    scenario: LabScenario,
) -> list[LabSensitivitySweep]:
    selection = _primary_sweep_selection(scenario)
    if selection is None:
        return []

    points: list[LabSensitivityPoint] = []
    comparison_id: str | None = None
    y_label: str | None = None
    y_unit: str | None = None

    for x_value in selection.values:
        variant = scenario.model_copy(deep=True)
        _set_sweep_value(variant, selection, x_value)
        applied: list[LabAppliedModification] = []
        lab_circuit = _build_lab_circuit(circuit, variant, applied)
        lab_packet = solve_circuit(
            lab_circuit,
            parser_used=f"lab_sensitivity_{selection.id}",
        )
        comparisons = _build_comparisons(baseline_packet, lab_packet, variant)
        comparison = _primary_comparison(comparisons)
        if comparison is None:
            continue
        comparison_id = comparison_id or comparison.id
        if comparison.id != comparison_id:
            continue
        y_label = y_label or comparison.label
        y_unit = y_unit or comparison.unit
        points.append(
            LabSensitivityPoint(
                x_value=x_value,
                lab_value=comparison.lab_value,
                measured_value=comparison.measured_value,
                delta=comparison.delta,
                relative_error_percent=comparison.relative_error_percent,
            )
        )

    if len(points) < 2 or comparison_id is None or y_label is None or y_unit is None:
        return []

    return [
        LabSensitivitySweep(
            id=f"sweep_{selection.id}",
            label=selection.label,
            x_label=selection.x_label,
            x_unit=selection.x_unit,
            y_label=y_label,
            y_unit=y_unit,
            comparison_id=comparison_id,
            points=points,
            insight=_sweep_insight(selection, points, y_unit),
        )
    ]


def _build_counterfactuals(
    circuit: CircuitProblem,
    baseline_packet: SolutionPacket,
    scenario: LabScenario,
    compensated_comparisons: list[LabComparison],
) -> list[LabCounterfactual]:
    if not scenario.enable_bias_compensation:
        return []
    if scenario.op_amp_input_bias_current_a is None and scenario.op_amp_input_offset_voltage_v is None:
        return []

    no_comp_scenario = scenario.model_copy(
        deep=True,
        update={"enable_bias_compensation": False},
    )
    applied: list[LabAppliedModification] = []
    no_comp_circuit = _build_lab_circuit(circuit, no_comp_scenario, applied)
    no_comp_packet = solve_circuit(no_comp_circuit, parser_used="lab_counterfactual_no_bias_comp")
    no_comp_comparisons = _build_comparisons(
        baseline_packet,
        no_comp_packet,
        no_comp_scenario,
    )
    summary = _bias_counterfactual_summary(no_comp_comparisons, compensated_comparisons)
    return [
        LabCounterfactual(
            id="without_bias_compensation",
            label="Bias compensation off",
            summary=summary,
            comparisons=no_comp_comparisons,
            applied_modifications=applied,
        )
    ]


def _primary_sweep_selection(scenario: LabScenario) -> SweepSelection | None:
    component_target = next(iter(scenario.component_value_error_percent), None)
    if component_target is not None:
        base = scenario.component_value_error_percent[component_target]
        span = max(abs(base), 5.0)
        return SweepSelection(
            id=f"component_error_{component_target}",
            label=f"{component_target} value-error sensitivity",
            x_label=f"{component_target} error",
            x_unit="%",
            values=_linear_percent_values(-span, span),
            kind="component_value_error_percent",
            target=component_target,
        )

    if scenario.resistor_tolerance_percent is not None:
        span = max(abs(scenario.resistor_tolerance_percent), 5.0)
        return SweepSelection(
            id="resistor_tolerance",
            label="Resistor drift sensitivity",
            x_label="resistor drift",
            x_unit="%",
            values=_linear_percent_values(-span, span),
            kind="resistor_tolerance_percent",
        )

    if scenario.source_amplitude_error_percent is not None:
        span = max(abs(scenario.source_amplitude_error_percent), 5.0)
        return SweepSelection(
            id="source_gain_error",
            label="Source gain sensitivity",
            x_label="source gain error",
            x_unit="%",
            values=_linear_percent_values(-span, span),
            kind="source_amplitude_error_percent",
        )

    if scenario.op_amp_input_bias_current_a is not None:
        base = scenario.op_amp_input_bias_current_a
        if abs(base) < 1e-15:
            return None
        return SweepSelection(
            id="op_amp_bias_current",
            label="Input-bias-current sensitivity",
            x_label="input bias current",
            x_unit="A",
            values=[base * factor for factor in [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]],
            kind="op_amp_input_bias_current_a",
        )

    if scenario.breadboard_leakage_ohm is not None:
        base = scenario.breadboard_leakage_ohm
        return SweepSelection(
            id="breadboard_leakage",
            label="Breadboard leakage sensitivity",
            x_label="leakage resistance",
            x_unit="ohm",
            values=[base * factor for factor in [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]],
            kind="breadboard_leakage_ohm",
        )

    if scenario.readout_gain_error_percent is not None:
        span = max(abs(scenario.readout_gain_error_percent), 2.0)
        return SweepSelection(
            id="readout_gain_error",
            label="Readout gain-error sensitivity",
            x_label="meter gain error",
            x_unit="%",
            values=_linear_percent_values(-span, span),
            kind="readout_gain_error_percent",
        )

    return None


def _linear_percent_values(start: float, stop: float) -> list[float]:
    start = max(start, -95.0)
    if stop <= start:
        stop = start + 1.0
    steps = 8
    return [start + (stop - start) * index / steps for index in range(steps + 1)]


def _set_sweep_value(
    scenario: LabScenario,
    selection: SweepSelection,
    value: float,
) -> None:
    if selection.kind == "component_value_error_percent" and selection.target is not None:
        scenario.component_value_error_percent = {selection.target: value}
    elif selection.kind == "resistor_tolerance_percent":
        scenario.resistor_tolerance_percent = value
    elif selection.kind == "source_amplitude_error_percent":
        scenario.source_amplitude_error_percent = value
    elif selection.kind == "op_amp_input_bias_current_a":
        scenario.op_amp_input_bias_current_a = value
    elif selection.kind == "breadboard_leakage_ohm":
        scenario.breadboard_leakage_ohm = value
    elif selection.kind == "readout_gain_error_percent":
        scenario.readout_gain_error_percent = value


def _primary_comparison(comparisons: list[LabComparison]) -> LabComparison | None:
    if not comparisons:
        return None
    requested = [comparison for comparison in comparisons if "requested" in comparison.source]
    return requested[0] if requested else comparisons[0]


def _sweep_insight(
    selection: SweepSelection,
    points: list[LabSensitivityPoint],
    y_unit: str,
) -> str:
    start = points[0]
    end = points[-1]
    moved = end.lab_value - start.lab_value
    if abs(moved) < 1e-12:
        return f"Sweeping {selection.x_label} did not visibly move this solved quantity."
    direction = "increased" if moved > 0 else "decreased"
    return (
        f"Across this sweep, the solved quantity {direction} by "
        f"{moved:.6g} {y_unit}; ask the student which physical path gives that sign."
    )


def _bias_counterfactual_summary(
    no_comp: list[LabComparison],
    compensated: list[LabComparison],
) -> str:
    no_comp_primary = _primary_comparison(no_comp)
    comp_primary = _primary_comparison(compensated)
    if no_comp_primary is None or comp_primary is None:
        return "Run with and without the balancing resistor to compare whether input-bias error has a visible output path."
    before = abs(no_comp_primary.delta)
    after = abs(comp_primary.delta)
    if after < before:
        return (
            f"The balancing resistor reduced the absolute shift in {comp_primary.label} "
            f"from {before:.6g} {comp_primary.unit} to {after:.6g} {comp_primary.unit}."
        )
    if after > before:
        return (
            f"The balancing resistor made {comp_primary.label} shift more in this topology. "
            "That usually means another low-impedance source or mismatch dominates the bias-current story."
        )
    return (
        f"The balancing resistor did not change {comp_primary.label} in this topology; "
        "look for an ideal source or very low resistance clamping one input."
    )


def _build_observations(
    lab_circuit: CircuitProblem,
    baseline_packet: SolutionPacket,
    lab_packet: SolutionPacket,
    scenario: LabScenario,
    applied: list[LabAppliedModification],
    comparisons: list[LabComparison],
) -> list[LabObservation]:
    observations: list[LabObservation] = []
    if not applied:
        observations.append(
            LabObservation(
                id="no_error_sources",
                severity="notice",
                title="No error source is active",
                body="Turn on at least one tolerance, source, op-amp, breadboard, or readout parameter before using the lab as a prediction check.",
            )
        )

    if lab_packet.verification_badge.label != "PASS":
        observations.append(
            LabObservation(
                id="lab_solve_failed",
                severity="failure",
                title="Lab scenario broke the solvable model",
                body=lab_packet.verification_badge.message,
            )
        )

    largest = _largest_comparison(comparisons)
    if largest is not None:
        observations.append(
            LabObservation(
                id="largest_shift",
                severity="watch" if abs(largest.delta) > 1e-9 else "notice",
                title="Largest visible shift",
                body=(
                    f"{largest.label} moved by {largest.delta:.6g} {largest.unit}. "
                    "Ask first whether the sign matches the physical story, then look at the percentage."
                ),
                value=largest.delta,
                unit=largest.unit,
            )
        )

    op_amps = [component for component in lab_circuit.components if is_op_amp_type(component.type)]
    if scenario.op_amp_input_bias_current_a is not None:
        observations.append(
            LabObservation(
                id="input_bias_current",
                severity="watch",
                title="Input bias current became a circuit current",
                body=(
                    "The op-amp input current is stamped into both input nodes. It only becomes a voltage error "
                    "when the surrounding resistance gives that current somewhere resistive to flow."
                ),
                value=scenario.op_amp_input_bias_current_a,
                unit="A",
                focus_component_ids=[component.id for component in op_amps],
            )
        )

    bias_mods = [item for item in applied if item.kind == "bias_compensation"]
    if scenario.enable_bias_compensation:
        observations.append(
            LabObservation(
                id="bias_compensation",
                severity="success" if bias_mods else "notice",
                title="Bias-current cancellation rule",
                body=(
                    "The lab estimates the resistance seen by the inverting input and adds the same resistance at the non-inverting input. "
                    "This creates matching bias-current voltage drops; if an ideal voltage source clamps an input, add source resistance to see the effect numerically."
                ),
                value=bias_mods[0].after_value if bias_mods else None,
                unit=bias_mods[0].unit if bias_mods else None,
                focus_component_ids=[item.target for item in bias_mods],
            )
        )

    saturation_warnings = [warning for warning in lab_packet.warnings if "saturated" in warning.lower()]
    if saturation_warnings:
        observations.append(
            LabObservation(
                id="op_amp_saturation",
                severity="failure",
                title="Op-amp output hit the rail model",
                body=saturation_warnings[0],
                focus_component_ids=[component.id for component in op_amps],
            )
        )
    else:
        observations.extend(_rail_window_observations(lab_circuit, lab_packet))

    if scenario.breadboard_leakage_ohm is not None:
        observations.append(
            LabObservation(
                id="breadboard_leakage",
                severity=_breadboard_leakage_severity(lab_circuit, scenario.breadboard_leakage_ohm),
                title="Breadboard leakage loads every high-impedance node",
                body=(
                    "The lab adds a resistor from each non-ground node to ground. This matters most when the circuit already uses large resistors or very small currents."
                ),
                value=scenario.breadboard_leakage_ohm,
                unit="ohm",
                focus_node_ids=[node for node in lab_circuit.nodes if node != lab_circuit.ground_node],
            )
        )

    if scenario.breadboard_shunt_capacitance_f is not None:
        observations.append(
            LabObservation(
                id="breadboard_capacitance",
                severity="notice" if lab_circuit.analysis_type == "dc_operating_point" else "watch",
                title="Breadboard capacitance is frequency dependent",
                body=(
                    "In DC operating point it is an open circuit. In AC or transient views it creates a real extra pole or settling tail."
                ),
                value=scenario.breadboard_shunt_capacitance_f,
                unit="F",
            )
        )

    if (
        scenario.readout_gain_error_percent is not None
        or scenario.readout_offset_v is not None
    ):
        observations.append(
            LabObservation(
                id="readout_vs_truth",
                severity="notice",
                title="Separate circuit truth from instrument display",
                body=(
                    "The lab packet keeps the solved circuit value and the measured readout value separate, because a wrong meter reading should not be mistaken for a changed circuit."
                ),
            )
        )

    if (
        scenario.source_amplitude_error_percent is not None
        or scenario.source_dc_offset_v is not None
    ):
        observations.append(
            LabObservation(
                id="source_generation_error",
                severity="watch",
                title="Signal generation error changes the stimulus",
                body=(
                    "This is upstream of the circuit. For linear circuits, many outputs move with it; for saturated circuits, the output may stop following."
                ),
            )
        )

    if baseline_packet.verification_badge.label != "PASS":
        observations.append(
            LabObservation(
                id="baseline_not_verified",
                severity="watch",
                title="Baseline was not verified",
                body="Treat lab comparisons cautiously until the original circuit passes the solver checks.",
            )
        )

    return observations


def _rail_window_observations(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[LabObservation]:
    observations: list[LabObservation] = []
    for component in circuit.components:
        if not is_op_amp_type(component.type):
            continue
        window = nonideal_output_window(component)
        if window is None or len(component.nodes) != 4:
            continue
        output_node = component.nodes[2]
        output = packet.node_voltages.get(output_node)
        if output is None:
            continue
        low, high = window
        span = max(high - low, 1e-12)
        margin = min(abs(output - low), abs(high - output))
        if margin / span < 0.08:
            observations.append(
                LabObservation(
                    id=f"near_rail_{component.id}",
                    severity="watch",
                    title=f"{component.id} is close to an output rail",
                    body=(
                        f"{output_node} is {output:.6g} V while the modeled linear window is "
                        f"{low:.6g} V to {high:.6g} V."
                    ),
                    value=output,
                    unit="V",
                    focus_component_ids=[component.id],
                    focus_node_ids=[output_node],
                )
            )
    return observations


def _largest_comparison(comparisons: list[LabComparison]) -> LabComparison | None:
    if not comparisons:
        return None
    return max(comparisons, key=lambda item: abs(item.delta))


def _breadboard_leakage_severity(
    circuit: CircuitProblem,
    leakage_ohm: float,
) -> str:
    largest_resistor = max(
        (component.value for component in circuit.components if component.type == "resistor"),
        default=0.0,
    )
    if largest_resistor and leakage_ohm < largest_resistor * 100.0:
        return "watch"
    return "notice"


def _teaching_script(
    scenario: LabScenario,
    comparisons: list[LabComparison],
) -> list[str]:
    script = [
        "Before running the lab, ask the student to predict the sign of the error, not the exact number.",
        "Change one error source at a time until the student can explain which physical path converts that error into an output change.",
        "After the run, compare baseline, solved-lab truth, and measured readout as three different claims.",
    ]
    if scenario.op_amp_input_bias_current_a is not None:
        script.append(
            "For input bias current, ask: what resistance does each input terminal see, and where does I_b times R appear as a voltage?"
        )
    if scenario.enable_bias_compensation:
        script.append(
            "For compensation, compute the inverting-input resistance seen by bias current, then match it at the other input and check whether the output offset shrinks."
        )
    if scenario.supply_positive_v is not None or scenario.supply_negative_v is not None:
        script.append(
            "For saturation, first calculate the desired linear output, then compare it with the allowed rail window."
        )
    if comparisons:
        script.append(
            "Use the largest-shift row as the next Socratic prompt: ask why that quantity was more sensitive than the others."
        )
    return script


def _unique_component_id(prefix: str, existing: set[str]) -> str:
    candidate = prefix
    suffix = 2
    while candidate in existing:
        candidate = f"{prefix}_{suffix}"
        suffix += 1
    return candidate


def _safe_id(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip())
    return cleaned or "node"
