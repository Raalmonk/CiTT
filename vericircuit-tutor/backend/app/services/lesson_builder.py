from __future__ import annotations

import re
from collections.abc import Iterable

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import (
    LessonCheck,
    LessonEquationStep,
    LessonPacket,
    LessonValueRef,
    SolutionPacket,
    TutorFocus,
    TutorObservation,
    TutorStep,
)
from app.services.value_formatter import format_complex_quantity, format_observation, format_quantity, format_value


SAFE_NUMERIC_CONSTANTS = {"0", "1", "2"}
NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?(?![A-Za-z_])", re.IGNORECASE)


def build_lesson_packet(circuit: CircuitProblem, packet: SolutionPacket) -> LessonPacket | None:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return None

    steps = packet.guided_steps
    value_refs = _build_value_refs(packet, steps)
    return LessonPacket(
        summary=_summary(circuit, packet),
        learning_objectives=_learning_objectives(circuit, packet),
        conceptual_overview=_conceptual_overview(circuit, packet),
        step_by_step_derivation=steps,
        equation_steps=_equation_steps(circuit, packet, steps),
        visual_cues=_visual_cues(steps),
        common_mistakes=_common_mistakes(steps),
        checks=_checks(packet),
        practice_prompts=_practice_prompts(circuit),
        verified_value_refs=value_refs,
        limitations=_limitations(circuit, packet),
    )


def lesson_has_unverified_numeric_claims(lesson: LessonPacket) -> bool:
    return bool(unverified_numeric_claims(lesson))


def unverified_numeric_claims(lesson: LessonPacket) -> list[str]:
    offenders: list[str] = []
    for text in _lesson_teaching_text(lesson):
        for token in NUMERIC_TOKEN_RE.findall(text):
            normalized = token.lstrip("+")
            if normalized in SAFE_NUMERIC_CONSTANTS:
                continue
            offenders.append(token)
    return offenders


def _lesson_teaching_text(lesson: LessonPacket) -> Iterable[str]:
    yield lesson.summary
    yield from lesson.learning_objectives
    yield from lesson.conceptual_overview
    yield from lesson.visual_cues
    yield from lesson.common_mistakes
    yield from lesson.practice_prompts
    yield from lesson.limitations
    for step in lesson.step_by_step_derivation:
        yield step.title
        yield step.body
        if step.look_at:
            yield step.look_at
        if step.why_it_matters:
            yield step.why_it_matters
        if step.common_mistake:
            yield step.common_mistake
        if step.caution:
            yield step.caution
        if step.next_action:
            yield step.next_action
    for equation in lesson.equation_steps:
        yield equation.title
        yield equation.equation
        yield equation.explanation
    for check in lesson.checks:
        yield check.label
        yield check.explanation


def _summary(circuit: CircuitProblem, packet: SolutionPacket) -> str:
    if packet.transient_response:
        return "A verified first-order transient lesson is available for the requested capacitor response."
    if packet.ac_requested_answers or packet.ac_sweep:
        return "A verified AC phasor lesson is available for the requested frequency-domain quantity."
    if circuit.bme_metadata is not None:
        return "A verified ideal-circuit lesson is available with cautious biomedical signal-chain context."
    return "A verified DC operating-point lesson is available for the requested circuit quantities."


def _learning_objectives(circuit: CircuitProblem, packet: SolutionPacket) -> list[str]:
    objectives = [
        "Identify the reference node, requested target, and sign convention before reading numbers.",
        "Connect each answer to solver-backed values in the Solution Packet.",
        "Use the verification badge and checks to separate verified results from unsupported claims.",
    ]
    if circuit.topology_id == "voltage_divider":
        objectives.insert(1, "Explain why one series current creates the divider voltage.")
    elif circuit.topology_id == "current_divider":
        objectives.insert(1, "Explain why parallel branches share the source current.")
    elif "bridge" in (circuit.topology_id or circuit.id):
        objectives.insert(1, "Use nodal analysis when a simple divider shortcut is not enough.")
    if packet.ac_requested_answers or packet.ac_sweep:
        objectives.insert(1, "Relate impedance, magnitude, and phase to the requested phasor.")
    if packet.transient_response:
        objectives.insert(1, "Relate initial value, final value, and time constant to the exponential response.")
    if circuit.bme_metadata is not None:
        objectives.append("Keep educational biomedical context separate from safety certification.")
    return objectives


def _conceptual_overview(circuit: CircuitProblem, packet: SolutionPacket) -> list[str]:
    overview = [
        f"What are we solving? The circuit is modeled as {circuit.analysis_type.replace('_', ' ')} with ground node {circuit.ground_node}.",
        "What circuit law applies? The solver enforces KCL through Modified Nodal Analysis and then checks the result.",
        "Where do numbers come from? User-visible values in the lesson are formatted from SolutionPacket fields or deterministic tutor observations.",
    ]
    if circuit.topology_id == "voltage_divider":
        overview.append("Series intuition comes first: the same branch current flows through both divider resistors.")
    elif circuit.topology_id == "current_divider":
        overview.append("Parallel intuition comes first: the branch voltages match while current splits by conductance.")
    elif "bridge" in (circuit.topology_id or circuit.id):
        overview.append("Bridge intuition: the middle resistor couples the divider midpoints, so independent divider shortcuts can fail.")
    if packet.ac_requested_answers or packet.ac_sweep:
        overview.append("AC intuition: impedance makes the answer a phasor with magnitude and phase, not only a scalar.")
    if packet.transient_response:
        overview.append("Transient intuition: the capacitor voltage approaches its final value exponentially.")
    if circuit.bme_metadata is not None:
        overview.append("Biomedical context is a teaching layer around the verified circuit result, not medical-device compliance.")
    return overview


def _equation_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    steps: list[TutorStep],
) -> list[LessonEquationStep]:
    focus = steps[0].focus if steps else TutorFocus()
    equations = [
        LessonEquationStep(
            id="sign_convention",
            title="Use the packet sign convention",
            equation="V_component = V(nodes[0]) - V(nodes[1]); I is positive from nodes[0] to nodes[1]",
            explanation="This defines polarity and current direction before any requested answer is read.",
            focus=focus,
        )
    ]
    if packet.transient_response:
        equations.extend(_rc_equations(packet, steps))
    elif packet.ac_requested_answers or packet.ac_sweep:
        equations.extend(_ac_equations(packet, steps))
    else:
        equations.extend(_dc_equations(circuit, packet, steps))
    equations.append(
        LessonEquationStep(
            id="verification_equation",
            title="Verify the solved packet",
            equation="sum I_leaving(node) = 0; sum P_signed = 0 when DC power balance applies",
            explanation="The tutor explains only after these deterministic checks pass.",
            focus=steps[-1].focus if steps else TutorFocus(),
            value_refs=["max_kcl_residual", "power_balance_error"],
        )
    )
    return equations


def _dc_equations(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    steps: list[TutorStep],
) -> list[LessonEquationStep]:
    focus = _focus_by_step(steps, "divider_series_path") or _focus_by_step(steps, "current_divider_parallel_branches") or (steps[0].focus if steps else TutorFocus())
    if circuit.topology_id == "voltage_divider":
        return [
            LessonEquationStep(
                id="series_current",
                title="Use one series current",
                equation="I_series = V_source / R_total",
                explanation="The divider resistors share one current path, so current is solved once and reused for voltage drops.",
                focus=focus,
                value_refs=["circuit_current"],
            ),
            LessonEquationStep(
                id="divider_output_readout",
                title="Read the requested divider value",
                equation="V_out = voltage across the requested lower branch or output node reference",
                explanation="The requested answer is extracted from the verified packet with its stated polarity.",
                focus=_focus_by_step(steps, "divider_output") or focus,
                value_refs=list(packet.requested_answers),
            ),
        ]
    if circuit.topology_id == "current_divider":
        return [
            LessonEquationStep(
                id="parallel_current_split",
                title="Use common branch voltage",
                equation="I_branch = V_common / R_branch",
                explanation="Parallel branches share node voltage, and the source current splits among conductances.",
                focus=focus,
                value_refs=list(packet.requested_answers),
            )
        ]
    if "bridge" in (circuit.topology_id or circuit.id):
        return [
            LessonEquationStep(
                id="bridge_nodal_kcl",
                title="Write KCL at bridge interior nodes",
                equation="sum conductance*(V_node - V_neighbor) = injected current",
                explanation="The bridge resistor couples the midpoint nodes, so nodal equations replace a simple divider shortcut.",
                focus=focus,
                value_refs=list(packet.requested_answers),
            )
        ]
    return [
        LessonEquationStep(
            id="dc_nodal_kcl",
            title="Write nodal KCL",
            equation="sum I_leaving(node) = 0",
            explanation="Unknown node voltages are solved by balancing currents at each non-reference node.",
            focus=focus,
            value_refs=list(packet.requested_answers),
        )
    ]


def _ac_equations(packet: SolutionPacket, steps: list[TutorStep]) -> list[LessonEquationStep]:
    return [
        LessonEquationStep(
            id="ac_impedance",
            title="Convert storage elements to impedance",
            equation="Z_C = 1/(j*omega*C); Z_L = j*omega*L",
            explanation="The AC solver uses complex impedance, so the answer carries magnitude and phase.",
            focus=_focus_by_step(steps, "ac_low_pass_pole") or (steps[0].focus if steps else TutorFocus()),
            value_refs=["analysis_frequency", "low_pass_cutoff_frequency"],
        ),
        LessonEquationStep(
            id="phasor_answer",
            title="Read magnitude and phase together",
            equation="phasor = magnitude angle phase",
            explanation="The output may be attenuated and phase shifted at the selected frequency.",
            focus=_focus_by_step(steps, "ac_output_phasor") or (steps[0].focus if steps else TutorFocus()),
            value_refs=[item for goal_id in packet.ac_requested_answers for item in [f"{goal_id}_magnitude", f"{goal_id}_phase"]],
        ),
    ]


def _rc_equations(packet: SolutionPacket, steps: list[TutorStep]) -> list[LessonEquationStep]:
    response = packet.transient_response
    refs = ["initial_capacitor_voltage", "final_capacitor_voltage", "thevenin_resistance", "time_constant"]
    return [
        LessonEquationStep(
            id="rc_time_constant",
            title="Compute the time scale",
            equation="tau = R_seen_by_C * C",
            explanation="The deterministic transient solver computes the resistance seen by the capacitor and multiplies by capacitance.",
            focus=_focus_by_step(steps, "rc_time_constant") or (steps[0].focus if steps else TutorFocus()),
            value_refs=refs,
        ),
        LessonEquationStep(
            id="rc_exponential",
            title="Use exponential approach",
            equation="V_C(t) = V_final + (V_initial - V_final)*exp(-t/tau)",
            explanation="The curve starts from the initial capacitor voltage and approaches the final DC value.",
            focus=_focus_by_step(steps, "rc_exponential_motion") or (steps[0].focus if steps else TutorFocus()),
            value_refs=refs if response else [],
        ),
    ]


def _build_value_refs(packet: SolutionPacket, steps: list[TutorStep]) -> list[LessonValueRef]:
    refs: dict[str, LessonValueRef] = {}
    for node, value in packet.node_voltages.items():
        _add_ref(
            refs,
            LessonValueRef(
                id=f"node_voltage_{node}",
                label=f"Node {node} voltage",
                formatted_value=format_value(value, "V"),
                source="solution_packet",
                note="Verified node voltage.",
            ),
        )
    for answer_id, answer in packet.requested_answers.items():
        _add_ref(
            refs,
            LessonValueRef(
                id=answer_id,
                label=answer_id.replace("_", " "),
                formatted_value=format_quantity(answer),
                source="solution_packet",
                note="Requested answer from the verified packet.",
            ),
        )
    for answer_id, answer in packet.ac_requested_answers.items():
        _add_ref(
            refs,
            LessonValueRef(
                id=f"{answer_id}_magnitude",
                label=f"{answer_id.replace('_', ' ')} magnitude",
                formatted_value=format_value(answer.magnitude, answer.unit),
                source="solution_packet",
                note="Requested AC magnitude from the verified packet.",
            ),
        )
        _add_ref(
            refs,
            LessonValueRef(
                id=f"{answer_id}_phase",
                label=f"{answer_id.replace('_', ' ')} phase",
                formatted_value=format_value(answer.phase_deg, "deg"),
                source="solution_packet",
                note="Requested AC phase from the verified packet.",
            ),
        )
        _add_ref(
            refs,
            LessonValueRef(
                id=answer_id,
                label=answer_id.replace("_", " "),
                formatted_value=format_complex_quantity(answer),
                source="solution_packet",
                note="Requested complex phasor from the verified packet.",
            ),
        )
    if packet.transient_response is not None:
        response = packet.transient_response
        for ref_id, label, value, unit in [
            ("initial_capacitor_voltage", "Initial capacitor voltage", response.initial_voltage_v, "V"),
            ("final_capacitor_voltage", "Final capacitor voltage", response.final_voltage_v, "V"),
            ("thevenin_resistance", "Resistance seen by capacitor", response.resistance_ohm, "ohm"),
            ("time_constant", "Time constant", response.time_constant_s, "s"),
        ]:
            _add_ref(
                refs,
                LessonValueRef(
                    id=ref_id,
                    label=label,
                    formatted_value=format_value(value, unit),
                    source="solution_packet",
                ),
            )
    for observation in [*packet.tutor_observations, *(value for step in steps for value in step.verified_values)]:
        formatted = format_observation(observation)
        _add_ref(
            refs,
            LessonValueRef(
                id=observation.id,
                label=observation.label,
                formatted_value=formatted,
                source="tutor_observation",
                note=observation.note or None,
            ),
        )
    for ref_id, label, value, unit in [
        ("max_kcl_residual", "Max KCL residual", packet.verification.max_kcl_residual_a, "A"),
        ("power_balance_error", "Power-balance error", packet.verification.power_balance_error_w, "W"),
    ]:
        _add_ref(
            refs,
            LessonValueRef(
                id=ref_id,
                label=label,
                formatted_value=format_value(value, unit),
                source="solution_packet",
            ),
        )
    return list(refs.values())


def _add_ref(refs: dict[str, LessonValueRef], value_ref: LessonValueRef) -> None:
    if value_ref.id not in refs or refs[value_ref.id].formatted_value is None:
        refs[value_ref.id] = value_ref


def _checks(packet: SolutionPacket) -> list[LessonCheck]:
    checks = [
        LessonCheck(
            id="verification_badge",
            label=f"Verification badge: {packet.verification_badge.label}",
            passed=packet.verification_badge.label == "PASS",
            explanation=packet.verification_badge.message,
        )
    ]
    checks.extend(
        LessonCheck(
            id=check.name,
            label=check.name,
            passed=check.passed,
            explanation=check.message,
        )
        for check in packet.verification.checks
    )
    return checks


def _visual_cues(steps: list[TutorStep]) -> list[str]:
    cues: list[str] = []
    for step in steps:
        focus = step.focus
        parts = []
        if focus.components:
            parts.append("components " + ", ".join(focus.components))
        if focus.nodes:
            parts.append("nodes " + ", ".join(focus.nodes))
        if focus.goals:
            parts.append("goals " + ", ".join(focus.goals))
        if parts:
            cues.append(f"{step.title}: focus " + "; ".join(parts) + ".")
    return cues


def _common_mistakes(steps: list[TutorStep]) -> list[str]:
    mistakes = []
    for step in steps:
        if step.common_mistake and step.common_mistake not in mistakes:
            mistakes.append(step.common_mistake)
    return mistakes


def _practice_prompts(circuit: CircuitProblem) -> list[str]:
    prompts = [
        "Change one component value and predict whether the requested answer should increase or decrease before re-solving.",
        "Select a different goal and explain the reference direction before looking at the number.",
    ]
    if circuit.topology_id == "voltage_divider":
        prompts.insert(0, "Swap the upper and lower resistor values and predict the output-node movement.")
    elif circuit.topology_id == "current_divider":
        prompts.insert(0, "Make one branch resistance smaller and predict which branch current grows.")
    elif "bridge" in (circuit.topology_id or circuit.id):
        prompts.insert(0, "Set the bridge resistor aside conceptually and predict how coupling changes the midpoint voltages.")
    elif circuit.analysis_type in {"ac_steady_state", "ac_single_frequency", "ac_sweep"}:
        prompts.insert(0, "Move the frequency below and above the corner and predict magnitude and phase trends.")
    elif circuit.analysis_type == "rc_transient":
        prompts.insert(0, "Ask what the capacitor voltage should be near one time constant and near final settling.")
    return prompts


def _limitations(circuit: CircuitProblem, packet: SolutionPacket) -> list[str]:
    limitations = [
        "The LLM is not used as the source of numerical truth.",
        "Unsupported or ambiguous features must be clarified instead of guessed.",
    ]
    if packet.ac_requested_answers or packet.ac_sweep:
        limitations.append("AC complex power is not verified in this MVP.")
    if circuit.analysis_type == "rc_transient":
        limitations.append("Only the implemented first-order RC transient template is covered.")
    if circuit.bme_metadata is not None:
        limitations.append("Biomedical notes are educational context, not patient-safety certification or device compliance.")
    return limitations


def _focus_by_step(steps: list[TutorStep], step_id: str) -> TutorFocus | None:
    return next((step.focus for step in steps if step.id == step_id), None)
