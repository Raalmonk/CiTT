from __future__ import annotations

from app.models.circuit_ir import CircuitProblem, Component, Goal, is_ideal_op_amp_type
from app.services.bme_variant_generator import (
    BMEPracticeVariant,
    generate_bme_practice_variants,
    generate_bme_value_variant,
)


def generate_value_variant(problem: CircuitProblem) -> CircuitProblem:
    bme_variant = generate_bme_value_variant(problem)
    if bme_variant is not None:
        return bme_variant

    variant = problem.model_copy(deep=True)
    variant.id = f"{problem.id}_value_variant"
    variant.title = f"{problem.title} - Changed Values"
    variant.topology_id = problem.topology_id
    variant.layout_hint = problem.layout_hint.copy() if problem.layout_hint else None
    variant.assumptions = [
        *problem.assumptions,
        "Practice variant: topology is unchanged; component values were adjusted deterministically.",
    ]

    factors = [1.5, 0.75, 1.2, 0.9, 1.1, 1.35]
    for idx, component in enumerate(variant.components):
        factor = factors[idx % len(factors)]
        if component.type in {"resistor", "capacitor", "inductor"}:
            component.value = max(component.value * factor, 1e-9)
        elif component.type in {"voltage_source", "current_source"} and component.value != 0.0:
            component.value = component.value * factor
        if component.type in {"voltage_source", "current_source"} and component.ac_magnitude is not None:
            component.ac_magnitude = max(component.ac_magnitude * factor, 1e-12)

    if variant.frequency_hz is not None:
        variant.frequency_hz = variant.frequency_hz * 1.25
    if variant.sweep is not None:
        variant.sweep.start_hz = max(variant.sweep.start_hz * 0.8, 1e-12)
        variant.sweep.stop_hz = max(variant.sweep.stop_hz * 1.25, variant.sweep.start_hz * 1.01)
    return variant


def _existing_goal_keys(problem: CircuitProblem) -> set[tuple[str, str]]:
    return {(goal.quantity, goal.target) for goal in problem.goals}


def _component_goal_candidates(component: Component) -> list[Goal]:
    if is_ideal_op_amp_type(component.type):
        output_node = component.nodes[2]
        reference_node = component.nodes[3]
        return [
            Goal(
                id=f"{component.id}_output_voltage",
                quantity="component_voltage",
                target=component.id,
                reference={
                    "positive_node": output_node,
                    "negative_node": reference_node,
                },
            ),
            Goal(
                id=f"{component.id}_output_current",
                quantity="component_current",
                target=component.id,
                reference={"from_node": output_node, "to_node": reference_node},
            ),
            Goal(
                id=f"{component.id}_output_power",
                quantity="component_power",
                target=component.id,
                reference={"component": component.id},
            ),
        ]

    goals = [
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
    if component.type in {"voltage_source", "current_source"}:
        goals.append(
            Goal(
                id=f"{component.id}_source_power",
                quantity="source_power",
                target=component.id,
                reference={"component": component.id},
            )
        )
    return goals


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
        candidate_goals.extend(_component_goal_candidates(component))

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
    variant.topology_id = problem.topology_id
    variant.layout_hint = problem.layout_hint.copy() if problem.layout_hint else None
    variant.goals = [selected]
    variant.assumptions = [
        *problem.assumptions,
        "Practice variant: the circuit is unchanged; only the requested target changed.",
    ]
    return variant


def _bme_variant_payload(variant: BMEPracticeVariant) -> dict[str, object]:
    return {
        "kind": variant.kind,
        "prompt": variant.prompt,
        "description": variant.description,
        "circuit_ir": variant.circuit.model_dump(),
    }


def generate_value_variants(problem: CircuitProblem) -> list[dict[str, object]]:
    bme_variants = generate_bme_practice_variants(problem)
    if bme_variants:
        return [_bme_variant_payload(variant) for variant in bme_variants]

    value_variant = generate_value_variant(problem)
    return [
        {
            "kind": "same_topology_changed_values",
            "prompt": "What if the component values change?",
            "description": "Same topology with deterministic component value, AC, or sweep changes.",
            "circuit_ir": value_variant.model_dump(),
        }
    ]


def generate_variants(problem: CircuitProblem) -> list[dict[str, object]]:
    goal_variant = generate_goal_variant(problem)
    return [
        *generate_value_variants(problem),
        {
            "kind": "same_circuit_different_goal",
            "prompt": "What if the requested target changes?",
            "description": "Same circuit with a different requested target quantity.",
            "circuit_ir": goal_variant.model_dump(),
        },
    ]
