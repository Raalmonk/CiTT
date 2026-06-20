from __future__ import annotations

import importlib
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.component_labels import format_component_label
from app.services.value_formatter import format_value

logger = logging.getLogger(__name__)

SchematicRenderer = Literal["optcpv"]


class OptCPVUnavailable(RuntimeError):
    """Raised when the optional OptCPV package cannot be imported."""


@dataclass(frozen=True)
class OptCPVBindings:
    from_citt_payload: Callable[[dict[str, Any]], Any]
    draw_svg: Callable[..., str]
    draw_optimized_svg: Callable[..., str]


def render_optcpv_schematic_svg(
    circuit: CircuitProblem,
    *,
    mode: Literal["raw", "optimized"] | None = None,
) -> str:
    bindings = _load_bindings()
    optcpv_circuit = bindings.from_citt_payload(_to_optcpv_payload(circuit))
    render_mode = _optcpv_render_mode(mode)

    if render_mode == "optimized":
        try:
            return bindings.draw_optimized_svg(
                optcpv_circuit,
                max_iterations=_optcpv_max_iterations(),
            )
        except Exception:
            logger.exception(
                "CiTT -> OptCPV optimized render failed; retrying raw OptCPV renderer."
            )

    return bindings.draw_svg(optcpv_circuit)


def _load_bindings() -> OptCPVBindings:
    _ensure_optcpv_path()
    try:
        adapter = importlib.import_module("optcpv.adapters.citt")
        optcpv = importlib.import_module("optcpv")
    except ImportError as exc:
        raise OptCPVUnavailable(
            "OptCPV is not importable. Install optcpv or set OPTCPV_PATH to its project root."
        ) from exc

    return OptCPVBindings(
        from_citt_payload=adapter.from_citt_payload,
        draw_svg=optcpv.draw_svg,
        draw_optimized_svg=optcpv.draw_optimized_svg,
    )


def _to_optcpv_payload(circuit: CircuitProblem) -> dict[str, Any]:
    payload = circuit.model_dump()
    payload["motif"] = circuit.topology_id or _layout_hint_value(circuit, "motif")
    payload["topology"] = circuit.topology_id
    payload["ground_node"] = circuit.ground_node
    output_node = _infer_output_node(circuit)
    if output_node:
        payload["output_node"] = output_node
    payload["goals"] = [_goal_payload(goal, circuit) for goal in circuit.goals]
    payload["components"] = [_component_payload(component) for component in circuit.components]
    return payload


def _component_payload(component: Component) -> dict[str, Any]:
    payload = component.model_dump()
    payload["label"] = (
        component.label
        if component.label and ("op_amp" in component.type or component.unit == "gain")
        else format_component_label(component)
    )
    payload["display_label"] = payload["label"]
    payload["value_label"] = payload["label"]
    payload["value"] = format_value(component.value, component.unit)
    return payload


def _goal_payload(goal: Goal, circuit: CircuitProblem) -> dict[str, Any]:
    payload = goal.model_dump()
    if goal.quantity == "node_voltage":
        payload["output_node"] = goal.target
        payload["target_node"] = goal.target
        payload["node"] = goal.target
    elif component := _component_by_id(circuit, goal.target):
        node = _first_non_ground_node(component.nodes, circuit.ground_node)
        if node:
            payload["output_node"] = node
            payload["target_node"] = node
            payload["node"] = node
    return payload


def _infer_output_node(circuit: CircuitProblem) -> str | None:
    for goal in circuit.goals:
        if goal.quantity == "node_voltage":
            return goal.target

    for goal in circuit.goals:
        component = _component_by_id(circuit, goal.target)
        if component:
            node = _first_non_ground_node(component.nodes, circuit.ground_node)
            if node:
                return node

    for component in reversed(circuit.components):
        node = _first_non_ground_node(component.nodes, circuit.ground_node)
        if node:
            return node
    return None


def _component_by_id(circuit: CircuitProblem, component_id: str) -> Component | None:
    return next(
        (component for component in circuit.components if component.id == component_id),
        None,
    )


def _first_non_ground_node(nodes: list[str], ground_node: str) -> str | None:
    return next((node for node in nodes if node != ground_node), None)


def _layout_hint_value(circuit: CircuitProblem, key: str) -> str | None:
    value = (circuit.layout_hint or {}).get(key)
    return str(value) if value is not None else None


def _ensure_optcpv_path() -> None:
    for candidate in _optcpv_path_candidates():
        if not candidate.exists():
            continue
        project_root = candidate.parent if candidate.name == "optcpv" else candidate
        if (project_root / "optcpv").is_dir() and str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            return


def _optcpv_path_candidates() -> list[Path]:
    configured = [
        Path(value).expanduser()
        for value in (os.getenv("OPTCPV_PATH"), os.getenv("OPTCPV_HOME"))
        if value
    ]
    return [
        *configured,
        Path.home() / "Documents" / "OptCPV",
    ]


def _optcpv_render_mode(
    explicit: Literal["raw", "optimized"] | None,
) -> Literal["raw", "optimized"]:
    raw_value = (
        explicit
        or os.getenv("CITT_OPTCPV_RENDER_MODE")
        or os.getenv("OPTCPV_RENDER_MODE")
        or "raw"
    )
    value = raw_value.strip().lower()
    if value in {"optimized", "optimize", "cv"}:
        return "optimized"
    return "raw"


def _optcpv_max_iterations() -> int:
    raw_value = os.getenv("CITT_OPTCPV_MAX_ITERATIONS", "5")
    try:
        return max(0, int(raw_value))
    except ValueError:
        logger.warning("Invalid CITT_OPTCPV_MAX_ITERATIONS=%r; using 5.", raw_value)
        return 5
