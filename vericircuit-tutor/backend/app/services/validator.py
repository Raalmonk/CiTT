from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import CheckResult, ProblemStatus


@dataclass
class ValidationResult:
    valid: bool
    status: ProblemStatus
    circuit: CircuitProblem | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)


SUPPORTED_COMPONENT_TYPES = {
    "resistor",
    "voltage_source",
    "current_source",
    "capacitor",
    "op_amp_ideal",
}
NORMALIZED_UNITS = {
    "resistor": "ohm",
    "voltage_source": "V",
    "current_source": "A",
    "capacitor": "F",
    "op_amp_ideal": "ideal",
}
AC_SUPPORTED_COMPONENT_TYPES = {
    "resistor",
    "voltage_source",
    "current_source",
    "capacitor",
    "op_amp_ideal",
}
NONIDEAL_OP_AMP_FEATURE_TERMS = {
    "rail",
    "rails",
    "saturation",
    "slew",
    "bias current",
    "input bias",
    "finite bandwidth",
    "bandwidth",
    "supply node",
    "supply nodes",
    "frequency response",
}


def _add_check(
    checks: list[CheckResult],
    name: str,
    passed: bool,
    message: str,
    value: float | str | None = None,
) -> None:
    checks.append(CheckResult(name=name, passed=passed, message=message, value=value))


def _component_map(problem: CircuitProblem) -> dict[str, Component]:
    return {component.id: component for component in problem.components}


def reachable_from_ground(problem: CircuitProblem) -> set[str]:
    graph: dict[str, set[str]] = defaultdict(set)
    for component in problem.components:
        nodes = component.nodes
        for idx, a in enumerate(nodes):
            for b in nodes[idx + 1 :]:
                graph[a].add(b)
                graph[b].add(a)

    if problem.ground_node not in problem.nodes:
        return set()

    visited = {problem.ground_node}
    queue: deque[str] = deque([problem.ground_node])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited


def validate_circuit(problem: CircuitProblem) -> ValidationResult:
    normalized = problem.model_copy(deep=True)
    checks: list[CheckResult] = []
    errors: list[str] = []
    warnings: list[str] = []

    if normalized.unsupported_features:
        message = "Unsupported features: " + ", ".join(normalized.unsupported_features)
        _add_check(checks, "unsupported_features", False, message)
        return ValidationResult(
            valid=False,
            status="unsupported",
            circuit=normalized,
            errors=[message],
            warnings=warnings,
            checks=checks,
        )

    if normalized.ambiguities:
        message = "Ambiguities must be resolved before solving: " + "; ".join(
            normalized.ambiguities
        )
        _add_check(checks, "ambiguities", False, message)
        return ValidationResult(
            valid=False,
            status="ambiguous",
            circuit=normalized,
            errors=[message],
            warnings=warnings,
            checks=checks,
        )

    if normalized.analysis_type == "ac_single_frequency":
        frequency_valid = normalized.frequency_hz is not None and normalized.frequency_hz > 0
        _add_check(
            checks,
            "ac_frequency_present",
            frequency_valid,
            "AC single-frequency analysis has a positive frequency."
            if frequency_valid
            else "AC single-frequency analysis requires frequency_hz > 0.",
            value=normalized.frequency_hz,
        )
        if not frequency_valid:
            errors.append("ac_single_frequency analysis requires frequency_hz > 0.")

    if normalized.analysis_type == "ac_sweep":
        sweep_valid = normalized.sweep is not None
        _add_check(
            checks,
            "ac_sweep_config_present",
            sweep_valid,
            "AC sweep analysis has a sweep configuration."
            if sweep_valid
            else "AC sweep analysis requires a sweep configuration.",
        )
        if not sweep_valid:
            errors.append("ac_sweep analysis requires sweep config.")

    ground_exists = bool(normalized.ground_node) and normalized.ground_node in normalized.nodes
    _add_check(
        checks,
        "ground_exists",
        ground_exists,
        f"Ground node is {normalized.ground_node!r}." if ground_exists else "No ground node found.",
    )
    if not ground_exists:
        errors.append("Exactly one ground node must exist or be inferred as '0'.")

    component_ids = [component.id for component in normalized.components]
    unique_ids = len(component_ids) == len(set(component_ids))
    _add_check(
        checks,
        "component_ids_unique",
        unique_ids,
        "Component IDs are unique." if unique_ids else "Duplicate component IDs found.",
    )
    if not unique_ids:
        errors.append("Component IDs must be unique.")

    component_nodes_valid = True
    component_types_supported = True
    values_valid = True
    units_valid = True
    for component in normalized.components:
        if component.type not in SUPPORTED_COMPONENT_TYPES:
            errors.append(
                f"Unsupported component type {component.type!r} on {component.id}. "
                "Supported types are resistor, voltage_source, current_source, "
                "capacitor, and op_amp_ideal."
            )
            component_types_supported = False
            component_nodes_valid = False
        if normalized.analysis_type in {"ac_single_frequency", "ac_sweep"}:
            if component.type not in AC_SUPPORTED_COMPONENT_TYPES:
                errors.append(
                    f"Unsupported component type {component.type!r} for AC analysis on {component.id}."
                )
                component_types_supported = False
        if component.type == "op_amp_ideal":
            if len(component.nodes) != 4:
                errors.append(
                    f"{component.id} op_amp_ideal must have nodes "
                    "[non_inverting, inverting, output, reference]."
                )
                component_nodes_valid = False
            if component.unit != "ideal":
                units_valid = False
                errors.append(f"{component.id} should use normalized SI unit 'ideal'.")
            label = (component.label or "").lower()
            requested_nonideal = [
                term for term in NONIDEAL_OP_AMP_FEATURE_TERMS if term in label
            ]
            if requested_nonideal:
                errors.append(
                    f"{component.id} requests unsupported ideal op-amp behavior: "
                    + ", ".join(sorted(requested_nonideal))
                    + "."
                )
                component_types_supported = False
        elif len(component.nodes) != 2:
            errors.append(f"{component.id} must connect exactly two nodes.")
            component_nodes_valid = False
        for node in component.nodes:
            if node not in normalized.nodes:
                normalized.nodes.append(node)
                warnings.append(f"Added referenced node {node!r} to circuit node list.")
        if not math.isfinite(component.value):
            values_valid = False
            errors.append(f"{component.id} has a non-finite value.")
        if component.type == "resistor" and component.value <= 0:
            values_valid = False
            errors.append(f"{component.id} is a resistor and must have a positive value.")
        if component.type == "capacitor" and component.value <= 0:
            values_valid = False
            errors.append(f"{component.id} is a capacitor and must have a positive value.")
        if component.type in {"voltage_source", "current_source"}:
            if component.ac_magnitude is not None and component.ac_magnitude < 0:
                values_valid = False
                errors.append(f"{component.id} AC magnitude must be non-negative.")
        elif component.ac_magnitude is not None or component.ac_phase_deg is not None:
            warnings.append(
                f"{component.id} has AC phasor fields, but only sources use them."
            )
        expected_unit = NORMALIZED_UNITS.get(component.type)
        if expected_unit and component.unit != expected_unit:
            units_valid = False
            errors.append(
                f"{component.id} should use normalized SI unit {expected_unit!r}, "
                f"not {component.unit!r}."
            )

    _add_check(
        checks,
        "component_types_supported",
        component_types_supported,
        "All component types are supported."
        if component_types_supported
        else "One or more component types is outside the MVP scope.",
    )
    _add_check(
        checks,
        "component_nodes_valid",
        component_nodes_valid,
        "All component nodes are valid.",
    )
    _add_check(
        checks,
        "component_values_valid",
        values_valid,
        "All component values are finite and physically valid.",
    )
    _add_check(
        checks,
        "units_normalized",
        units_valid,
        "Component values use normalized SI units.",
    )

    components_by_id = _component_map(normalized)
    goal_targets_valid = True
    goal_references_valid = True
    for goal in normalized.goals:
        if goal.quantity == "node_voltage" and goal.target not in normalized.nodes:
            goal_targets_valid = False
            errors.append(f"Goal {goal.id} refers to missing node {goal.target!r}.")
        if goal.quantity != "node_voltage" and goal.target not in components_by_id:
            goal_targets_valid = False
            errors.append(f"Goal {goal.id} refers to missing component {goal.target!r}.")
        if goal.quantity == "source_power":
            component = components_by_id.get(goal.target)
            if component is not None and component.type not in {"voltage_source", "current_source"}:
                goal_targets_valid = False
                errors.append(f"Goal {goal.id} requests source power for non-source {goal.target!r}.")
        if goal.reference:
            if goal.quantity == "component_voltage":
                positive_node = goal.reference.get("positive_node")
                negative_node = goal.reference.get("negative_node")
                if positive_node is not None and positive_node not in normalized.nodes:
                    goal_references_valid = False
                    errors.append(
                        f"Goal {goal.id} voltage reference uses missing node {positive_node!r}."
                    )
                if negative_node is not None and negative_node not in normalized.nodes:
                    goal_references_valid = False
                    errors.append(
                        f"Goal {goal.id} voltage reference uses missing node {negative_node!r}."
                    )
            if goal.quantity == "component_current":
                from_node = goal.reference.get("from_node")
                to_node = goal.reference.get("to_node")
                if from_node is not None and from_node not in normalized.nodes:
                    goal_references_valid = False
                    errors.append(
                        f"Goal {goal.id} current reference uses missing node {from_node!r}."
                    )
                if to_node is not None and to_node not in normalized.nodes:
                    goal_references_valid = False
                    errors.append(
                        f"Goal {goal.id} current reference uses missing node {to_node!r}."
                    )

    _add_check(
        checks,
        "goal_targets_valid",
        goal_targets_valid,
        "All requested goals refer to known nodes or components.",
    )
    _add_check(
        checks,
        "goal_references_valid",
        goal_references_valid,
        "All goal reference nodes are known.",
    )

    reachable = reachable_from_ground(normalized)
    connectivity_valid = True
    if normalized.components and not reachable:
        connectivity_valid = False
        errors.append("Circuit graph is not connected to ground.")
    for node in normalized.nodes:
        if node not in reachable:
            components_using_node = [
                component.id for component in normalized.components if node in component.nodes
            ]
            if components_using_node:
                connectivity_valid = False
                errors.append(
                    f"Node {node!r} is not connected to ground through the circuit graph."
                )
    _add_check(
        checks,
        "graph_connected_to_ground",
        connectivity_valid,
        "All component nodes are connected to the ground-referenced circuit graph.",
        value=len(reachable),
    )

    if not errors:
        status: ProblemStatus = "solved"
    elif not component_types_supported:
        status = "unsupported"
    else:
        status = "invalid"
    return ValidationResult(
        valid=not errors,
        status=status,
        circuit=normalized,
        errors=errors,
        warnings=warnings,
        checks=checks,
    )
