from __future__ import annotations

from app.models.circuit_ir import CircuitProblem, Goal


def generate_value_variant(problem: CircuitProblem) -> CircuitProblem:
    variant = problem.model_copy(deep=True)
    variant.id = f"{problem.id}_value_variant"
    variant.title = f"{problem.title} - Changed Values"
    variant.assumptions = [
        *problem.assumptions,
        "Practice variant: topology is unchanged; component values were adjusted deterministically.",
    ]

    factors = [1.5, 0.75, 1.2, 0.9, 1.1, 1.35]
    for idx, component in enumerate(variant.components):
        factor = factors[idx % len(factors)]
        if component.type == "resistor":
            component.value = max(component.value * factor, 1e-9)
        elif component.type in {"voltage_source", "current_source"}:
            component.value = component.value * factor
    return variant


def _existing_goal_keys(problem: CircuitProblem) -> set[tuple[str, str]]:
    return {(goal.quantity, goal.target) for goal in problem.goals}


def generate_goal_variant(problem: CircuitProblem) -> CircuitProblem:
    existing = _existing_goal_keys(problem)
    candidate_goals: list[Goal] = []
    for node in problem.nodes:
        if node != problem.ground_node:
            candidate_goals.append(
                Goal(
                    id=f"{node}_voltage",
                    quantity="node_voltage",
                    target=node,
                    reference={"positive_node": node, "negative_node": problem.ground_node},
                )
            )
    for component in problem.components:
        candidate_goals.extend(
            [
                Goal(
                    id=f"{component.id}_voltage",
                    quantity="component_voltage",
                    target=component.id,
                    reference={
                        "positive_node": component.nodes[0],
                        "negative_node": component.nodes[1],
                    },
                ),
                Goal(
                    id=f"{component.id}_current",
                    quantity="component_current",
                    target=component.id,
                    reference={"from_node": component.nodes[0], "to_node": component.nodes[1]},
                ),
                Goal(
                    id=f"{component.id}_power",
                    quantity="component_power",
                    target=component.id,
                    reference={"component": component.id},
                ),
            ]
        )
        if component.type in {"voltage_source", "current_source"}:
            candidate_goals.append(
                Goal(
                    id=f"{component.id}_source_power",
                    quantity="source_power",
                    target=component.id,
                    reference={"component": component.id},
                )
            )

    selected = next(
        (
            goal
            for goal in candidate_goals
            if (goal.quantity, goal.target) not in existing
        ),
        candidate_goals[0],
    )

    variant = problem.model_copy(deep=True)
    variant.id = f"{problem.id}_goal_variant"
    variant.title = f"{problem.title} - Different Target"
    variant.goals = [selected]
    variant.assumptions = [
        *problem.assumptions,
        "Practice variant: the circuit is unchanged; only the requested target changed.",
    ]
    return variant


def generate_variants(problem: CircuitProblem) -> list[dict[str, object]]:
    value_variant = generate_value_variant(problem)
    goal_variant = generate_goal_variant(problem)
    return [
        {
            "kind": "same_topology_changed_values",
            "description": "Same topology with deterministic component value changes.",
            "circuit_ir": value_variant.model_dump(),
        },
        {
            "kind": "same_circuit_different_goal",
            "description": "Same circuit with a different requested target quantity.",
            "circuit_ir": goal_variant.model_dump(),
        },
    ]

