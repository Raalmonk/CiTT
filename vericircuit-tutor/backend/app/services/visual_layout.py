from __future__ import annotations

from collections import defaultdict, deque

from app.models.circuit_ir import CircuitProblem, Component, is_ideal_op_amp_type
from app.models.visual_layout import (
    VisualAnnotation,
    VisualCircuit,
    VisualComponent,
    VisualFocusRegion,
    VisualNode,
    VisualOverlay,
    VisualPoint,
    VisualWire,
)
from app.services.component_labels import format_component_label


VARIANT_SUFFIXES = ("_value_variant", "_goal_variant")


def build_visual_circuit(circuit: CircuitProblem) -> VisualCircuit:
    key = _renderer_key(circuit)
    positions, strategy = _node_positions(circuit, key)
    nodes = [
        VisualNode(
            id=node_id,
            label=node_id,
            position=VisualPoint(x=point[0], y=point[1]),
            role=_node_role(circuit, node_id),
        )
        for node_id, point in positions.items()
    ]
    components = [_visual_component(circuit, component, key) for component in circuit.components]
    annotations = _annotations(circuit)
    focus_regions = _focus_regions(circuit)
    overlays = _overlays(circuit, focus_regions)
    wires = [
        VisualWire(
            id=f"wire_{component.id}",
            component_id=component.id,
            from_node=component.nodes[0],
            to_node=component.nodes[1],
            points=[
                VisualPoint(x=positions[component.nodes[0]][0], y=positions[component.nodes[0]][1]),
                VisualPoint(x=positions[component.nodes[1]][0], y=positions[component.nodes[1]][1]),
            ],
        )
        for component in circuit.components
        if len(component.nodes) == 2
        and component.nodes[0] in positions
        and component.nodes[1] in positions
    ]
    return VisualCircuit(
        circuit_id=circuit.id,
        renderer=_renderer_name(key),
        layout_strategy=strategy,
        nodes=nodes,
        components=components,
        wires=wires,
        annotations=annotations,
        overlays=overlays,
        focus_regions=focus_regions,
        warnings=[] if key in {"voltage_divider", "current_divider", "bridge_network", "bridge_network_alt", "rc_low_pass"} else ["Fallback semantic layout for interaction anchors; SVG rendering is handled by OptCPV."],
    )


def _visual_component(circuit: CircuitProblem, component: Component, key: str) -> VisualComponent:
    role = "generic"
    if component.type in {"voltage_source", "current_source"}:
        role = "source"
    elif is_ideal_op_amp_type(component.type):
        role = "op_amp"
    elif key == "rc_low_pass" and component.type in {"resistor", "capacitor"}:
        role = "filter"
    elif "bridge" in key:
        role = "bridge"
    elif any(goal.target == component.id for goal in circuit.goals):
        role = "load"

    orientation = "auto"
    if is_ideal_op_amp_type(component.type):
        orientation = "triangle"
    elif key in {"voltage_divider", "current_divider"}:
        orientation = "vertical"
    elif key in {"rc_low_pass", "bridge_network", "bridge_network_alt"}:
        orientation = "horizontal" if len(component.nodes) == 2 and component.nodes[0] != circuit.ground_node and component.nodes[1] != circuit.ground_node else "vertical"

    return VisualComponent(
        id=component.id,
        type=component.type,
        label=format_component_label(component),
        nodes=component.nodes,
        role=role,  # type: ignore[arg-type]
        orientation=orientation,  # type: ignore[arg-type]
    )


def _annotations(circuit: CircuitProblem) -> list[VisualAnnotation]:
    annotations = [
        VisualAnnotation(
            id="ground_reference",
            kind="ground",
            label="Ground reference",
            target_type="node",
            target_id=circuit.ground_node,
        )
    ]
    for goal in circuit.goals:
        reference = goal.reference or {}
        if reference.get("positive_node") and reference.get("negative_node"):
            annotations.append(
                VisualAnnotation(
                    id=f"{goal.id}_polarity",
                    kind="polarity",
                    label="+/- requested voltage reference",
                    target_type="goal",
                    target_id=goal.id,
                )
            )
        elif goal.quantity == "node_voltage":
            annotations.append(
                VisualAnnotation(
                    id=f"{goal.id}_polarity",
                    kind="polarity",
                    label="Node voltage relative to ground",
                    target_type="goal",
                    target_id=goal.id,
                )
            )
    if circuit.analysis_type in {"ac_steady_state", "ac_single_frequency", "ac_sweep"}:
        annotations.append(
            VisualAnnotation(
                id="phasor_hint",
                kind="phasor",
                label="AC quantities are phasors with magnitude and phase.",
                target_type="circuit",
                target_id=circuit.id,
            )
        )
    return annotations


def _focus_regions(circuit: CircuitProblem) -> list[VisualFocusRegion]:
    regions = []
    for goal in circuit.goals:
        components = [] if goal.quantity == "node_voltage" else [goal.target]
        nodes = [goal.target] if goal.quantity == "node_voltage" else []
        reference = goal.reference or {}
        for key in ("positive_node", "negative_node", "from_node", "to_node"):
            node = reference.get(key)
            if isinstance(node, str) and node not in nodes:
                nodes.append(node)
        regions.append(
            VisualFocusRegion(
                id=f"goal_{goal.id}",
                label=f"Goal {goal.id}",
                components=components,
                nodes=nodes,
                goals=[goal.id],
            )
        )
    return regions


def _overlays(circuit: CircuitProblem, focus_regions: list[VisualFocusRegion]) -> list[VisualOverlay]:
    overlays = [
        VisualOverlay(
            id=f"{region.id}_reference_overlay",
            kind="goal_reference",
            label=f"Reference markers for {region.label}",
            focus_region_id=region.id,
            enabled_by_default=False,
        )
        for region in focus_regions
    ]
    if circuit.analysis_type == "dc_operating_point":
        overlays.append(
            VisualOverlay(
                id="kcl_node_overlay",
                kind="kcl_node",
                label="KCL arrows for the selected node when AnalysisView is available.",
            )
        )
    if circuit.analysis_type in {"ac_steady_state", "ac_single_frequency", "ac_sweep"}:
        overlays.append(
            VisualOverlay(
                id="phasor_overlay",
                kind="phasor_hint",
                label="Phasor magnitude and phase cue.",
            )
        )
    return overlays


def _node_positions(circuit: CircuitProblem, key: str) -> tuple[dict[str, tuple[float, float]], str]:
    ground = circuit.ground_node
    if key == "voltage_divider":
        return {"n1": (430, 90), "n2": (430, 260), ground: (430, 430)}, "template_voltage_divider"
    if key == "current_divider":
        return {"top": (460, 90), ground: (460, 430)}, "template_current_divider"
    if key in {"bridge_network", "bridge_network_alt"}:
        source = "n1" if "n1" in circuit.nodes else "src"
        left = "n2" if "n2" in circuit.nodes else "a"
        right = "n3" if "n3" in circuit.nodes else "b"
        return {
            source: (120, 100),
            left: (430, 270),
            right: (760, 270),
            ground: (120, 440),
        }, "template_bridge"
    if key == "rc_low_pass":
        return {
            "in": (150, 180),
            "out": (430, 180),
            ground: (430, 350),
        }, "template_rc_low_pass"
    return _fallback_positions(circuit), "fallback_left_to_right"


def _fallback_positions(circuit: CircuitProblem) -> dict[str, tuple[float, float]]:
    ground = circuit.ground_node
    positions: dict[str, tuple[float, float]] = {}
    graph: dict[str, set[str]] = defaultdict(set)
    for component in circuit.components:
        for idx, node_a in enumerate(component.nodes):
            for node_b in component.nodes[idx + 1 :]:
                graph[node_a].add(node_b)
                graph[node_b].add(node_a)

    depth = {ground: 0}
    queue: deque[str] = deque([ground])
    while queue:
        node = queue.popleft()
        for neighbor in sorted(graph[node]):
            if neighbor in depth:
                continue
            depth[neighbor] = depth[node] + 1
            queue.append(neighbor)

    for node in circuit.nodes:
        if node not in depth:
            depth[node] = max(depth.values(), default=0) + 1

    by_depth: dict[int, list[str]] = defaultdict(list)
    for node, node_depth in depth.items():
        by_depth[node_depth].append(node)

    for node_depth, nodes in by_depth.items():
        ordered = sorted(nodes, key=lambda item: (item != ground, item))
        column_x = 120 + node_depth * 190
        total_height = (len(ordered) - 1) * 90
        start_y = 210 - total_height / 2
        for index, node in enumerate(ordered):
            positions[node] = (column_x, start_y + index * 90)
    return positions


def _node_role(circuit: CircuitProblem, node_id: str):
    if node_id == circuit.ground_node:
        return "ground"
    if any(component.type in {"voltage_source", "current_source"} and node_id in component.nodes for component in circuit.components):
        return "input"
    if any(goal.target == node_id for goal in circuit.goals):
        return "output"
    return "internal"


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


def _renderer_name(key: str) -> str:
    return "optcpv"
