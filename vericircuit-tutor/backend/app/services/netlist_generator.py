from __future__ import annotations

from app.models.circuit_ir import CircuitProblem, Component


def _fmt(value: float) -> str:
    return f"{value:.12g}"


def _line_for_component(component: Component) -> str:
    node_a, node_b = component.nodes
    if component.type == "resistor":
        return f"{component.id} {node_a} {node_b} {_fmt(component.value)}"
    if component.type == "voltage_source":
        return f"{component.id} {node_a} {node_b} DC {_fmt(component.value)}"
    if component.type == "current_source":
        return f"{component.id} {node_a} {node_b} DC {_fmt(component.value)}"
    raise ValueError(f"Unsupported component type: {component.type}")


def generate_netlist(problem: CircuitProblem) -> str:
    lines = ["* VeriCircuit Tutor generated netlist"]
    lines.extend(_line_for_component(component) for component in problem.components)
    lines.extend([".op", ".end"])
    return "\n".join(lines)

