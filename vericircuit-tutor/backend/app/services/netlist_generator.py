from __future__ import annotations

from app.models.circuit_ir import CircuitProblem, Component


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
    if component.type == "voltage_source":
        return f"{component.id} {node_a} {node_b} DC {_fmt(component.value)}{ac_suffix}"
    if component.type == "current_source":
        return f"{component.id} {node_a} {node_b} DC {_fmt(component.value)}{ac_suffix}"
    if component.type == "op_amp_ideal":
        vp, vm, out, ref = component.nodes
        return "\n".join(
            [
                f"* {component.id} ideal op-amp: nodes {vp} {vm} {out} {ref}",
                f"* implemented internally as MNA constraint V({vp})=V({vm})",
            ]
        )
    raise ValueError(f"Unsupported component type: {component.type}")


def generate_netlist(problem: CircuitProblem) -> str:
    lines = ["* VeriCircuit Tutor generated netlist"]
    lines.extend(_line_for_component(component) for component in problem.components)
    if problem.analysis_type == "ac_single_frequency" and problem.frequency_hz is not None:
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
    else:
        lines.append(".op")
    lines.append(".end")
    return "\n".join(lines)
