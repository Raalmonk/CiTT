from __future__ import annotations

from html import escape
from math import cos, pi, sin

import schemdraw
import schemdraw.elements as elm

from app.models.circuit_ir import CircuitProblem, Component


VARIANT_SUFFIXES = ("_value_variant", "_goal_variant")


def _fmt(value: float, unit: str) -> str:
    if unit == "ohm":
        if abs(value) >= 1000:
            return f"{value / 1000:g} kOhm"
        return f"{value:g} ohm"
    if unit == "A" and 0 < abs(value) < 1:
        return f"{value * 1000:g} mA"
    return f"{value:g} {unit}"


def _label(component: Component) -> str:
    return f"{component.id} {_fmt(component.value, component.unit)}"


def _components(problem: CircuitProblem) -> dict[str, Component]:
    return {component.id: component for component in problem.components}


def _schemdraw_svg(drawing: schemdraw.Drawing, renderer: str) -> str:
    svg = drawing.get_imagedata("svg").decode("utf-8")
    return _tag_svg(svg, renderer)


def _tag_svg(svg: str, renderer: str) -> str:
    insert_at = svg.find(">") + 1
    if insert_at <= 0:
        return svg
    desc = f'<desc>VeriCircuit Tutor renderer: {escape(renderer)}</desc>'
    return f"{svg[:insert_at]}{desc}{svg[insert_at:]}"


def _dot(name: str, at: tuple[float, float], loc: str = "top") -> elm.Dot:
    return elm.Dot().at(at).label(name, loc=loc)


def _render_voltage_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.0, fontsize=11)

    top_left = (0, 4)
    bottom_left = (0, 0)
    top = (4, 4)
    mid = (4, 2)
    bottom = (4, 0)

    d += elm.SourceV().at(bottom_left).to(top_left).label(_label(c["V1"]), loc="left")
    d += elm.Line().at(top_left).to(top)
    d += elm.Dot().at(top_left)
    d += _dot("n1", top, loc="right")
    d += elm.Resistor().at(top).to(mid).label(_label(c["R1"]), loc="right")
    d += _dot("n2", mid, loc="right")
    d += elm.Resistor().at(mid).to(bottom).label(_label(c["R2"]), loc="right")
    d += elm.Line().at(bottom).to(bottom_left)
    d += _dot("0", bottom, loc="right")
    d += elm.Ground().at(bottom_left)
    return _schemdraw_svg(d, "schemdraw_voltage_divider")


def _render_current_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.0, fontsize=11)

    top_left = (0, 4)
    bottom_left = (0, 0)
    top_r1 = (3, 4)
    bottom_r1 = (3, 0)
    top_r2 = (6, 4)
    bottom_r2 = (6, 0)

    d += elm.SourceI().at(bottom_left).to(top_left).label(_label(c["I1"]), loc="left")
    d += elm.Line().at(top_left).to(top_r2)
    d += elm.Line().at(bottom_r2).to(bottom_left)
    d += _dot("top", top_r1, loc="top")
    d += elm.Resistor().at(top_r1).to(bottom_r1).label(_label(c["R1"]), loc="right")
    d += elm.Resistor().at(top_r2).to(bottom_r2).label(_label(c["R2"]), loc="right")
    d += _dot("0", bottom_r1, loc="bottom")
    d += elm.Ground().at(bottom_left)
    return _schemdraw_svg(d, "schemdraw_current_divider")


def _render_bridge(problem: CircuitProblem) -> str:
    c = _components(problem)
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.0, fontsize=10.5)

    source_node = "n1" if "n1" in problem.nodes else "src"
    left_mid = "n2" if "n2" in problem.nodes else "a"
    right_mid = "n3" if "n3" in problem.nodes else "b"

    top_left = (0, 4)
    bottom_left = (0, 0)
    top_bus_left = (2, 4)
    top_bus_right = (8, 4)
    bottom_bus_left = (2, 0)
    bottom_bus_right = (8, 0)
    left_mid_xy = (3, 2)
    right_mid_xy = (7, 2)

    d += elm.SourceV().at(bottom_left).to(top_left).label(_label(c["V1"]), loc="left")
    d += elm.Line().at(top_left).to(top_bus_right)
    d += elm.Line().at(bottom_bus_right).to(bottom_left)
    d += elm.Dot().at(top_bus_left).label(source_node, loc="top")
    d += elm.Dot().at(bottom_bus_left).label("0", loc="bottom")
    d += elm.Ground().at(bottom_left)

    d += elm.Line().at(top_bus_left).to((3, 4))
    d += elm.Resistor().at((3, 4)).to(left_mid_xy).label(_label(c["R1"]), loc="left")
    d += _dot(left_mid, left_mid_xy, loc="left")
    d += elm.Resistor().at(left_mid_xy).to((3, 0)).label(_label(c["R2"]), loc="left")
    d += elm.Line().at((3, 0)).to(bottom_bus_left)

    d += elm.Line().at(top_bus_right).to((7, 4))
    d += elm.Resistor().at((7, 4)).to(right_mid_xy).label(_label(c["R3"]), loc="right")
    d += _dot(right_mid, right_mid_xy, loc="right")
    d += elm.Resistor().at(right_mid_xy).to((7, 0)).label(_label(c["R4"]), loc="right")
    d += elm.Line().at((7, 0)).to(bottom_bus_right)

    d += elm.Resistor().at(left_mid_xy).to(right_mid_xy).label(_label(c["R5"]), loc="top")
    return _schemdraw_svg(d, "schemdraw_bridge_network")


def _wire(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<line class="wire" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" />'


def _node(name: str, x: float, y: float) -> str:
    return (
        f'<circle class="node" cx="{x:g}" cy="{y:g}" r="4" />'
        f'<text class="node-label" x="{x + 8:g}" y="{y - 8:g}">{escape(name)}</text>'
    )


def _fallback_resistor(component: Component, x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f'<line class="component resistor" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" />'
        f'<text class="component-label" x="{(x1 + x2) / 2:g}" y="{(y1 + y2) / 2 - 10:g}">'
        f"{escape(_label(component))}</text>"
    )


def _fallback_source(component: Component, x: float, y: float) -> str:
    symbol = "V" if component.type == "voltage_source" else "I"
    return (
        f'<circle class="source" cx="{x:g}" cy="{y:g}" r="24" />'
        f'<text class="source-symbol" x="{x:g}" y="{y + 6:g}">{symbol}</text>'
        f'<text class="component-label" x="{x:g}" y="{y + 44:g}">{escape(_label(component))}</text>'
    )


def _svg(width: int, height: int, body: str, renderer: str) -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Circuit schematic">
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
    return _tag_svg(svg, renderer)


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
            pieces.append(_fallback_resistor(component, x1, y1, x2, y2))
        else:
            pieces.append(_fallback_source(component, (x1 + x2) / 2, (y1 + y2) / 2))
    for node, (x, y) in positions.items():
        pieces.append(_node(node, x, y))
    return _svg(width, height, "\n  ".join(pieces), "fallback_graph")


def _normalized_base_id(circuit_id: str) -> str:
    base_id = circuit_id
    changed = True
    while changed:
        changed = False
        for suffix in VARIANT_SUFFIXES:
            if base_id.endswith(suffix):
                base_id = base_id[: -len(suffix)]
                changed = True
    return base_id


def _renderer_key(circuit: CircuitProblem) -> str:
    if circuit.topology_id:
        return circuit.topology_id
    return _normalized_base_id(circuit.id)


def render_schematic_svg(circuit: CircuitProblem) -> str:
    key = _renderer_key(circuit)
    if key == "voltage_divider":
        try:
            return _render_voltage_divider(circuit)
        except KeyError:
            return _render_fallback_graph(circuit)
    if key == "current_divider":
        try:
            return _render_current_divider(circuit)
        except KeyError:
            return _render_fallback_graph(circuit)
    if key in {"bridge_network", "bridge_network_alt"}:
        try:
            return _render_bridge(circuit)
        except KeyError:
            return _render_fallback_graph(circuit)
    return _render_fallback_graph(circuit)

