from __future__ import annotations

from app.models.circuit_ir import (
    CircuitProblem,
    Component,
    is_ideal_op_amp_type,
    is_nonideal_op_amp_type,
)


def _fmt(value: float) -> str:
    return f"{value:.12g}"


def _line_for_component(component: Component) -> str:
    node_a, node_b = component.nodes[0], component.nodes[1]
    ac_suffix = ""
    if component.type in {"voltage_source", "current_source"} and (
        component.ac_magnitude is not None or component.ac_phase_deg is not None
    ):
        ac_suffix = (
            f" AC {_fmt(component.ac_magnitude or 0.0)} "
            f"{_fmt(component.ac_phase_deg or 0.0)}"
        )
    if component.type == "resistor":
        return f"{component.id} {node_a} {node_b} {_fmt(component.value)}"
    if component.type == "capacitor":
        return f"{component.id} {node_a} {node_b} {_fmt(component.value)}"
    if component.type == "inductor":
        return f"{component.id} {node_a} {node_b} {_fmt(component.value)}"
    if component.type == "diode":
        saturation_current = component.saturation_current_a or 1e-12
        emission = component.emission_coefficient or 1.0
        thermal_voltage = component.thermal_voltage_v or 0.025852
        return "\n".join(
            [
                f"{component.id} {node_a} {node_b} D_{component.id}",
                (
                    f".model D_{component.id} D("
                    f"IS={_fmt(saturation_current)} N={_fmt(emission)} "
                    f"VT={_fmt(thermal_voltage)})"
                ),
            ]
        )
    if component.type == "voltage_source":
        return f"{component.id} {node_a} {node_b} DC {_fmt(component.value)}{ac_suffix}"
    if component.type == "current_source":
        return f"{component.id} {node_a} {node_b} DC {_fmt(component.value)}{ac_suffix}"
    if is_ideal_op_amp_type(component.type):
        vp, vm, out, ref = component.nodes
        return "\n".join(
            [
                f"* {component.id} ideal op-amp: nodes {vp} {vm} {out} {ref}",
                f"* implemented internally as MNA constraint V({vp})=V({vm})",
            ]
        )
    if is_nonideal_op_amp_type(component.type):
        vp, vm, out, ref = component.nodes
        details = [
            f"* {component.id} nonideal op-amp: nodes {vp} {vm} {out} {ref}",
            "* implemented internally as finite-gain VCVS plus optional rail clamp",
        ]
        if component.open_loop_gain is not None:
            details.append(f"* open_loop_gain={_fmt(component.open_loop_gain)}")
        if component.gain_bandwidth_hz is not None:
            details.append(f"* gain_bandwidth_hz={_fmt(component.gain_bandwidth_hz)}")
        if component.bandwidth_hz is not None:
            details.append(f"* bandwidth_hz={_fmt(component.bandwidth_hz)}")
        if component.supply_positive_v is not None and component.supply_negative_v is not None:
            details.append(
                f"* rails={_fmt(component.supply_negative_v)}..{_fmt(component.supply_positive_v)} V"
            )
        if component.output_current_limit_a is not None:
            details.append(f"* output_current_limit_a={_fmt(component.output_current_limit_a)}")
        if component.input_offset_voltage_v is not None:
            details.append(f"* input_offset_voltage_v={_fmt(component.input_offset_voltage_v)}")
        if component.input_resistance_ohm is not None:
            details.append(f"* input_resistance_ohm={_fmt(component.input_resistance_ohm)}")
        if component.output_resistance_ohm is not None:
            details.append(f"* output_resistance_ohm={_fmt(component.output_resistance_ohm)}")
        if component.compensation_capacitance_f is not None:
            details.append(f"* compensation_capacitance_f={_fmt(component.compensation_capacitance_f)}")
        if component.clamp_diode_saturation_current_a is not None:
            details.append(
                f"* clamp_diode_saturation_current_a={_fmt(component.clamp_diode_saturation_current_a)}"
            )
        return "\n".join(details)
    raise ValueError(f"Unsupported component type: {component.type}")


def generate_netlist(problem: CircuitProblem) -> str:
    lines = ["* VeriCircuit Tutor generated netlist"]
    lines.extend(_line_for_component(component) for component in problem.components)
    if problem.analysis_type in {"ac_steady_state", "ac_single_frequency"} and problem.frequency_hz is not None:
        lines.append(f".ac lin 1 {_fmt(problem.frequency_hz)} {_fmt(problem.frequency_hz)}")
    elif problem.analysis_type == "ac_sweep" and problem.sweep is not None:
        if problem.sweep.scale == "log":
            lines.append(
                f".ac dec {problem.sweep.points_per_decade} "
                f"{_fmt(problem.sweep.start_hz)} {_fmt(problem.sweep.stop_hz)}"
            )
        else:
            lines.append(
                f".ac lin {problem.sweep.points_per_decade} "
                f"{_fmt(problem.sweep.start_hz)} {_fmt(problem.sweep.stop_hz)}"
            )
    elif problem.analysis_type == "rc_transient":
        initial = problem.transient.initial_voltage_v if problem.transient else 0.0
        lines.append(f"* numerical transient, initial target capacitor voltage {_fmt(initial)} V")
    else:
        lines.append(".op")
    lines.append(".end")
    return "\n".join(lines)
