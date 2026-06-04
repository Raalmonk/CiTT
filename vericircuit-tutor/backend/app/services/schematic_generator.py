from __future__ import annotations

from html import escape
from math import cos, pi, sin

from app.models.circuit_ir import CircuitProblem, Component


def _fmt(value: float, unit: str) -> str:
    if unit == "ohm":
        if abs(value) >= 1000 and value % 1000 == 0:
            return f"{value / 1000:g} kOhm"
        return f"{value:g} ohm"
    if unit == "A" and 0 < abs(value) < 1:
        return f"{value * 1000:g} mA"
    return f"{value:g} {unit}"


def _label(component: Component) -> str:
    return escape(f"{component.id} {_fmt(component.value, component.unit)}")


def _wire(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<line class="wire" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" />'


def _node(name: str, x: float, y: float) -> str:
    return (
        f'<circle class="node" cx="{x:g}" cy="{y:g}" r="4" />'
        f'<text class="node-label" x="{x + 8:g}" y="{y - 8:g}">{escape(name)}</text>'
    )


def _resistor(component: Component, x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f'<line class="component resistor" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" />'
        f'<text class="component-label" x="{(x1 + x2) / 2:g}" y="{(y1 + y2) / 2 - 10:g}">'
        f"{_label(component)}</text>"
    )


def _source(component: Component, x: float, y: float) -> str:
    symbol = "V" if component.type == "voltage_source" else "I"
    return (
        f'<circle class="source" cx="{x:g}" cy="{y:g}" r="24" />'
        f'<text class="source-symbol" x="{x:g}" y="{y + 6:g}">{symbol}</text>'
        f'<text class="component-label" x="{x:g}" y="{y + 44:g}">{_label(component)}</text>'
    )


def _svg(width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Circuit schematic">
  <style>
    .bg {{ fill: #ffffff; }}
    .wire {{ stroke: #1f2937; stroke-width: 2.4; fill: none; }}
    .component {{ stroke: #1768ac; stroke-width: 4; stroke-linecap: round; fill: none; }}
    .resistor {{ stroke-dasharray: 7 5; }}
    .source {{ stroke: #117a4b; stroke-width: 3; fill: #eef8f3; }}
    .node {{ fill: #111827; }}
    .node-label {{ fill: #4b5563; font: 12px sans-serif; }}
    .component-label {{ fill: #111827; font: 13px sans-serif; text-anchor: middle; }}
    .source-symbol {{ fill: #117a4b; font: 700 18px sans-serif; text-anchor: middle; }}
    .title {{ fill: #111827; font: 700 16px sans-serif; }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}" />
  {body}
</svg>"""


def _components(problem: CircuitProblem) -> dict[str, Component]:
    return {component.id: component for component in problem.components}


def _render_voltage_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    body = "\n  ".join(
        [
            f'<text class="title" x="24" y="28">{escape(problem.title)}</text>',
            _node("n1", 130, 80),
            _node("n2", 300, 80),
            _node("0", 300, 230),
            _wire(130, 80, 190, 80),
            _resistor(c["R1"], 190, 80, 260, 80),
            _wire(260, 80, 300, 80),
            _wire(300, 80, 300, 115),
            _resistor(c["R2"], 300, 115, 300, 185),
            _wire(300, 185, 300, 230),
            _wire(130, 104, 130, 230),
            _wire(130, 230, 300, 230),
            _source(c["V1"], 130, 80),
        ]
    )
    return _svg(460, 280, body)


def _render_current_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    body = "\n  ".join(
        [
            f'<text class="title" x="24" y="28">{escape(problem.title)}</text>',
            _node("top", 240, 80),
            _node("0", 240, 230),
            _wire(120, 80, 360, 80),
            _wire(120, 230, 360, 230),
            _wire(120, 104, 120, 230),
            _source(c["I1"], 120, 80),
            _wire(240, 80, 240, 110),
            _resistor(c["R1"], 240, 110, 240, 190),
            _wire(240, 190, 240, 230),
            _wire(360, 80, 360, 110),
            _resistor(c["R2"], 360, 110, 360, 190),
            _wire(360, 190, 360, 230),
        ]
    )
    return _svg(480, 280, body)


def _render_bridge(problem: CircuitProblem) -> str:
    c = _components(problem)
    source_node = "n1" if "n1" in problem.nodes else "src"
    left_mid = "n2" if "n2" in problem.nodes else "a"
    right_mid = "n3" if "n3" in problem.nodes else "b"
    body = "\n  ".join(
        [
            f'<text class="title" x="24" y="28">{escape(problem.title)}</text>',
            _node(source_node, 240, 70),
            _node(left_mid, 145, 155),
            _node(right_mid, 335, 155),
            _node("0", 240, 250),
            _wire(240, 70, 200, 105),
            _resistor(c["R1"], 200, 105, 145, 155),
            _wire(240, 70, 285, 105),
            _resistor(c["R3"], 285, 105, 335, 155),
            _wire(145, 155, 145, 185),
            _resistor(c["R2"], 145, 185, 145, 230),
            _wire(145, 230, 240, 250),
            _wire(335, 155, 335, 185),
            _resistor(c["R4"], 335, 185, 335, 230),
            _wire(335, 230, 240, 250),
            _resistor(c["R5"], 180, 155, 300, 155),
            _wire(145, 155, 180, 155),
            _wire(300, 155, 335, 155),
            _source(c["V1"], 240, 250),
            _wire(240, 226, 240, 70),
        ]
    )
    return _svg(500, 310, body)


def _render_fallback_graph(problem: CircuitProblem) -> str:
    width = 560
    height = 360
    nodes = sorted(problem.nodes)
    center_x = width / 2
    center_y = height / 2
    radius = 120
    positions: dict[str, tuple[float, float]] = {}
    for idx, node in enumerate(nodes):
        angle = (2 * pi * idx / max(len(nodes), 1)) - pi / 2
        positions[node] = (center_x + radius * cos(angle), center_y + radius * sin(angle))

    pieces = [f'<text class="title" x="24" y="28">{escape(problem.title)}</text>']
    for component in problem.components:
        x1, y1 = positions[component.nodes[0]]
        x2, y2 = positions[component.nodes[1]]
        pieces.append(_wire(x1, y1, x2, y2))
        if component.type == "resistor":
            pieces.append(_resistor(component, x1, y1, x2, y2))
        else:
            pieces.append(_source(component, (x1 + x2) / 2, (y1 + y2) / 2))
    for node, (x, y) in positions.items():
        pieces.append(_node(node, x, y))
    return _svg(width, height, "\n  ".join(pieces))


def render_schematic_svg(circuit: CircuitProblem) -> str:
    if circuit.id == "voltage_divider":
        return _render_voltage_divider(circuit)
    if circuit.id == "current_divider":
        return _render_current_divider(circuit)
    if circuit.id in {"bridge_network", "bridge_network_alt"}:
        return _render_bridge(circuit)
    return _render_fallback_graph(circuit)

