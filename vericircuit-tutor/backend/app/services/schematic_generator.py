from __future__ import annotations

from html import escape
from math import cos, pi, sin

import schemdraw
import schemdraw.elements as elm

from app.models.circuit_ir import CircuitProblem, Component


VARIANT_SUFFIXES = ("_value_variant", "_goal_variant")
UNIT = 3.0
FONT_SIZE_COMPONENT = 14
FONT_SIZE_NODE = 12
LABEL_OFFSET_SMALL = 0.35
LABEL_OFFSET_MEDIUM = 0.65
LABEL_OFFSET_LARGE = 0.95
CANVAS_PADDING = 0.55


def _fmt(value: float, unit: str) -> str:
    if unit == "ohm":
        if abs(value) >= 1000:
            return f"{value / 1000:g} kΩ"
        return f"{value:g} Ω"
    if unit == "A" and 0 < abs(value) < 1:
        return f"{value * 1000:g} mA"
    return f"{value:g} {unit}"


def format_component_label(component: Component) -> str:
    return f"{component.id} = {_fmt(component.value, component.unit)}"


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


def _component_label(
    element: elm.Element,
    component: Component,
    loc: str,
    ofst: float = LABEL_OFFSET_MEDIUM,
) -> elm.Element:
    return element.label(
        format_component_label(component),
        loc=loc,
        ofst=ofst,
        rotate=False,
        fontsize=FONT_SIZE_COMPONENT,
    )


def _node_label(text: str, at: tuple[float, float]) -> elm.Label:
    return elm.Label(text, fontsize=FONT_SIZE_NODE).at(at)


def _dot(at: tuple[float, float]) -> elm.Dot:
    return elm.Dot().at(at)


def _base_drawing() -> schemdraw.Drawing:
    d = schemdraw.Drawing(show=False)
    d.config(
        unit=UNIT,
        fontsize=FONT_SIZE_COMPONENT,
        inches_per_unit=0.45,
        margin=CANVAS_PADDING,
    )
    return d


def _render_voltage_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    d = _base_drawing()

    top_left = (0, 5)
    bottom_left = (0, 0)
    top = (4.5, 5)
    mid = (4.5, 2.5)
    bottom = (4.5, 0)

    d += _component_label(elm.SourceV().at(bottom_left).to(top_left), c["V1"], "left", LABEL_OFFSET_LARGE)
    d += elm.Line().at(top_left).to(top)
    d += elm.Dot().at(top_left)
    d += _dot(top)
    d += _node_label("n1", (top[0] + 0.55, top[1] + 0.55))
    d += _component_label(elm.Resistor().at(top).to(mid), c["R1"], "right", LABEL_OFFSET_LARGE)
    d += _dot(mid)
    d += _node_label("n2", (mid[0] - 0.65, mid[1]))
    d += _component_label(elm.Resistor().at(mid).to(bottom), c["R2"], "right", LABEL_OFFSET_LARGE)
    d += elm.Line().at(bottom).to(bottom_left)
    d += _dot(bottom)
    d += _node_label("0", (bottom[0] + 0.55, bottom[1] - 0.6))
    d += elm.Ground().at(bottom_left)
    return _schemdraw_svg(d, "schemdraw_voltage_divider")


def _render_current_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    d = _base_drawing()

    top_left = (0, 5)
    bottom_left = (0, 0)
    top_r1 = (4, 5)
    bottom_r1 = (3, 0)
    top_r2 = (8, 5)
    bottom_r2 = (6, 0)

    bottom_r1 = (4, 0)
    bottom_r2 = (8, 0)

    d += _component_label(elm.SourceI().at(bottom_left).to(top_left), c["I1"], "left", LABEL_OFFSET_LARGE)
    d += elm.Line().at(top_left).to(top_r2)
    d += elm.Line().at(bottom_r2).to(bottom_left)
    d += _dot(top_r1)
    d += _node_label("top", (top_r1[0], top_r1[1] + 0.65))
    d += _component_label(elm.Resistor().at(top_r1).to(bottom_r1), c["R1"], "left", LABEL_OFFSET_LARGE)
    d += _component_label(elm.Resistor().at(top_r2).to(bottom_r2), c["R2"], "right", LABEL_OFFSET_LARGE)
    d += _dot(bottom_r1)
    d += _node_label("0", (bottom_r1[0], bottom_r1[1] - 0.75))
    d += elm.Ground().at(bottom_left)
    return _schemdraw_svg(d, "schemdraw_current_divider")


def _render_bridge(problem: CircuitProblem) -> str:
    c = _components(problem)
    d = _base_drawing()

    source_node = "n1" if "n1" in problem.nodes else "src"
    left_mid = "n2" if "n2" in problem.nodes else "a"
    right_mid = "n3" if "n3" in problem.nodes else "b"

    top_left = (0, 6)
    bottom_left = (0, 0)
    top_bus_left = (3, 6)
    top_bus_right = (12, 6)
    bottom_bus_left = (3, 0)
    bottom_bus_right = (12, 0)
    left_branch_x = 4.25
    right_branch_x = 10.75
    left_mid_xy = (left_branch_x, 3)
    right_mid_xy = (right_branch_x, 3)

    d += _component_label(elm.SourceV().at(bottom_left).to(top_left), c["V1"], "left", LABEL_OFFSET_LARGE)
    d += elm.Line().at(top_left).to(top_bus_right)
    d += elm.Line().at(bottom_bus_right).to(bottom_left)
    d += elm.Dot().at(top_bus_left)
    d += _node_label(source_node, (top_bus_left[0] + 0.2, top_bus_left[1] + 0.8))
    d += elm.Dot().at(bottom_bus_left)
    d += _node_label("0", (bottom_bus_left[0] + 0.35, bottom_bus_left[1] - 0.9))
    d += elm.Ground().at(bottom_left)

    d += elm.Line().at(top_bus_left).to((left_branch_x, 6))
    d += _component_label(elm.Resistor().at((left_branch_x, 6)).to(left_mid_xy), c["R1"], "left", LABEL_OFFSET_LARGE)
    d += _dot(left_mid_xy)
    d += _node_label(left_mid, (left_mid_xy[0] - 0.8, left_mid_xy[1] - 0.15))
    d += _component_label(elm.Resistor().at(left_mid_xy).to((left_branch_x, 0)), c["R2"], "left", LABEL_OFFSET_LARGE)
    d += elm.Line().at((left_branch_x, 0)).to(bottom_bus_left)

    d += elm.Line().at(top_bus_right).to((right_branch_x, 6))
    d += _component_label(elm.Resistor().at((right_branch_x, 6)).to(right_mid_xy), c["R3"], "right", LABEL_OFFSET_LARGE)
    d += _dot(right_mid_xy)
    d += _node_label(right_mid, (right_mid_xy[0] + 0.8, right_mid_xy[1] - 0.15))
    d += _component_label(elm.Resistor().at(right_mid_xy).to((right_branch_x, 0)), c["R4"], "right", LABEL_OFFSET_LARGE)
    d += elm.Line().at((right_branch_x, 0)).to(bottom_bus_right)

    d += _component_label(elm.Resistor().at(left_mid_xy).to(right_mid_xy), c["R5"], "top", LABEL_OFFSET_LARGE)
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
        f"{escape(format_component_label(component))}</text>"
    )


def _fallback_source(component: Component, x: float, y: float) -> str:
    symbol = "V" if component.type == "voltage_source" else "I"
    return (
        f'<circle class="source" cx="{x:g}" cy="{y:g}" r="24" />'
        f'<text class="source-symbol" x="{x:g}" y="{y + 6:g}">{symbol}</text>'
        f'<text class="component-label" x="{x:g}" y="{y + 44:g}">{escape(format_component_label(component))}</text>'
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
