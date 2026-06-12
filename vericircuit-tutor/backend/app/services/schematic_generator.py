from __future__ import annotations

from html import escape
from math import cos, pi, sin

try:
    import schemdraw
    import schemdraw.elements as elm
except ImportError:  # pragma: no cover - exercised only when dependencies are absent.
    schemdraw = None
    elm = None

from app.models.circuit_ir import CircuitProblem, Component, is_ideal_op_amp_type


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
    if unit == "F" and 0 < abs(value) < 1:
        return f"{value * 1_000_000:g} uF"
    if unit == "H" and 0 < abs(value) < 1:
        return f"{value * 1000:g} mH"
    if unit == "ideal":
        return "ideal"
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
    .circuit-component {{ cursor: pointer; }}
    .circuit-node {{ cursor: pointer; }}
    .circuit-component:hover .component-label,
    .circuit-node:hover .node-label {{ fill: #1768ac; }}
    .current-path {{
      stroke: transparent;
      stroke-width: 8;
      fill: none;
      pointer-events: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
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


def _attr(value: str) -> str:
    return escape(value, quote=True)


def _svg_component_group(component_id: str, body: str) -> str:
    return (
        f'<g class="circuit-component" data-component-id="{_attr(component_id)}">\n'
        f"  {body}\n"
        "</g>"
    )


def _svg_node_group(node_id: str, body: str) -> str:
    return (
        f'<g class="circuit-node" data-node-id="{_attr(node_id)}">\n'
        f"  {body}\n"
        "</g>"
    )


def _svg_current_path(component_id: str, points: list[tuple[float, float]]) -> str:
    commands = [f"M {points[0][0]:g} {points[0][1]:g}"]
    commands.extend(f"L {x:g} {y:g}" for x, y in points[1:])
    return (
        f'<path class="current-path" data-component-id="{_attr(component_id)}" '
        f'd="{" ".join(commands)}" />'
    )


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


def _svg_source_vertical(
    x: float,
    y1: float,
    y2: float,
    component: Component,
    symbol: str,
    label_x: float,
    label_y: float,
    label_anchor: str = "middle",
) -> str:
    radius = 38
    mid_y = (y1 + y2) / 2
    return "\n  ".join(
        [
            _svg_line(x, y1, x, mid_y - radius, "wire"),
            _svg_line(x, mid_y + radius, x, y2, "wire"),
            f'<circle class="source" cx="{x:g}" cy="{mid_y:g}" r="{radius:g}" />',
            _svg_text(x, mid_y, symbol, cls="source-symbol"),
            _svg_label(label_x, label_y, format_component_label(component), label_anchor),
            _svg_current_path(component.id, [(x, y1), (x, y2)]),
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
    source_x = 120
    branch_x = 430
    top_y = 90
    mid_y = 260
    bottom_y = 430

    body = "\n  ".join(
        [
            _svg_line(source_x, top_y, branch_x, top_y),
            _svg_line(branch_x, bottom_y, source_x, bottom_y),
            _svg_component_group(
                "V1",
                _svg_source_vertical(
                    source_x,
                    top_y,
                    bottom_y,
                    c["V1"],
                    "V",
                    source_x - 72,
                    mid_y,
                    "end",
                ),
            ),
            _svg_component_group(
                "R1",
                "\n  ".join(
                    [
                        _svg_resistor_vertical(
                            branch_x,
                            top_y,
                            mid_y,
                            format_component_label(c["R1"]),
                            branch_x + 85,
                            (top_y + mid_y) / 2,
                            "start",
                        ),
                        _svg_current_path("R1", [(branch_x, top_y), (branch_x, mid_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R2",
                "\n  ".join(
                    [
                        _svg_resistor_vertical(
                            branch_x,
                            mid_y,
                            bottom_y,
                            format_component_label(c["R2"]),
                            branch_x + 85,
                            (mid_y + bottom_y) / 2,
                            "start",
                        ),
                        _svg_current_path("R2", [(branch_x, mid_y), (branch_x, bottom_y)]),
                    ]
                ),
            ),
            _svg_node_group(
                "n1",
                "\n  ".join(
                    [
                        _svg_dot(source_x, top_y),
                        _svg_dot(branch_x, top_y),
                        _svg_text(branch_x + 42, top_y - 32, "n1", anchor="start", cls="node-label"),
                    ]
                ),
            ),
            _svg_node_group(
                "n2",
                "\n  ".join(
                    [
                        _svg_dot(branch_x, mid_y),
                        _svg_text(branch_x - 42, mid_y, "n2", anchor="end", cls="node-label"),
                    ]
                ),
            ),
            _svg_node_group(
                "0",
                "\n  ".join(
                    [
                        _svg_dot(source_x, bottom_y),
                        _svg_dot(branch_x, bottom_y),
                        _svg_text(branch_x + 42, bottom_y + 38, "0", anchor="start", cls="node-label"),
                        _svg_ground(source_x, bottom_y),
                    ]
                ),
            ),
        ]
    )
    return _manual_svg(620, 520, body, "schemdraw_voltage_divider")


def _render_current_divider(problem: CircuitProblem) -> str:
    c = _components(problem)
    source_x = 120
    r1_x = 360
    r2_x = 560
    top_y = 90
    bottom_y = 430

    body = "\n  ".join(
        [
            _svg_line(source_x, top_y, r2_x, top_y),
            _svg_line(r2_x, bottom_y, source_x, bottom_y),
            _svg_component_group(
                "I1",
                _svg_source_vertical(
                    source_x,
                    bottom_y,
                    top_y,
                    c["I1"],
                    "I",
                    source_x - 72,
                    (top_y + bottom_y) / 2,
                    "end",
                ),
            ),
            _svg_component_group(
                "R1",
                "\n  ".join(
                    [
                        _svg_resistor_vertical(
                            r1_x,
                            top_y,
                            bottom_y,
                            format_component_label(c["R1"]),
                            r1_x - 80,
                            (top_y + bottom_y) / 2,
                            "end",
                        ),
                        _svg_current_path("R1", [(r1_x, top_y), (r1_x, bottom_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R2",
                "\n  ".join(
                    [
                        _svg_resistor_vertical(
                            r2_x,
                            top_y,
                            bottom_y,
                            format_component_label(c["R2"]),
                            r2_x + 80,
                            (top_y + bottom_y) / 2,
                            "start",
                        ),
                        _svg_current_path("R2", [(r2_x, top_y), (r2_x, bottom_y)]),
                    ]
                ),
            ),
            _svg_node_group(
                "top",
                "\n  ".join(
                    [
                        _svg_dot(source_x, top_y),
                        _svg_dot(r1_x, top_y),
                        _svg_dot(r2_x, top_y),
                        _svg_text(r1_x, top_y - 38, "top", anchor="middle", cls="node-label"),
                    ]
                ),
            ),
            _svg_node_group(
                "0",
                "\n  ".join(
                    [
                        _svg_dot(source_x, bottom_y),
                        _svg_dot(r1_x, bottom_y),
                        _svg_dot(r2_x, bottom_y),
                        _svg_text(r1_x, bottom_y + 38, "0", anchor="middle", cls="node-label"),
                        _svg_ground(source_x, bottom_y),
                    ]
                ),
            ),
        ]
    )
    return _manual_svg(740, 520, body, "schemdraw_current_divider")


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
            _svg_component_group(
                "V1",
                "\n  ".join(
                    [
                        _svg_line(source_x, top_y, source_x, mid_y - source_radius),
                        _svg_line(source_x, mid_y + source_radius, source_x, bottom_y),
                        f'<circle class="source" cx="{source_x:g}" cy="{mid_y:g}" r="{source_radius:g}" />',
                        _svg_text(source_x, mid_y, "V", cls="source-symbol"),
                        _svg_label(source_x - 70, bottom_y + 55, format_component_label(c["V1"])),
                        _svg_current_path("V1", [(source_x, top_y), (source_x, bottom_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R1",
                "\n  ".join(
                    [
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
                        _svg_current_path("R1", [(left_x, top_y), (left_x, mid_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R2",
                "\n  ".join(
                    [
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
                        _svg_current_path("R2", [(left_x, mid_y), (left_x, bottom_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R3",
                "\n  ".join(
                    [
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
                        _svg_current_path("R3", [(right_x, top_y), (right_x, mid_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R4",
                "\n  ".join(
                    [
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
                        _svg_current_path("R4", [(right_x, mid_y), (right_x, bottom_y)]),
                    ]
                ),
            ),
            _svg_component_group(
                "R5",
                "\n  ".join(
                    [
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
                        _svg_current_path("R5", [(left_x, mid_y), (right_x, mid_y)]),
                    ]
                ),
            ),
            _svg_node_group(
                source_node,
                "\n  ".join(
                    [
                        _svg_dot(source_x, top_y),
                        _svg_dot(left_x, top_y),
                        _svg_dot(right_x, top_y),
                        _svg_text(source_x + 55, top_y - 28, source_node, anchor="start", cls="node-label"),
                    ]
                ),
            ),
            _svg_node_group(
                "0",
                "\n  ".join(
                    [
                        _svg_dot(source_x, bottom_y),
                        _svg_dot(left_x, bottom_y),
                        _svg_dot(right_x, bottom_y),
                        _svg_text(source_x + 55, bottom_y + 40, "0", anchor="start", cls="node-label"),
                        _svg_ground(source_x, bottom_y),
                    ]
                ),
            ),
            _svg_node_group(
                left_mid,
                "\n  ".join(
                    [
                        _svg_dot(left_x, mid_y),
                        _svg_text(left_x - 45, mid_y - 18, left_mid, anchor="end", cls="node-label"),
                    ]
                ),
            ),
            _svg_node_group(
                right_mid,
                "\n  ".join(
                    [
                        _svg_dot(right_x, mid_y),
                        _svg_text(right_x + 45, mid_y - 18, right_mid, anchor="start", cls="node-label"),
                    ]
                ),
            ),
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


def _fallback_capacitor(component: Component, x1: float, y1: float, x2: float, y2: float) -> str:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    gap = 10
    plate = 18
    ax = mid_x - ux * gap
    ay = mid_y - uy * gap
    bx = mid_x + ux * gap
    by = mid_y + uy * gap
    return "\n".join(
        [
            _wire(x1, y1, ax, ay),
            _wire(bx, by, x2, y2),
            f'<line class="component capacitor" x1="{ax + px * plate:g}" y1="{ay + py * plate:g}" x2="{ax - px * plate:g}" y2="{ay - py * plate:g}" />',
            f'<line class="component capacitor" x1="{bx + px * plate:g}" y1="{by + py * plate:g}" x2="{bx - px * plate:g}" y2="{by - py * plate:g}" />',
            f'<text class="component-label" x="{mid_x:g}" y="{mid_y - 32:g}">{escape(format_component_label(component))}</text>',
        ]
    )


def _fallback_inductor(component: Component, x1: float, y1: float, x2: float, y2: float) -> str:
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    symbol_length = min(length * 0.5, 88.0)
    start_x = (x1 + x2) / 2 - ux * symbol_length / 2
    start_y = (y1 + y2) / 2 - uy * symbol_length / 2
    end_x = (x1 + x2) / 2 + ux * symbol_length / 2
    end_y = (y1 + y2) / 2 + uy * symbol_length / 2
    radius = min(14.0, symbol_length / 5)
    coils = []
    turns = 4
    step = symbol_length / turns
    for index in range(turns):
        sx = start_x + ux * step * index
        sy = start_y + uy * step * index
        ex = start_x + ux * step * (index + 1)
        ey = start_y + uy * step * (index + 1)
        c1x = sx + ux * step * 0.25 + px * radius
        c1y = sy + uy * step * 0.25 + py * radius
        c2x = sx + ux * step * 0.75 + px * radius
        c2y = sy + uy * step * 0.75 + py * radius
        coils.append(f"C {c1x:g},{c1y:g} {c2x:g},{c2y:g} {ex:g},{ey:g}")
    path = f"M {start_x:g},{start_y:g} " + " ".join(coils)
    return "\n".join(
        [
            _wire(x1, y1, start_x, start_y),
            _wire(end_x, end_y, x2, y2),
            f'<path class="component inductor" d="{path}" />',
            f'<text class="component-label" x="{(x1 + x2) / 2:g}" y="{(y1 + y2) / 2 - 32:g}">{escape(format_component_label(component))}</text>',
        ]
    )


def _fallback_source(component: Component, x: float, y: float) -> str:
    symbol = "V" if component.type == "voltage_source" else "I"
    return (
        f'<circle class="source" cx="{x:g}" cy="{y:g}" r="24" />'
        f'<text class="source-symbol" x="{x:g}" y="{y + 6:g}">{symbol}</text>'
        f'<text class="component-label" x="{x:g}" y="{y + 44:g}">{escape(format_component_label(component))}</text>'
    )


def _fallback_op_amp(component: Component, positions: dict[str, tuple[float, float]]) -> str:
    vp, vm, out, ref = component.nodes
    node_points = [positions[node] for node in component.nodes]
    center_x = sum(point[0] for point in node_points) / len(node_points)
    center_y = sum(point[1] for point in node_points) / len(node_points)
    left_x = center_x - 34
    right_x = center_x + 42
    top_y = center_y - 42
    bottom_y = center_y + 42
    out_x, out_y = positions[out]
    ref_x, ref_y = positions[ref]
    vp_x, vp_y = positions[vp]
    vm_x, vm_y = positions[vm]
    return "\n".join(
        [
            _wire(vp_x, vp_y, left_x, center_y - 18),
            _wire(vm_x, vm_y, left_x, center_y + 18),
            _wire(right_x, center_y, out_x, out_y),
            _wire(center_x, bottom_y, ref_x, ref_y),
            f'<polygon class="component opamp" points="{left_x:g},{top_y:g} {left_x:g},{bottom_y:g} {right_x:g},{center_y:g}" />',
            f'<text class="source-symbol" x="{left_x + 12:g}" y="{center_y - 18:g}">+</text>',
            f'<text class="source-symbol" x="{left_x + 12:g}" y="{center_y + 18:g}">-</text>',
            f'<text class="component-label" x="{center_x:g}" y="{top_y - 10:g}">{escape(format_component_label(component))}</text>',
        ]
    )


def _svg(width: int, height: int, body: str, renderer: str) -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Circuit schematic">
  <style>
    .bg {{ fill: #ffffff; }}
    .wire {{ stroke: #1f2937; stroke-width: 2.4; fill: none; }}
    .component {{ stroke: #1768ac; stroke-width: 4; stroke-linecap: round; fill: none; }}
    .resistor {{ stroke-dasharray: 7 5; }}
    .capacitor {{ stroke: #1768ac; }}
    .inductor {{ stroke: #1768ac; }}
    .opamp {{ fill: #ffffff; stroke: #1768ac; }}
    .source {{ stroke: #117a4b; stroke-width: 3; fill: #eef8f3; }}
    .node {{ fill: #111827; }}
    .circuit-component {{ cursor: pointer; }}
    .circuit-node {{ cursor: pointer; }}
    .current-path {{
      stroke: transparent;
      stroke-width: 8;
      fill: none;
      pointer-events: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
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
        node_points = [positions[node] for node in component.nodes]
        if is_ideal_op_amp_type(component.type):
            pieces.append(_svg_component_group(component.id, _fallback_op_amp(component, positions)))
            continue
        x1, y1 = positions[component.nodes[0]]
        x2, y2 = positions[component.nodes[1]]
        if component.type == "resistor":
            component_body = _fallback_resistor(component, x1, y1, x2, y2)
        elif component.type == "capacitor":
            component_body = _fallback_capacitor(component, x1, y1, x2, y2)
        elif component.type == "inductor":
            component_body = _fallback_inductor(component, x1, y1, x2, y2)
        elif component.type in {"voltage_source", "current_source"}:
            component_body = "\n".join(
                [
                    _wire(x1, y1, x2, y2),
                    _fallback_source(component, (x1 + x2) / 2, (y1 + y2) / 2),
                ]
            )
        else:
            component_body = _wire(x1, y1, x2, y2)
        current_path = _svg_current_path(component.id, [(x, y) for x, y in node_points[:2]])
        pieces.append(_svg_component_group(component.id, "\n".join([component_body, current_path])))
    for node, (x, y) in positions.items():
        pieces.append(_svg_node_group(node, _node(node, x, y)))
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
