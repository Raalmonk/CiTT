from __future__ import annotations

import math
from collections.abc import Iterable

from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import SolutionPacket, TutorFocus, TutorObservation, TutorStep


def focus(
    circuit: CircuitProblem,
    components: Iterable[str] = (),
    nodes: Iterable[str] = (),
    current_paths: Iterable[str] = (),
    goals: Iterable[str] = (),
) -> TutorFocus:
    component_ids = {component.id for component in circuit.components}
    node_ids = set(circuit.nodes)
    goal_ids = {goal.id for goal in circuit.goals}
    return TutorFocus(
        components=[item for item in components if item in component_ids],
        nodes=[item for item in nodes if item in node_ids],
        current_paths=[item for item in current_paths if item in component_ids],
        goals=[item for item in goals if item in goal_ids],
    )


def observation_lookup(packet: SolutionPacket) -> dict[str, TutorObservation]:
    return {observation.id: observation for observation in packet.tutor_observations}


def packet_observation(packet: SolutionPacket, observation_id: str) -> TutorObservation | None:
    return observation_lookup(packet).get(observation_id)


def only_present(values: Iterable[TutorObservation | None]) -> list[TutorObservation]:
    return [value for value in values if value is not None]


def node_voltage(packet: SolutionPacket, node_id: str, label: str | None = None) -> TutorObservation | None:
    if node_id not in packet.node_voltages:
        return None
    return TutorObservation(
        id=f"node_voltage_{node_id}",
        label=label or f"Node {node_id} voltage",
        value=float(packet.node_voltages[node_id]),
        unit="V",
        note="Verified node voltage from the Solution Packet.",
    )


def component_current(
    packet: SolutionPacket,
    component_id: str,
    label: str | None = None,
) -> TutorObservation | None:
    result = packet.component_results.get(component_id)
    if result is None:
        return None
    return TutorObservation(
        id=f"component_current_{component_id}",
        label=label or f"{component_id} current",
        value=float(result.current.value),
        unit=result.current.unit,
        note="Verified component current from the Solution Packet.",
    )


def requested_answer(
    packet: SolutionPacket,
    answer_id: str,
    label: str | None = None,
) -> TutorObservation | None:
    answer = packet.requested_answers.get(answer_id)
    if answer is None:
        return None
    return TutorObservation(
        id=answer_id,
        label=label or answer_id.replace("_", " "),
        value=float(answer.value),
        unit=answer.unit,
        note="Requested answer from the verified Solution Packet.",
    )


def requested_answer_for_goal(
    packet: SolutionPacket,
    goal_id: str,
    label: str | None = None,
) -> TutorObservation | None:
    return requested_answer(packet, goal_id, label)


def ac_answer_magnitude(
    packet: SolutionPacket,
    answer_id: str,
    label: str | None = None,
) -> TutorObservation | None:
    answer = packet.ac_requested_answers.get(answer_id)
    if answer is None:
        return None
    return TutorObservation(
        id=f"{answer_id}_magnitude",
        label=label or f"{answer_id.replace('_', ' ')} magnitude",
        value=float(answer.magnitude),
        unit=answer.unit,
        note="Requested AC answer magnitude from the verified Solution Packet.",
    )


def ac_answer_phase(packet: SolutionPacket, answer_id: str) -> TutorObservation | None:
    answer = packet.ac_requested_answers.get(answer_id)
    if answer is None:
        return None
    return TutorObservation(
        id=f"{answer_id}_phase",
        label=f"{answer_id.replace('_', ' ')} phase",
        value=float(answer.phase_deg),
        unit="deg",
        note="Requested AC answer phase from the verified Solution Packet.",
    )


def cutoff_frequency_observation(
    resistor: Component | None,
    capacitor: Component | None,
    observation_id: str = "low_pass_cutoff_frequency",
) -> TutorObservation | None:
    if resistor is None or capacitor is None or resistor.value <= 0 or capacitor.value <= 0:
        return None
    return TutorObservation(
        id=observation_id,
        label="Low-pass corner frequency",
        value=float(1.0 / (2.0 * math.pi * resistor.value * capacitor.value)),
        unit="Hz",
        note="Computed deterministically from the detected R and C values in Circuit IR.",
    )


def verification_observations(packet: SolutionPacket) -> list[TutorObservation]:
    values = [
        TutorObservation(
            id="internal_verification_status",
            label="Internal verification",
            note=packet.verification_badge.label,
        ),
        TutorObservation(
            id="reference_cross_check_status",
            label="Reference cross-check",
            note="not available",
        ),
    ]
    values.append(
        TutorObservation(
            id="max_kcl_residual",
            label="Max KCL residual",
            value=float(packet.verification.max_kcl_residual_a),
            unit="A",
            note="Internal circuit-law residual check.",
        )
    )
    values.append(
        TutorObservation(
            id="power_balance_error",
            label="Power-balance error",
            value=float(packet.verification.power_balance_error_w),
            unit="W",
            note="Internal power-balance check when applicable.",
        )
    )
    return values


def all_requested_observations(packet: SolutionPacket) -> list[TutorObservation]:
    observations = [
        TutorObservation(
            id=answer_id,
            label=answer_id.replace("_", " "),
            value=float(answer.value),
            unit=answer.unit,
            note="Requested answer from the verified Solution Packet.",
        )
        for answer_id, answer in packet.requested_answers.items()
    ]
    observations.extend(
        observation
        for answer_id, answer in packet.ac_requested_answers.items()
        for observation in [
            TutorObservation(
                id=f"{answer_id}_magnitude",
                label=f"{answer_id.replace('_', ' ')} magnitude",
                value=float(answer.magnitude),
                unit=answer.unit,
                note="Requested AC answer magnitude from the verified Solution Packet.",
            ),
            TutorObservation(
                id=f"{answer_id}_phase",
                label=f"{answer_id.replace('_', ' ')} phase",
                value=float(answer.phase_deg),
                unit="deg",
                note="Requested AC answer phase from the verified Solution Packet.",
            ),
        ]
    )
    return observations


def goal_focus_ids(circuit: CircuitProblem) -> tuple[list[str], list[str], list[str]]:
    component_focus: list[str] = []
    node_focus: list[str] = []
    goal_ids: list[str] = []
    for goal in circuit.goals:
        goal_ids.append(goal.id)
        if goal.quantity == "node_voltage":
            node_focus.append(goal.target)
        else:
            component_focus.append(goal.target)
    return component_focus, node_focus, goal_ids


def source_ids(circuit: CircuitProblem) -> list[str]:
    return [
        component.id
        for component in circuit.components
        if component.type in {"voltage_source", "current_source"}
    ]


def first_goal_id(circuit: CircuitProblem) -> str | None:
    return circuit.goals[0].id if circuit.goals else None


def verification_step(circuit: CircuitProblem, packet: SolutionPacket) -> TutorStep:
    component_focus, node_focus, goal_ids = goal_focus_ids(circuit)
    return TutorStep(
        id="verification_boundary",
        title="Inspect the verification boundary",
        body=(
            "The packet is internally verified and inspectable. Independent reference cross-checking is "
            "reported separately when available."
        ),
        look_at="Look at the answer and verification status together.",
        why_it_matters="Internal checks catch many failures, but independent oracle checks are a separate confidence layer.",
        common_mistake="Equating internal verification with absolute correctness.",
        focus=focus(circuit, components=component_focus, nodes=node_focus, goals=goal_ids),
        verified_values=verification_observations(packet),
        caution="Reference cross-check is reported separately from internal verification.",
    )
