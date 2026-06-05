from __future__ import annotations

from html import escape
from math import cos, pi, sin

try:
    import schemdraw
    import schemdraw.elements as elm
except ImportError:  # pragma: no cover - exercised only when dependencies are absent.
    schemdraw = None
    elm = None

from app.models.circuit_ir import CircuitProblem, Component


VARIANT_SUFFIXES = ("_value_variant", "_goal_variant")
UNIT = 3.0
FONT_SIZE_COMPONENT = 14
FONT_SIZE_NODE = 12
LABEL_OFFSET_SMALL = 0.35
LABEL_OFFSET_MEDIUM = 0.65
LABEL_OFFSET_LARGE = 0.95
CANVAS_PADDING = 0.55
BRIDGE_WIDTH = 1100
BRIDGE_HEIGHT = 560


def _configure_schemdraw_backend() -> None:
    if schemdraw is None:
        return
    try:
        schemdraw.use("svg")
    except Exception:
        pass
    try:
        schemdraw.svgconfig.text = "text"
    except Exception:
        pass


_configure_schemdraw_backend()


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
    raw = drawing.get_imagedata("svg")
    if isinstance(raw, bytes):
        svg = raw.decode("utf-8")
    else:
        svg = str(raw)
    svg = svg.lstrip()
    svg_start = svg.find("<svg")
    if svg_start > 0:
        svg = svg[svg_start:]
    return _tag_svg(svg, renderer)


def _tag_svg(svg: str, renderer: str) -> str:
    insert_at = svg.find(">") + 1
    if insert_at <= 0:
        return svg
    desc = f'<desc>VeriCircuit Tutor renderer: {escape(renderer)}</desc>'
    return f"{svg[:insert_at]}{desc}{svg[insert_at:]}"


def _manual_svg(width: int, height: int, body: str, renderer: str) -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Circuit schematic">
  <style>
    .bg {{ fill: #ffffff; }}
    .wire {{ stroke: #111827; stroke-width: 5; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
    .component {{ stroke: #111827; stroke-width: 5; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
    .node {{ fill: #111827; stroke: #ffffff; stroke-width: 2; }}
    .source {{ stroke: #111827; stroke-width: 5; fill: #ffffff; }}
    .label, .node-label, .component-label, .source-label {{
      font: 22px system-ui, sans-serif;
      fill: #111827;
      paint-order: stroke;
      stroke: #ffffff;
      stroke-width: 6px;
      stroke-linejoin: round;
    }}
    .source-symbol {{ font: 700 28px system-ui, sans-serif; fill: #111827; text-anchor: middle; dominant-baseline: central; }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}" />
  {body}
</svg>"""
    return _tag_svg(svg, renderer)


def _svg_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    class_name: str = "wire",
) -> str:
    return (
        f'<line class="{class_name}" x1="{x1:g}" y1="{y1:g}" '
        f'x2="{x2:g}" y2="{y2:g}" />'
    )


def _svg_dot(x: float, y: float) -> str:
    return f'<circle class="node" cx="{x:g}" cy="{y:g}" r="8" />'


def _svg_text(
    x: float,
    y: float,
    text: str,
    anchor: str = "middle",
    cls: str = "label",
) -> str:
    return (
        f'<text class="{cls}" x="{x:g}" y="{y:g}" text-anchor="{anchor}" '
        f'dominant-baseline="middle">{escape(text)}</text>'
    )


def _svg_label(x: float, y: float, text: str, anchor: str = "middle") -> str:
    return _svg_text(x, y, text, anchor=anchor, cls="component-label")


def _svg_ground(x: float, y: float) -> str:
    return "\n  ".join(
        [
            _svg_line(x, y, x, y + 20),
            _svg_line(x - 30, y + 20, x + 30, y + 20),
            _svg_line(x - 20, y + 32, x + 20, y + 32),
            _svg_line(x - 10, y + 44, x + 10, y + 44),
        ]
    )


def _zigzag_points_vertical(x: float, y1: float, y2: float) -> list[tuple[float, float]]:
    steps = 8
    span = y2 - y1
    amplitude = 18
    points = [(x, y1)]
    for idx in range(1, steps):
        y = y1 + span * idx / steps
        offset = amplitude if idx % 2 else -amplitude
        points.append((x + offset, y))
    points.append((x, y2))
    return points


def _zigzag_points_horizontal(x1: float, y: float, x2: float) -> list[tuple[float, float]]:
    steps = 8
    span = x2 - x1
    amplitude = 18
    points = [(x1, y)]
    for idx in range(1, steps):
        x = x1 + span * idx / steps
        offset = amplitude if idx % 2 else -amplitude
        points.append((x, y + offset))
    points.append((x2, y))
    return points


def _svg_path(points: list[tuple[float, float]], class_name: str = "component") -> str:
    commands = [f"M {points[0][0]:g} {points[0][1]:g}"]
    commands.extend(f"L {x:g} {y:g}" for x, y in points[1:])
    return f'<path class="{class_name}" d="{" ".join(commands)}" />'


def _svg_resistor_vertical(
    x: float,
    y1: float,
    y2: float,
    label: str,
    label_x: float,
    label_y: float,
    label_anchor: str,
) -> str:
    body_margin = 28
    z1 = y1 + body_margin
    z2 = y2 - body_margin
    return "\n  ".join(
        [
            _svg_line(x, y1, x, z1, "wire"),
            _svg_path(_zigzag_points_vertical(x, z1, z2), "component"),
            _svg_line(x, z2, x, y2, "wire"),
            _svg_label(label_x, label_y, label, label_anchor),
        ]
    )


def _svg_resistor_horizontal(
    x1: float,
    y: float,
    x2: float,
    label: str,
    label_x: float,
    label_y: float,
    label_anchor: str,
) -> str:
    body_margin = 28
    z1 = x1 + body_margin
    z2 = x2 - body_margin
    return "\n  ".join(
        [
            _svg_line(x1, y, z1, y, "wire"),
            _svg_path(_zigzag_points_horizontal(z1, y, z2), "component"),
            _svg_line(z2, y, x2, y, "wire"),
            _svg_label(label_x, label_y, label, label_anchor),
        ]
    )


def _component_label(
    element: elm.Element,
    component: Component,
    loc: str,
    ofst: float | tuple[float, float] = LABEL_OFFSET_MEDIUM,
) -> elm.Element:
    return element.label(
        format_component_label(component),
        loc=loc,
        ofst=ofst,
        rotate=False,
        fontsize=FONT_SIZE_COMPONENT,
    )


def _node_label(text: str, at: tuple[float, float]) -> elm.Label:
    label = elm.Label().at(at)
    try:
        return label.label(
            text,
            fontsize=FONT_SIZE_NODE,
            loc="center",
            ofst=0,
            rotate=False,
        )
    except Exception:
        return elm.Label().at(at).label(text, fontsize=FONT_SIZE_NODE)


def _dot(at: tuple[float, float]) -> elm.Dot:
    return elm.Dot().at(at)


def _base_drawing() -> schemdraw.Drawing:
    if schemdraw is None:
        raise RuntimeError("schemdraw is not installed")
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

    d += _component_label(elm.SourceV().at(bottom_left).to(top_left), c["V1"], "left", (-0.75, 0.1))
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

    d += _component_label(elm.SourceI().at(bottom_left).to(top_left), c["I1"], "left", (-0.75, 0.1))
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


def _render_bridge_manual_svg(problem: CircuitProblem) -> str:
    c = _components(problem)
    required = {"V1", "R1", "R2", "R3", "R4", "R5"}
    if not required <= set(c):
        return _render_fallback_graph(problem)

    source_node = "n1" if "n1" in problem.nodes else "src"
    left_mid = "n2" if "n2" in problem.nodes else "a"
    right_mid = "n3" if "n3" in problem.nodes else "b"

    source_x = 120
    top_y = 100
    bottom_y = 440
    left_x = 430
    right_x = 760
    mid_y = 270
    top_bus_right = 910
    bottom_bus_right = 910
    source_radius = 42

    r_top_end = mid_y - 45
    r_bottom_start = mid_y + 45
    r5_left = left_x + 55
    r5_right = right_x - 55
    r5_label_x = (left_x + right_x) / 2

    body = "\n  ".join(
        [
            _svg_line(source_x, top_y, top_bus_right, top_y),
            _svg_line(source_x, bottom_y, bottom_bus_right, bottom_y),
            _svg_line(source_x, top_y, source_x, mid_y - source_radius),
            _svg_line(source_x, mid_y + source_radius, source_x, bottom_y),
            f'<circle class="source" cx="{source_x:g}" cy="{mid_y:g}" r="{source_radius:g}" />',
            _svg_text(source_x, mid_y, "V", cls="source-symbol"),
            _svg_label(source_x - 70, bottom_y + 55, format_component_label(c["V1"])),
            _svg_text(source_x + 55, top_y - 28, source_node, anchor="start", cls="node-label"),
            _svg_text(source_x + 55, bottom_y + 40, "0", anchor="start", cls="node-label"),
            _svg_ground(source_x, bottom_y),
            _svg_dot(source_x, top_y),
            _svg_dot(source_x, bottom_y),
            _svg_dot(left_x, top_y),
            _svg_dot(left_x, bottom_y),
            _svg_dot(right_x, top_y),
            _svg_dot(right_x, bottom_y),
            _svg_resistor_vertical(
                left_x,
                top_y,
                r_top_end,
                format_component_label(c["R1"]),
                left_x - 95,
                (top_y + r_top_end) / 2,
                "end",
            ),
            _svg_line(left_x, r_top_end, left_x, mid_y),
            _svg_dot(left_x, mid_y),
            _svg_text(left_x - 45, mid_y - 18, left_mid, anchor="end", cls="node-label"),
            _svg_line(left_x, mid_y, left_x, r_bottom_start),
            _svg_resistor_vertical(
                left_x,
                r_bottom_start,
                bottom_y,
                format_component_label(c["R2"]),
                left_x - 95,
                (r_bottom_start + bottom_y) / 2,
                "end",
            ),
            _svg_resistor_vertical(
                right_x,
                top_y,
                r_top_end,
                format_component_label(c["R3"]),
                right_x + 95,
                (top_y + r_top_end) / 2,
                "start",
            ),
            _svg_line(right_x, r_top_end, right_x, mid_y),
            _svg_dot(right_x, mid_y),
            _svg_text(right_x + 45, mid_y - 18, right_mid, anchor="start", cls="node-label"),
            _svg_line(right_x, mid_y, right_x, r_bottom_start),
            _svg_resistor_vertical(
                right_x,
                r_bottom_start,
                bottom_y,
                format_component_label(c["R4"]),
                right_x + 95,
                (r_bottom_start + bottom_y) / 2,
                "start",
            ),
            _svg_line(left_x, mid_y, r5_left, mid_y),
            _svg_resistor_horizontal(
                r5_left,
                mid_y,
                r5_right,
                format_component_label(c["R5"]),
                r5_label_x,
                mid_y - 58,
                "middle",
            ),
            _svg_line(r5_right, mid_y, right_x, mid_y),
        ]
    )
    return _manual_svg(BRIDGE_WIDTH, BRIDGE_HEIGHT, body, "manual_svg_bridge_network")


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


def _render_fallback_graph(problem: CircuitProblem, renderer: str = "fallback_graph") -> str:
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
    return _svg(width, height, "\n  ".join(pieces), renderer)


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


def _render_template_or_fallback(circuit: CircuitProblem, renderer) -> str:
    try:
        return renderer(circuit)
    except Exception:
        return _render_fallback_graph(circuit, "fallback_graph_after_schemdraw_error")


def render_schematic_svg(circuit: CircuitProblem) -> str:
    key = _renderer_key(circuit)
    if key == "voltage_divider":
        return _render_template_or_fallback(circuit, _render_voltage_divider)
    if key == "current_divider":
        return _render_template_or_fallback(circuit, _render_current_divider)
    if key in {"bridge_network", "bridge_network_alt"}:
        return _render_template_or_fallback(circuit, _render_bridge_manual_svg)
    return _render_fallback_graph(circuit)
