from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.models.circuit_ir import (
    CircuitProblem,
    Component,
    is_nonideal_op_amp_type,
    is_op_amp_type,
)
from app.models.solution_packet import CalculationTrace, ComponentResult, QuantityValue


SOURCE_SIGN_CONVENTION = (
    "Voltage is V(nodes[0]) - V(nodes[1]); current is positive from nodes[0] "
    "to nodes[1]; power is voltage times current. Negative source power means "
    "the source supplies power to the circuit."
)
DEFAULT_NONIDEAL_OPEN_LOOP_GAIN = 100_000.0


@dataclass
class SolveResult:
    success: bool
    message: str | None = None
    node_voltages: dict[str, float] = field(default_factory=dict)
    voltage_source_currents: dict[str, float] = field(default_factory=dict)
    op_amp_output_currents: dict[str, float] = field(default_factory=dict)
    component_results: dict[str, ComponentResult] = field(default_factory=dict)
    requested_answers: dict[str, QuantityValue] = field(default_factory=dict)
    calculation_trace: CalculationTrace = field(default_factory=CalculationTrace)
    warnings: list[str] = field(default_factory=list)


def nonideal_open_loop_gain(component: Component) -> float:
    if component.open_loop_gain is not None:
        return component.open_loop_gain
    if component.value > 0:
        return component.value
    return DEFAULT_NONIDEAL_OPEN_LOOP_GAIN


def nonideal_output_window(component: Component) -> tuple[float, float] | None:
    if component.supply_positive_v is None or component.supply_negative_v is None:
        return None
    margin = component.output_swing_margin_v or 0.0
    lower = min(component.supply_negative_v, component.supply_positive_v) + margin
    upper = max(component.supply_negative_v, component.supply_positive_v) - margin
    if lower > upper:
        lower, upper = upper, lower
    return lower, upper


def clipped_nonideal_output(component: Component, output_voltage: float) -> float | None:
    window = nonideal_output_window(component)
    if window is None:
        return None
    lower, upper = window
    clipped = min(max(output_voltage, lower), upper)
    if abs(clipped - output_voltage) <= 1e-12:
        return None
    return clipped


def _node_voltage(node: str, node_voltages: dict[str, float]) -> float:
    if node not in node_voltages:
        raise KeyError(f"Node {node!r} was not solved and cannot be used as a voltage reference.")
    return node_voltages[node]


def _component_voltage(nodes: list[str], node_voltages: dict[str, float]) -> float:
    return _node_voltage(nodes[0], node_voltages) - _node_voltage(nodes[1], node_voltages)


def _op_amp_output_voltage(nodes: list[str], node_voltages: dict[str, float]) -> float:
    return _node_voltage(nodes[2], node_voltages) - _node_voltage(nodes[3], node_voltages)


def _quantity(
    value: float,
    unit: str,
    explanation_key: str | None = None,
    reference: dict[str, str] | None = None,
) -> QuantityValue:
    return QuantityValue(
        value=float(value),
        unit=unit,
        explanation_key=explanation_key,
        reference=reference,
    )


def _stamp_conductance(
    matrix: np.ndarray,
    node_index: dict[str, int],
    node_a: str,
    node_b: str,
    conductance: float,
) -> None:
    idx_a = node_index.get(node_a)
    idx_b = node_index.get(node_b)
    if idx_a is not None:
        matrix[idx_a, idx_a] += conductance
    if idx_b is not None:
        matrix[idx_b, idx_b] += conductance
    if idx_a is not None and idx_b is not None:
        matrix[idx_a, idx_b] -= conductance
        matrix[idx_b, idx_a] -= conductance


def _build_requested_answers(
    problem: CircuitProblem,
    node_voltages: dict[str, float],
    component_results: dict[str, ComponentResult],
) -> dict[str, QuantityValue]:
    answers: dict[str, QuantityValue] = {}
    components_by_id = {component.id: component for component in problem.components}

    for goal in problem.goals:
        key = f"{goal.quantity}:{goal.target}"
        if goal.quantity == "node_voltage":
            value = node_voltages[goal.target]
            answers[goal.id] = _quantity(
                value,
                "V",
                explanation_key=key,
                reference={"positive_node": goal.target, "negative_node": problem.ground_node},
            )
            continue

        component = components_by_id[goal.target]
        result = component_results[goal.target]

        if goal.quantity == "component_voltage":
            if goal.reference and {"positive_node", "negative_node"} <= set(goal.reference):
                value = (
                    _node_voltage(str(goal.reference["positive_node"]), node_voltages)
                    - _node_voltage(str(goal.reference["negative_node"]), node_voltages)
                )
                reference = {
                    "positive_node": str(goal.reference["positive_node"]),
                    "negative_node": str(goal.reference["negative_node"]),
                }
            else:
                value = result.voltage.value
                reference = {
                    "positive_node": component.nodes[0],
                    "negative_node": component.nodes[1],
                }
            answers[goal.id] = _quantity(value, "V", explanation_key=key, reference=reference)
        elif goal.quantity == "component_current":
            answers[goal.id] = _quantity(
                result.current.value,
                "A",
                explanation_key=key,
                reference={"from_node": component.nodes[0], "to_node": component.nodes[1]},
            )
        elif goal.quantity in {"component_power", "source_power"}:
            answers[goal.id] = _quantity(
                result.power.value,
                "W",
                explanation_key=key,
                reference={"component": component.id},
            )

    return answers


def solve_mna(
    problem: CircuitProblem,
    _forced_op_amp_outputs: dict[str, float] | None = None,
) -> SolveResult:
    forced_op_amp_outputs = _forced_op_amp_outputs or {}
    ground = problem.ground_node
    non_ground_nodes = [node for node in problem.nodes if node != ground]
    node_index = {node: idx for idx, node in enumerate(non_ground_nodes)}
    voltage_sources = [
        component for component in problem.components if component.type == "voltage_source"
    ]
    inductors = [component for component in problem.components if component.type == "inductor"]
    op_amps = [component for component in problem.components if is_op_amp_type(component.type)]
    source_index = {
        component.id: len(non_ground_nodes) + idx
        for idx, component in enumerate(voltage_sources)
    }
    inductor_index = {
        component.id: len(non_ground_nodes) + len(voltage_sources) + idx
        for idx, component in enumerate(inductors)
    }
    op_amp_index = {
        component.id: len(non_ground_nodes) + len(voltage_sources) + len(inductors) + idx
        for idx, component in enumerate(op_amps)
    }
    unknown_order = [
        *(f"V({node})" for node in non_ground_nodes),
        *(f"I({component.id})" for component in voltage_sources),
        *(f"I({component.id})" for component in inductors),
        *(f"I({component.id}_out)" for component in op_amps),
    ]

    size = len(non_ground_nodes) + len(voltage_sources) + len(inductors) + len(op_amps)
    if size == 0:
        return SolveResult(
            success=False,
            message="Circuit has no unknowns to solve.",
            calculation_trace=CalculationTrace(unknown_order=unknown_order),
        )

    # Matrix layout:
    # [ G  B ] [v_node]   [i_injected]
    # [ C  D ] [i_vs  ] = [v_source  ]
    #
    # G holds KCL conductance terms for non-ground nodes. The voltage-source
    # columns/rows add the extra unknown currents needed by Modified Nodal
    # Analysis. Ground is not an unknown; its voltage is fixed at 0 V.
    matrix = np.zeros((size, size), dtype=float)
    rhs = np.zeros(size, dtype=float)

    for component in problem.components:
        node_a, node_b = component.nodes[0], component.nodes[1]
        idx_a = node_index.get(node_a)
        idx_b = node_index.get(node_b)

        if component.type == "resistor":
            conductance = 1.0 / component.value
            # Resistor stamp: current leaving node a is g*(Va - Vb), and
            # current leaving node b is g*(Vb - Va). This adds +g to each
            # connected diagonal and -g to each off-diagonal coupling.
            _stamp_conductance(matrix, node_index, node_a, node_b, conductance)

        elif component.type == "capacitor":
            # DC operating point: ideal capacitors are open circuits.
            continue

        elif component.type == "inductor":
            inductor_idx = inductor_index[component.id]
            # DC operating point: ideal inductors are steady-state shorts.
            # Model this as a 0 V source so the branch current remains solved.
            if idx_a is not None:
                matrix[idx_a, inductor_idx] += 1.0
                matrix[inductor_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, inductor_idx] -= 1.0
                matrix[inductor_idx, idx_b] -= 1.0
            rhs[inductor_idx] = 0.0

        elif component.type == "current_source":
            current = component.value
            # Current source direction is nodes[0] -> nodes[1]. KCL rows use
            # current injected into a node on the RHS, so current leaves node a
            # (-I injection) and enters node b (+I injection).
            if idx_a is not None:
                rhs[idx_a] -= current
            if idx_b is not None:
                rhs[idx_b] += current

        elif component.type == "voltage_source":
            vs_idx = source_index[component.id]
            # Voltage source stamp: the source current is an extra unknown in
            # the KCL rows. The extra constraint row enforces Va - Vb = Vsource.
            if idx_a is not None:
                matrix[idx_a, vs_idx] += 1.0
                matrix[vs_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, vs_idx] -= 1.0
                matrix[vs_idx, idx_b] -= 1.0
            rhs[vs_idx] = component.value
        elif is_op_amp_type(component.type):
            if len(component.nodes) != 4:
                return SolveResult(
                    success=False,
                    message=(
                        f"{component.id} op-amp must have nodes "
                        "[non_inverting, inverting, output, reference]."
                    ),
                    calculation_trace=CalculationTrace(
                        unknown_order=unknown_order,
                        mna_matrix=matrix.tolist(),
                        rhs_vector=rhs.tolist(),
                    ),
                )
            vp, vm, out, ref = component.nodes
            op_idx = op_amp_index[component.id]
            idx_vp = node_index.get(vp)
            idx_vm = node_index.get(vm)
            idx_out = node_index.get(out)
            idx_ref = node_index.get(ref)

            if component.input_resistance_ohm is not None:
                _stamp_conductance(
                    matrix,
                    node_index,
                    vp,
                    vm,
                    1.0 / component.input_resistance_ohm,
                )

            if idx_out is not None:
                matrix[idx_out, op_idx] += 1.0
            if idx_ref is not None:
                matrix[idx_ref, op_idx] -= 1.0
            if is_nonideal_op_amp_type(component.type):
                bias_current = component.input_bias_current_a or 0.0
                for input_idx in [idx_vp, idx_vm]:
                    if input_idx is not None:
                        rhs[input_idx] -= bias_current
                    if idx_ref is not None:
                        rhs[idx_ref] += bias_current

                forced_output = forced_op_amp_outputs.get(component.id)
                if forced_output is not None:
                    if idx_out is not None:
                        matrix[op_idx, idx_out] += 1.0
                    if idx_ref is not None:
                        matrix[op_idx, idx_ref] -= 1.0
                    rhs[op_idx] = forced_output
                elif component.output_resistance_ohm is not None:
                    output_conductance = 1.0 / component.output_resistance_ohm
                    gain = nonideal_open_loop_gain(component)
                    gm = gain * output_conductance
                    offset = component.input_offset_voltage_v or 0.0
                    if idx_out is not None:
                        matrix[op_idx, idx_out] -= output_conductance
                    if idx_ref is not None:
                        matrix[op_idx, idx_ref] += output_conductance
                    if idx_vp is not None:
                        matrix[op_idx, idx_vp] += gm
                    if idx_vm is not None:
                        matrix[op_idx, idx_vm] -= gm
                    matrix[op_idx, op_idx] += 1.0
                    rhs[op_idx] = -gm * offset
                else:
                    gain = nonideal_open_loop_gain(component)
                    offset = component.input_offset_voltage_v or 0.0
                    if idx_out is not None:
                        matrix[op_idx, idx_out] += 1.0
                    if idx_ref is not None:
                        matrix[op_idx, idx_ref] -= 1.0
                    if idx_vp is not None:
                        matrix[op_idx, idx_vp] -= gain
                    if idx_vm is not None:
                        matrix[op_idx, idx_vm] += gain
                    rhs[op_idx] = gain * offset
            else:
                if idx_vp is not None:
                    matrix[op_idx, idx_vp] += 1.0
                if idx_vm is not None:
                    matrix[op_idx, idx_vm] -= 1.0
        else:
            return SolveResult(
                success=False,
                message=f"Unsupported component type {component.type!r} reached the MNA solver.",
                calculation_trace=CalculationTrace(
                    unknown_order=unknown_order,
                    mna_matrix=matrix.tolist(),
                    rhs_vector=rhs.tolist(),
                ),
            )

    trace = CalculationTrace(
        unknown_order=unknown_order,
        mna_matrix=matrix.tolist(),
        rhs_vector=rhs.tolist(),
    )

    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as exc:
        trace.solution_vector = []
        message = f"MNA matrix is singular or ill-conditioned: {exc}"
        if op_amps:
            message += (
                " Ideal op-amp circuit may require a closed-loop feedback path "
                "or additional constraints."
            )
        return SolveResult(
            success=False,
            message=message,
            calculation_trace=trace,
        )
    trace.solution_vector = solution.tolist()

    node_voltages = {ground: 0.0}
    for node, idx in node_index.items():
        node_voltages[node] = float(solution[idx])

    saturation_outputs = dict(forced_op_amp_outputs)
    saturation_warnings: list[str] = []
    for component in op_amps:
        if not is_nonideal_op_amp_type(component.type):
            continue
        if component.id in forced_op_amp_outputs:
            continue
        output_voltage = _op_amp_output_voltage(component.nodes, node_voltages)
        clipped_output = clipped_nonideal_output(component, output_voltage)
        if clipped_output is None:
            continue
        saturation_outputs[component.id] = clipped_output
        message = (
            f"{component.id} nonideal op-amp saturated: finite-gain output "
            f"{output_voltage:.6g} V was clamped to {clipped_output:.6g} V by the rail model."
        )
        if component.slew_rate_v_per_s is not None:
            recovery_step = abs(output_voltage - clipped_output)
            slew_time_s = recovery_step / component.slew_rate_v_per_s
            message += f" Slew-limited recovery estimate is at least {slew_time_s:.6g} s."
        if component.clipping_recovery_s is not None:
            message += f" Clipping recovery parameter is {component.clipping_recovery_s:.6g} s."
        saturation_warnings.append(message)

    if saturation_warnings:
        saturated_result = solve_mna(problem, _forced_op_amp_outputs=saturation_outputs)
        saturated_result.warnings = [*saturation_warnings, *saturated_result.warnings]
        return saturated_result

    voltage_source_currents = {
        component.id: float(solution[source_index[component.id]])
        for component in voltage_sources
    }
    inductor_currents = {
        component.id: float(solution[inductor_index[component.id]])
        for component in inductors
    }
    op_amp_output_currents = {
        component.id: float(solution[op_amp_index[component.id]])
        for component in op_amps
    }

    component_results: dict[str, ComponentResult] = {}
    for component in problem.components:
        voltage = (
            _op_amp_output_voltage(component.nodes, node_voltages)
            if is_op_amp_type(component.type)
            else _component_voltage(component.nodes, node_voltages)
        )
        if component.type == "resistor":
            current = voltage / component.value
            sign_convention = (
                "Passive sign convention: current is positive from nodes[0] "
                "to nodes[1], and resistor power is absorbed when positive."
            )
        elif component.type == "capacitor":
            current = 0.0
            sign_convention = (
                "DC operating point: ideal capacitor is treated as an open circuit. "
                "Voltage is V(nodes[0]) - V(nodes[1]); current is 0 A."
            )
        elif component.type == "inductor":
            current = inductor_currents[component.id]
            sign_convention = (
                "DC operating point: ideal inductor is treated as a short circuit. "
                "Voltage is constrained to 0 V; current is positive from nodes[0] to nodes[1]."
            )
        elif component.type == "current_source":
            current = component.value
            sign_convention = SOURCE_SIGN_CONVENTION
        elif component.type == "voltage_source":
            current = voltage_source_currents[component.id]
            sign_convention = SOURCE_SIGN_CONVENTION
        elif is_op_amp_type(component.type):
            current = op_amp_output_currents[component.id]
            if is_nonideal_op_amp_type(component.type):
                if component.output_resistance_ohm is not None:
                    sign_convention = (
                        "Nonideal op-amp macromodel: output port is a VCCS plus finite "
                        "output resistance, with current positive from output to reference."
                    )
                else:
                    sign_convention = (
                        "Nonideal op-amp model: voltage is V(output) - V(reference), "
                        "output current is positive from output to reference, finite gain "
                        "and optional rail clamp are included."
                    )
            else:
                sign_convention = (
                    "Ideal op-amp sign convention: voltage is V(output) - V(reference), "
                    "and output current is positive from output to reference."
                )
        else:
            return SolveResult(
                success=False,
                message=f"Unsupported component type {component.type!r} reached result derivation.",
                calculation_trace=trace,
            )

        power = voltage * current
        component_results[component.id] = ComponentResult(
            voltage=_quantity(
                voltage,
                "V",
                reference={
                    "positive_node": component.nodes[2]
                    if is_op_amp_type(component.type)
                    else component.nodes[0],
                    "negative_node": component.nodes[3]
                    if is_op_amp_type(component.type)
                    else component.nodes[1],
                },
            ),
            current=_quantity(
                current,
                "A",
                reference={
                    "from_node": component.nodes[2]
                    if is_op_amp_type(component.type)
                    else component.nodes[0],
                    "to_node": component.nodes[3]
                    if is_op_amp_type(component.type)
                    else component.nodes[1],
                },
            ),
            power=_quantity(power, "W", reference={"component": component.id}),
            sign_convention=sign_convention,
        )

    requested_answers = _build_requested_answers(
        problem,
        node_voltages,
        component_results,
    )
    return SolveResult(
        success=True,
        node_voltages=node_voltages,
        voltage_source_currents=voltage_source_currents,
        op_amp_output_currents=op_amp_output_currents,
        component_results=component_results,
        requested_answers=requested_answers,
        calculation_trace=trace,
    )
