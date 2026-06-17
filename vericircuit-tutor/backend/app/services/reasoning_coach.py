from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import CircuitProblem
from app.models.coaching import (
    AdaptivePracticePrompt,
    CoachLocalCheck,
    CoachMetrics,
    CoachNudge,
    InstructorDashboardRequest,
    InstructorDashboardResponse,
    MisconceptionCohortSummary,
    ReasoningCoachRequest,
    ReasoningCoachResponse,
    ReflectionJournalEntry,
    RepresentationMode,
    StudentCommitment,
    StudentFrame,
    StudentProfile,
)
from app.models.solution_packet import SolutionPacket
from app.services.explainer import explain_solution
from app.services.gemini_client import GeminiClientUnavailable, GeminiStructuredClient
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


MISCONCEPTION_LABELS = {
    "common_mode_as_differential": "common-mode vs differential input",
    "inappropriate_divider_shortcut": "using a divider shortcut on a coupled network",
    "sign_convention": "current direction and sign convention",
    "capacitor_dc_behavior": "capacitor behavior in DC",
    "ideal_op_amp_input_current": "ideal op-amp input-current assumption",
    "unit_prefix": "unit prefix conversion",
    "aliasing_nyquist_misread": "anti-aliasing and Nyquist reasoning",
}

MISCONCEPTION_INTERVENTIONS = {
    "common_mode_as_differential": "Run a short differential-versus-common-mode warmup before ECG gain problems.",
    "inappropriate_divider_shortcut": "Use coupled-node bridge examples and ask students to mark every extra branch before shortcuts.",
    "sign_convention": "Require a passive sign convention and current arrows before KCL substitution.",
    "capacitor_dc_behavior": "Start DC/AC/transient problems by classifying each capacitor model.",
    "ideal_op_amp_input_current": "Review ideal op-amp assumptions separately from real loading limits.",
    "unit_prefix": "Add a base-SI rewrite checkpoint before every numeric substitution.",
    "aliasing_nyquist_misread": "Compare sampling frequency, Nyquist frequency, and cutoff on one annotated axis.",
}


class GeminiStudentFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suspected_method: str | None = None
    confusion: str | None = None
    likely_misconceptions: list[
        Literal[
            "common_mode_as_differential",
            "inappropriate_divider_shortcut",
            "sign_convention",
            "capacitor_dc_behavior",
            "ideal_op_amp_input_current",
            "unit_prefix",
            "aliasing_nyquist_misread",
        ]
    ] = Field(default_factory=list)
    confidence: Literal["unknown", "low", "medium", "high"] = "unknown"
    evidence: list[str] = Field(default_factory=list)


def coach_student_attempt(request: ReasoningCoachRequest) -> ReasoningCoachResponse:
    parsed = parse_problem(request.problem_text, request.mode)
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)
    warnings = [*parsed.warnings, *packet.warnings]

    profile = (
        request.student_profile.model_copy(deep=True)
        if request.student_profile is not None
        else StudentProfile()
    )
    frame, frame_warnings = _extract_student_frame_for_request(
        request,
        parsed.circuit,
        packet,
    )
    warnings.extend(frame_warnings)
    has_commitment = _has_commitment(request.student_commitment)
    focus_issue = _select_focus_issue(
        request.student_commitment,
        frame,
        parsed.circuit,
        packet,
        profile,
        has_commitment,
    )
    hint_level = _effective_hint_level(request, has_commitment)
    answer_revealed = (
        hint_level == 5
        and has_commitment
        and packet.status == "solved"
        and packet.verification_badge.label == "PASS"
    )
    local_check = _build_local_check(
        focus_issue,
        parsed.circuit,
        packet,
        answer_revealed,
    )
    nudge = _build_nudge(
        focus_issue,
        hint_level,
        parsed.circuit,
        packet,
        answer_revealed,
        _select_representation_mode(request, profile, parsed.circuit),
    )
    profile_update = _update_profile(
        profile,
        frame,
        parsed.circuit,
        hint_level,
        answer_revealed,
    )
    metrics = CoachMetrics(
        hint_budget_used=profile_update.hint_budget_used,
        independence_score=profile_update.independence_level,
        confidence_calibration=_confidence_calibration(frame, focus_issue),
    )
    reflection = _build_reflection(
        frame,
        focus_issue,
        hint_level,
        answer_revealed,
        profile_update,
        has_commitment,
    )

    return ReasoningCoachResponse(
        circuit_id=parsed.circuit.id,
        parser_used=parsed.parser_used,
        warnings=warnings,
        verification_badge=packet.verification_badge,
        student_frame=frame,
        local_check=local_check,
        nudge=nudge,
        profile_update=profile_update,
        metrics=metrics,
        reflection=reflection,
        adaptive_practice=_build_adaptive_practice(
            focus_issue,
            parsed.circuit,
            _select_representation_mode(request, profile, parsed.circuit),
        ),
        guardrails=[
            "Solver and verifier are the source of truth for numerical answers.",
            "Final numerical answers are withheld until hint level 5 after a student commitment.",
            "The coach returns one local blocker or next move instead of correcting every issue at once.",
        ],
        solution_packet=packet if answer_revealed else None,
        explanation=explain_solution(packet) if answer_revealed else None,
    )


def build_instructor_dashboard(
    request: InstructorDashboardRequest,
) -> InstructorDashboardResponse:
    profiles = request.student_profiles
    student_count = len(profiles)
    independence = {"high": 0, "medium": 0, "low": 0}
    affected_by_issue: dict[str, int] = {}
    occurrences_by_issue: dict[str, int] = {}

    for profile in profiles:
        independence[profile.independence_level] += 1
        for issue, count in profile.recurring_misconceptions.items():
            if count <= 0:
                continue
            affected_by_issue[issue] = affected_by_issue.get(issue, 0) + 1
            occurrences_by_issue[issue] = occurrences_by_issue.get(issue, 0) + int(count)

    summaries = [
        MisconceptionCohortSummary(
            misconception=issue,
            label=MISCONCEPTION_LABELS.get(issue, issue.replace("_", " ")),
            affected_students=affected_by_issue[issue],
            total_occurrences=occurrences_by_issue[issue],
            affected_percent=(
                affected_by_issue[issue] / student_count * 100.0
                if student_count
                else 0.0
            ),
            suggested_intervention=MISCONCEPTION_INTERVENTIONS.get(
                issue,
                "Review the underlying concept with one small verified example.",
            ),
        )
        for issue in sorted(
            affected_by_issue,
            key=lambda item: (-affected_by_issue[item], -occurrences_by_issue[item], item),
        )
    ]

    return InstructorDashboardResponse(
        student_count=student_count,
        cohort_independence=independence,
        misconception_summary=summaries,
        guardrails=[
            "Dashboard percentages summarize submitted StudentProfile objects only.",
            "The dashboard identifies learning patterns; it does not grade clinical or device safety competence.",
        ],
    )


def _has_commitment(commitment: StudentCommitment) -> bool:
    return bool(_commitment_text(commitment).strip())


def _commitment_text(commitment: StudentCommitment) -> str:
    parts = [
        commitment.attempt_text,
        commitment.plan or "",
        " ".join(commitment.knowns),
        commitment.unknown or "",
        commitment.first_equation or "",
        commitment.expected_answer or "",
        " ".join(commitment.assumptions),
    ]
    return " ".join(part for part in parts if part).strip()


def _extract_student_frame_for_request(
    request: ReasoningCoachRequest,
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> tuple[StudentFrame, list[str]]:
    heuristic = _extract_student_frame(request.student_commitment, circuit, packet)
    if request.mode not in {"gemini", "gemini_strict"} or not _has_commitment(request.student_commitment):
        return heuristic, []

    try:
        gemini_frame = _extract_student_frame_with_gemini(
            request.student_commitment,
            circuit,
        )
    except GeminiClientUnavailable as exc:
        fallback = heuristic.model_copy(update={"source": "gemini_fallback"})
        return fallback, [f"Gemini student-frame extraction unavailable: {exc}"]
    except ValueError as exc:
        fallback = heuristic.model_copy(update={"source": "gemini_fallback"})
        return fallback, [f"Gemini student-frame extraction returned invalid JSON: {exc}"]

    return _merge_student_frames(heuristic, gemini_frame), []


def _extract_student_frame_with_gemini(
    commitment: StudentCommitment,
    circuit: CircuitProblem,
) -> StudentFrame:
    response_text = GeminiStructuredClient().generate_json_text(
        prompt=_student_frame_prompt(commitment, circuit),
        schema_model=GeminiStudentFrame,
    )
    parsed = GeminiStudentFrame.model_validate_json(response_text)
    return StudentFrame(
        suspected_method=parsed.suspected_method,
        confusion=parsed.confusion,
        likely_misconceptions=list(parsed.likely_misconceptions),
        confidence=parsed.confidence,
        evidence=[*parsed.evidence, "gemini_student_frame"],
        source="gemini",
    )


def _student_frame_prompt(
    commitment: StudentCommitment,
    circuit: CircuitProblem,
) -> str:
    return f"""
Read the student's partial reasoning for a verified circuit tutor.

Return only JSON matching the provided schema.

Rules:
- Do not solve the circuit.
- Do not compute voltages, currents, powers, phasors, units, or final answers.
- Do not reveal a solution path.
- Only classify the student's current thinking, confusion, and likely misconception.
- Prefer one or two local misconception tags. Do not list every possible issue.
- Use likely_misconceptions only from the schema enum.
- If the student appears broadly correct, leave likely_misconceptions empty.

Circuit context:
- id: {circuit.id}
- title: {circuit.title}
- analysis_type: {circuit.analysis_type}
- topology_id: {circuit.topology_id}
- has_bme_metadata: {circuit.bme_metadata is not None}
- component_types: {sorted({component.type for component in circuit.components})}
- goal_quantities: {[goal.quantity for goal in circuit.goals]}

Student commitment:
{commitment.model_dump_json()}
""".strip()


def _merge_student_frames(
    heuristic: StudentFrame,
    gemini_frame: StudentFrame,
) -> StudentFrame:
    return StudentFrame(
        suspected_method=gemini_frame.suspected_method or heuristic.suspected_method,
        confusion=gemini_frame.confusion or heuristic.confusion,
        likely_misconceptions=_unique(
            [
                *gemini_frame.likely_misconceptions,
                *heuristic.likely_misconceptions,
            ]
        ),
        confidence=(
            gemini_frame.confidence
            if gemini_frame.confidence != "unknown"
            else heuristic.confidence
        ),
        evidence=_unique([*gemini_frame.evidence, *heuristic.evidence]),
        source="gemini",
    )


def _extract_student_frame(
    commitment: StudentCommitment,
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> StudentFrame:
    text = _commitment_text(commitment)
    normalized = text.lower()
    evidence: list[str] = []
    misconceptions: list[str] = []

    suspected_method = _suspected_method(normalized)
    if suspected_method:
        evidence.append(f"method:{suspected_method}")

    confusion = None
    if _contains_any(normalized, ["confused", "not sure", "unsure", "stuck", "?", "i think"]):
        confusion = _short_confusion_label(normalized)
        evidence.append("student_signaled_uncertainty")

    if _is_differential_bme(circuit, packet) and _looks_like_common_mode_gain_error(normalized):
        misconceptions.append("common_mode_as_differential")
        evidence.append("common_mode_gain_language")

    if _is_bridge_like(circuit) and "divider" in normalized:
        misconceptions.append("inappropriate_divider_shortcut")
        evidence.append("divider_shortcut_on_coupled_network")

    if (
        circuit.analysis_type == "dc_operating_point"
        and any(component.type == "capacitor" for component in circuit.components)
        and "capacitor" in normalized
        and _contains_any(normalized, ["short", "conduct", "current through", "passes dc"])
    ):
        misconceptions.append("capacitor_dc_behavior")
        evidence.append("dc_capacitor_current_language")

    if _has_ideal_op_amp(circuit) and "op amp" in normalized and _contains_any(
        normalized,
        ["input current", "loads", "loading", "draws current"],
    ):
        misconceptions.append("ideal_op_amp_input_current")
        evidence.append("ideal_op_amp_loading_language")

    if _contains_any(normalized, ["sign", "direction", "negative"]) and _contains_any(
        normalized,
        ["current", "kcl", "source"],
    ):
        misconceptions.append("sign_convention")
        evidence.append("sign_or_direction_language")

    if _contains_any(normalized, [" mv", "millivolt", " micro", " uf", "kohm", "k ohm"]):
        misconceptions.append("unit_prefix")
        evidence.append("unit_prefix_language")

    if (
        circuit.bme_metadata is not None
        and circuit.bme_metadata.adc_sampling_frequency_hz is not None
        and _contains_any(normalized, ["nyquist", "alias"])
        and _contains_any(normalized, ["above", "higher", "greater"])
    ):
        misconceptions.append("aliasing_nyquist_misread")
        evidence.append("nyquist_cutoff_language")

    return StudentFrame(
        suspected_method=suspected_method,
        confusion=confusion,
        likely_misconceptions=_unique(misconceptions),
        confidence=_confidence(commitment, normalized),
        evidence=_unique(evidence),
    )


def _suspected_method(normalized_text: str) -> str | None:
    if _contains_any(normalized_text, ["phasor", "impedance", "frequency", "jw", "omega"]):
        return "ac_phasor"
    if _contains_any(normalized_text, ["transient", "time constant", "tau", "exponential"]):
        return "rc_transient"
    if "divider" in normalized_text:
        return "voltage_divider"
    if _contains_any(normalized_text, ["kcl", "nodal", "node voltage"]):
        return "nodal_analysis"
    if _contains_any(normalized_text, ["gain", "op amp", "amplifier"]):
        return "op_amp_gain"
    if _contains_any(normalized_text, ["unit", "milli", "micro", "kilo"]):
        return "unit_check"
    return None


def _confidence(commitment: StudentCommitment, normalized_text: str) -> str:
    if commitment.confidence_percent is not None:
        if commitment.confidence_percent < 40:
            return "low"
        if commitment.confidence_percent > 75:
            return "high"
        return "medium"
    if _contains_any(normalized_text, ["confused", "not sure", "unsure", "guess", "stuck"]):
        return "low"
    if _contains_any(normalized_text, ["confident", "sure", "definitely"]):
        return "high"
    return "unknown"


def _short_confusion_label(normalized_text: str) -> str:
    if "op amp" in normalized_text:
        return "op amp role"
    if "sign" in normalized_text or "direction" in normalized_text:
        return "sign convention"
    if "unit" in normalized_text or "mv" in normalized_text:
        return "unit conversion"
    if "common" in normalized_text:
        return "common-mode handling"
    return "next method choice"


def _select_focus_issue(
    commitment: StudentCommitment,
    frame: StudentFrame,
    circuit: CircuitProblem,
    packet: SolutionPacket,
    profile: StudentProfile,
    has_commitment: bool,
) -> str:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return "problem_not_verified"
    if not has_commitment:
        return "no_commitment"

    priority = [
        "common_mode_as_differential",
        "inappropriate_divider_shortcut",
        "capacitor_dc_behavior",
        "ideal_op_amp_input_current",
        "sign_convention",
        "unit_prefix",
        "aliasing_nyquist_misread",
    ]
    for issue in priority:
        if issue in frame.likely_misconceptions:
            return issue

    recurrent_issue = _recurrent_issue(commitment, circuit, packet, profile)
    if recurrent_issue:
        return recurrent_issue

    return "generic_next_step"


def _recurrent_issue(
    commitment: StudentCommitment,
    circuit: CircuitProblem,
    packet: SolutionPacket,
    profile: StudentProfile,
) -> str | None:
    text = _commitment_text(commitment).lower()
    recurring = profile.recurring_misconceptions
    if recurring.get("sign_convention", 0) >= 2 and (
        _contains_any(text, ["current", "kcl", "source"])
        or any(goal.quantity in {"component_current", "component_power", "source_power"} for goal in circuit.goals)
    ):
        return "sign_convention"
    if recurring.get("unit_prefix", 0) >= 2 and (
        commitment.expected_answer or _contains_any(text, ["unit", "mv", "uf", "kohm"])
    ):
        return "unit_prefix"
    if (
        recurring.get("common_mode_as_differential", 0) >= 2
        and _is_differential_bme(circuit, packet)
    ):
        return "common_mode_as_differential"
    if (
        recurring.get("capacitor_dc_behavior", 0) >= 2
        and circuit.analysis_type == "dc_operating_point"
        and any(component.type == "capacitor" for component in circuit.components)
    ):
        return "capacitor_dc_behavior"
    return None


def _effective_hint_level(request: ReasoningCoachRequest, has_commitment: bool) -> int:
    if not has_commitment:
        return 0
    if request.reveal_solution or request.requested_hint_level >= 5:
        return 5
    requested = min(max(request.requested_hint_level, 0), 4)
    profile = request.student_profile
    if profile is not None and profile.independence_level == "low" and requested > 1:
        return 1
    if profile is not None and profile.hint_budget_used >= 6 and requested > 2:
        return 2
    return requested


def _select_representation_mode(
    request: ReasoningCoachRequest,
    profile: StudentProfile,
    circuit: CircuitProblem,
) -> RepresentationMode:
    if request.representation_mode != "physical_intuition":
        return request.representation_mode
    preference = profile.hint_preference.lower()
    if "diagram" in preference:
        return "diagram"
    if "equation" in preference or "kcl" in preference:
        return "kcl_equation"
    if "unit" in preference or "magnitude" in preference:
        return "units_magnitude"
    if "biomedical" in preference or (circuit.bme_metadata is not None and "context" in preference):
        return "biomedical_context"
    return "biomedical_context" if circuit.bme_metadata is not None else "physical_intuition"


def _build_local_check(
    focus_issue: str,
    circuit: CircuitProblem,
    packet: SolutionPacket,
    answer_revealed: bool,
) -> CoachLocalCheck:
    if focus_issue == "problem_not_verified":
        return CoachLocalCheck(
            status="blocked",
            focus_issue=focus_issue,
            verified_context="The parser, solver, or verifier did not produce a PASS packet, so CiTT cannot coach from hidden truth yet.",
            blocks_next_step=True,
        )
    if focus_issue == "no_commitment":
        return CoachLocalCheck(
            status="needs_commit",
            focus_issue=focus_issue,
            verified_context="An internal verified packet exists, but the student has not committed a frame to check.",
            blocks_next_step=True,
        )
    if answer_revealed:
        return CoachLocalCheck(
            status="ready_for_reveal",
            focus_issue=focus_issue,
            verified_context="The hidden solver/verifier packet passed and the student has used the reveal-level hint.",
            blocks_next_step=False,
        )
    if focus_issue == "generic_next_step":
        return CoachLocalCheck(
            status="ready_for_next",
            focus_issue=focus_issue,
            verified_context="The current frame is plausible against the hidden verified packet; final values remain hidden.",
            blocks_next_step=False,
        )
    return CoachLocalCheck(
        status="productive",
        focus_issue=focus_issue,
        verified_context=f"The hidden verified packet suggests a local issue: {MISCONCEPTION_LABELS[focus_issue]}.",
        blocks_next_step=True,
    )


def _build_nudge(
    focus_issue: str,
    hint_level: int,
    circuit: CircuitProblem,
    packet: SolutionPacket,
    answer_revealed: bool,
    representation_mode: RepresentationMode,
) -> CoachNudge:
    if focus_issue == "problem_not_verified":
        return CoachNudge(
            hint_level=0,
            representation_mode=representation_mode,
            message="Clarify the circuit statement before solving. CiTT cannot safely coach from an unverified internal packet.",
            question="What component, node, source direction, or requested quantity should be made explicit first?",
            representation_prompt=_representation_prompt(
                "problem_not_verified",
                representation_mode,
                circuit,
            ),
            choices=["Clarify connectivity", "Clarify source direction", "Clarify requested quantity"],
        )
    if focus_issue == "no_commitment":
        return CoachNudge(
            hint_level=0,
            representation_mode=representation_mode,
            message="Commit one starting frame before seeing the solution path.",
            question="What do you think the first unknown is?",
            representation_prompt=_representation_prompt(
                "no_commitment",
                representation_mode,
                circuit,
            ),
            choices=["Name the unknown", "State a method", "State an assumption"],
        )
    if answer_revealed:
        return CoachNudge(
            hint_level=5,
            representation_mode=representation_mode,
            message="Full verified reveal is enabled for this turn.",
            question="Compare your original frame with the verified packet: which assumption changed?",
            representation_prompt=_representation_prompt(
                focus_issue,
                representation_mode,
                circuit,
            ),
            choices=["Check sign convention", "Check unit scale", "Write a reflection"],
            answer_revealed=True,
        )

    message, question = _issue_prompt(focus_issue, hint_level, circuit, packet)
    return CoachNudge(
        hint_level=hint_level,  # type: ignore[arg-type]
        representation_mode=representation_mode,
        message=message,
        question=question,
        representation_prompt=_representation_prompt(
            focus_issue,
            representation_mode,
            circuit,
        ),
        choices=_choices_for(circuit, focus_issue),
        answer_revealed=False,
    )


def _issue_prompt(
    focus_issue: str,
    hint_level: int,
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> tuple[str, str]:
    if focus_issue == "common_mode_as_differential":
        prompts = {
            0: (
                "Separate the two input ideas before calculating.",
                "Which signal is differential, and which signal is common to both inputs?",
            ),
            1: (
                "You are thinking about gain, which is useful. Pause and separate differential input from common-mode input.",
                "Which one does the ideal instrumentation amplifier amplify?",
            ),
            2: (
                "Choose the method that keeps the two input modes apart before any gain calculation.",
                "Would you start with differential/common-mode decomposition, resistor-ratio gain, or output swing?",
            ),
            3: (
                "Write the input decomposition symbolically first: Vdiff uses the input difference, and Vcm uses their average.",
                "After that split, where should ideal differential gain be applied?",
            ),
            4: (
                "Your checkpoint is conceptual: ideal gain belongs to the differential signal, while common-mode belongs in a rejection or nonideality check.",
                "Which term should be withheld from the ideal output equation?",
            ),
        }
        return prompts[hint_level]

    if focus_issue == "inappropriate_divider_shortcut":
        prompts = {
            0: (
                "Before choosing a shortcut, name what connects the interior nodes.",
                "Is the target node isolated enough for a simple divider?",
            ),
            1: (
                "A divider instinct is useful, but this network has a coupling path that can move the node voltages together.",
                "Which node would make KCL easiest to write first?",
            ),
            2: (
                "Choose between a local divider shortcut and nodal analysis by checking whether the target node has a coupling branch.",
                "Which branch prevents the simple divider from being independent?",
            ),
            3: (
                "Use one KCL equation at an interior node and include every connected resistor current with one sign convention.",
                "Will you count currents leaving the node or entering it?",
            ),
            4: (
                "Numerical work should wait until the coupled-node KCL structure is written.",
                "Which extra branch current would be missing from the shortcut?",
            ),
        }
        return prompts[hint_level]

    if focus_issue == "sign_convention":
        prompts = {
            0: (
                "Pause on direction before doing algebra.",
                "What current direction are you choosing as positive?",
            ),
            1: (
                "The sign can be allowed to come out negative, but only after you declare a positive direction.",
                "What direction will your KCL currents use?",
            ),
            2: (
                "Pick a convention now: all currents leaving the node, or all currents entering the node.",
                "Which convention will make your next equation easier to audit?",
            ),
            3: (
                "Try writing KCL with all currents leaving the node, using the same node-voltage difference pattern for each branch.",
                "Which branch current term are you least sure about?",
            ),
            4: (
                "Your checkpoint is not the final number; it is whether every current term follows the direction you declared.",
                "Which sign would flip if the actual current goes opposite your chosen arrow?",
            ),
        }
        return prompts[hint_level]

    if focus_issue == "capacitor_dc_behavior":
        prompts = {
            0: (
                "Classify the analysis mode before deciding what the capacitor does.",
                "Is this DC, AC, or transient?",
            ),
            1: (
                "For a DC operating point after settling, an ideal capacitor does not carry steady current.",
                "What branch disappears from the DC KCL picture?",
            ),
            2: (
                "Choose whether this is a DC open-circuit simplification, an AC impedance problem, or a transient initial/final-value problem.",
                "Which model matches the requested analysis?",
            ),
            3: (
                "Rewrite the KCL without steady capacitor current if the request is DC operating point.",
                "Which remaining resistive or source branch sets the node?",
            ),
            4: (
                "Your checkpoint is whether you used the capacitor model that matches the analysis type.",
                "What would change if the problem were transient instead?",
            ),
        }
        return prompts[hint_level]

    if focus_issue == "ideal_op_amp_input_current":
        prompts = {
            0: (
                "State the ideal op-amp assumption before treating it as a load.",
                "What is the ideal input current?",
            ),
            1: (
                "The op-amp can constrain voltages without drawing input current in the ideal model.",
                "Which node equation should not include op-amp input current?",
            ),
            2: (
                "Choose whether the op-amp affects this step through input current, feedback voltage constraint, or output swing context.",
                "Which effect belongs to the ideal solver?",
            ),
            3: (
                "Write the KCL at the input node using external components, then add the ideal voltage constraint separately.",
                "Which current path enters the op-amp input in the ideal model?",
            ),
            4: (
                "Your checkpoint is whether loading was added by assumption rather than by a component in the Circuit IR.",
                "What assumption lets that current term vanish?",
            ),
        }
        return prompts[hint_level]

    if focus_issue == "unit_prefix":
        prompts = {
            0: (
                "Estimate the unit before calculating.",
                "Should the answer scale as volts, amps, ohms, or a time/frequency unit?",
            ),
            1: (
                "Your structure may be fine, but unit prefixes can move the answer by large factors.",
                "Which prefix conversion should be written in SI units first?",
            ),
            2: (
                "Choose a unit checkpoint before algebra: source units, component units, or requested-answer units.",
                "Which one is most likely to change the magnitude?",
            ),
            3: (
                "Rewrite the known values in base SI units before substituting them into the equation.",
                "Which value changes when you convert the prefix?",
            ),
            4: (
                "Your checkpoint is magnitude sanity, not the final answer: a prefix mistake usually shifts powers of ten.",
                "Does your expected magnitude match the physical scale of the circuit?",
            ),
        }
        return prompts[hint_level]

    if focus_issue == "aliasing_nyquist_misread":
        prompts = {
            0: (
                "Separate sampling frequency, Nyquist frequency, and filter cutoff before calculating.",
                "Which one is half the sampling frequency?",
            ),
            1: (
                "Anti-aliasing reasoning starts by comparing cutoff with Nyquist, not by placing cutoff above it by default.",
                "What should the filter do to content near Nyquist?",
            ),
            2: (
                "Choose the next concept: cutoff placement, attenuation at Nyquist, or sampling-rate constraint.",
                "Which check would show whether high-frequency content is reduced before the ADC?",
            ),
            3: (
                "Write the relationship between sampling frequency and Nyquist first, then compare the filter corner to that marker.",
                "Which frequency should be treated as the aliasing boundary?",
            ),
            4: (
                "Your checkpoint is qualitative attenuation at the Nyquist marker, not a claim of alias-free sampling.",
                "What additional information would be needed to prove alias energy is acceptable?",
            ),
        }
        return prompts[hint_level]

    return _generic_prompt(hint_level, circuit, packet)


def _generic_prompt(
    hint_level: int,
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> tuple[str, str]:
    first_step = packet.guided_steps[0] if packet.guided_steps else None
    step_title = first_step.title if first_step else "the reference node and requested quantity"
    next_action = first_step.next_action if first_step and first_step.next_action else "choose the next analysis move"
    prompts = {
        0: (
            "Reflect before calculating.",
            "What quantity do you need before the requested answer can be found?",
        ),
        1: (
            f"Your current frame is plausible. Focus locally on {step_title.lower()}.",
            "What would you check there before moving to algebra?",
        ),
        2: (
            "Choose the next method move rather than reading the final answer.",
            "Would you define node voltages, choose a sign convention, or simplify the source first?",
        ),
        3: (
            "Build the equation scaffold for the next local step and leave the numbers hidden.",
            "What equation structure follows from the reference and sign convention you chose?",
        ),
        4: (
            f"Use this as a checkpoint before reveal: {next_action}",
            "What unit, sign, or physical magnitude should your next answer have?",
        ),
    }
    return prompts[hint_level]


def _choices_for(circuit: CircuitProblem, focus_issue: str) -> list[str]:
    if focus_issue == "common_mode_as_differential":
        return ["Separate input modes", "State ideal assumption", "Check output reference"]
    if focus_issue == "inappropriate_divider_shortcut":
        return ["Define node voltages", "Write KCL", "Identify the coupling branch"]
    if focus_issue == "sign_convention":
        return ["Currents leaving", "Currents entering", "Draw current arrows"]
    if focus_issue == "capacitor_dc_behavior":
        return ["Use DC open model", "Use AC impedance", "Use transient model"]
    if focus_issue == "ideal_op_amp_input_current":
        return ["Use input-current assumption", "Use feedback constraint", "Check output reference"]
    if focus_issue == "unit_prefix":
        return ["Convert to SI", "Estimate magnitude", "Check requested unit"]
    if focus_issue == "aliasing_nyquist_misread":
        return ["Find Nyquist", "Compare cutoff", "Ask for attenuation check"]
    if circuit.analysis_type in {"ac_steady_state", "ac_single_frequency", "ac_sweep"}:
        return ["Convert impedance", "Predict magnitude trend", "Predict phase trend"]
    if circuit.analysis_type == "rc_transient":
        return ["Find initial value", "Find final value", "Find time constant"]
    if _is_differential_circuit(circuit):
        return ["Separate input modes", "Trace feedback", "Check output polarity"]
    if circuit.topology_id == "voltage_divider":
        return ["Anchor source and ground", "Follow series current", "Read output polarity"]
    if circuit.topology_id == "current_divider":
        return ["Anchor source node", "Compare branches", "Choose current directions"]
    return ["Define node voltages", "Choose sign convention", "Write one KCL equation"]


def _representation_prompt(
    focus_issue: str,
    representation_mode: RepresentationMode,
    circuit: CircuitProblem,
) -> str:
    if representation_mode == "diagram":
        if focus_issue == "common_mode_as_differential":
            return "On the diagram, mark the two input source nodes as a pair before tracing the output node."
        if focus_issue == "inappropriate_divider_shortcut":
            return "Circle the target node and every branch connected to it; the extra coupling branch decides whether a divider shortcut is valid."
        if focus_issue == "sign_convention":
            return "Draw one current arrow per branch before writing symbols; keep the arrows even if a solved current becomes negative."
        if focus_issue == "capacitor_dc_behavior":
            return "Cross out the ideal capacitor branch only for DC steady state; leave it active for AC or transient reasoning."
        return "Point to the source, ground node, target node, and one branch that controls the next step."

    if representation_mode == "kcl_equation":
        if focus_issue == "common_mode_as_differential":
            return "Write Vdiff and Vcm as separate symbolic quantities before any gain expression."
        if focus_issue == "inappropriate_divider_shortcut":
            return "Write one KCL line with every current connected to the target node, including the coupling branch."
        if focus_issue == "sign_convention":
            return "Choose either sum I_leaving = 0 or sum I_entering = 0, then use that pattern for every branch."
        if focus_issue == "ideal_op_amp_input_current":
            return "Write KCL without an op-amp input-current term, then add the ideal voltage constraint separately."
        return "Write the next equation structure using symbols only; keep numerical substitution for later."

    if representation_mode == "units_magnitude":
        if focus_issue == "unit_prefix":
            return "Rewrite every value in base SI units, then estimate whether the result should be large or small before calculating."
        if focus_issue == "aliasing_nyquist_misread":
            return "Place sampling frequency, Nyquist frequency, and cutoff on one frequency axis before judging attenuation."
        return "State the expected unit and order of magnitude before substituting numbers."

    if representation_mode == "biomedical_context":
        if focus_issue == "common_mode_as_differential":
            return "Treat common-mode voltage as the large shared body/electrode level and differential voltage as the small desired biosignal."
        if focus_issue == "aliasing_nyquist_misread":
            return "Frame the RC stage as protecting the ADC from high-frequency content that could fold into the biomedical band."
        if circuit.bme_metadata is not None:
            return f"Connect the next circuit step to the signal-chain role: {circuit.bme_metadata.signal_chain_role}"
        return "Name the measurement context first, then decide which circuit abstraction supports that measurement."

    if focus_issue == "common_mode_as_differential":
        return "Use the physical story: shared motion or electrode offset is not the same as the tiny difference you want to amplify."
    if focus_issue == "inappropriate_divider_shortcut":
        return "Ask whether the target node can move independently; any extra branch lets another part of the circuit pull on it."
    if focus_issue == "sign_convention":
        return "A negative current is not failure; it means the real current chose the opposite direction from your arrow."
    if focus_issue == "capacitor_dc_behavior":
        return "At settled DC, an ideal capacitor has stopped moving charge; in AC or transient work, that story changes."
    return "Explain the next move in words before turning it into symbols."


def _build_adaptive_practice(
    focus_issue: str,
    circuit: CircuitProblem,
    representation_mode: RepresentationMode,
) -> list[AdaptivePracticePrompt]:
    if focus_issue not in MISCONCEPTION_LABELS:
        return []

    prompts = {
        "common_mode_as_differential": [
            (
                "diff_common_split_1",
                "An instrumentation amplifier sees +1.01 V and +0.99 V at its two inputs. Before calculating output, name Vdiff and Vcm.",
                "Practice separating the small differential signal from the shared common-mode level.",
            ),
            (
                "diff_common_split_2",
                "An ECG front-end has a large electrode offset shared by both inputs and a small heart-signal difference. Which part receives ideal differential gain?",
                "Practice deciding what ideal gain does and does not amplify.",
            ),
        ],
        "inappropriate_divider_shortcut": [
            (
                "coupled_node_shortcut_1",
                "A midpoint divider node also connects through a resistor to another unknown node. Decide whether a divider shortcut is enough.",
                "Practice spotting when an extra branch turns a shortcut into a nodal-analysis problem.",
            ),
            (
                "coupled_node_shortcut_2",
                "Mark every branch touching a bridge midpoint before choosing a method.",
                "Practice checking topology before applying a formula.",
            ),
        ],
        "sign_convention": [
            (
                "sign_convention_1",
                "Write KCL for one node twice: once with currents leaving positive and once with currents entering positive.",
                "Practice seeing that either convention works if used consistently.",
            ),
            (
                "sign_convention_2",
                "Draw an assumed current arrow through a resistor, then explain what a negative solved value would mean.",
                "Practice interpreting sign without erasing the chosen reference direction.",
            ),
        ],
        "capacitor_dc_behavior": [
            (
                "capacitor_mode_1",
                "Classify the same capacitor branch under DC steady state, AC phasor, and first-order transient analysis.",
                "Practice matching capacitor behavior to analysis type.",
            ),
            (
                "capacitor_mode_2",
                "For a settled DC circuit with a capacitor to ground, decide whether that branch appears in KCL.",
                "Practice removing only the steady-state capacitor current, not the node itself.",
            ),
        ],
        "ideal_op_amp_input_current": [
            (
                "op_amp_assumption_1",
                "At an ideal op-amp input node, list the external resistor currents and decide whether to include input current.",
                "Practice separating ideal input-current assumptions from feedback voltage constraints.",
            ),
            (
                "op_amp_assumption_2",
                "State what ideal op-amp rule constrains V+ and V- in a negative-feedback circuit.",
                "Practice using the ideal model without inventing a load current.",
            ),
        ],
        "unit_prefix": [
            (
                "unit_prefix_1",
                "Convert kOhm, mV, uF, and mA into base SI units before writing an equation.",
                "Practice preventing power-of-ten errors before substitution.",
            ),
            (
                "unit_prefix_2",
                "Estimate whether a divider output should be closer to millivolts, volts, or kilovolts before calculating.",
                "Practice magnitude sanity checks.",
            ),
        ],
        "aliasing_nyquist_misread": [
            (
                "nyquist_cutoff_1",
                "For an ADC sampling at 4000 Hz, mark Nyquist and decide whether a low-pass cutoff above it helps or hurts aliasing.",
                "Practice comparing cutoff with the aliasing boundary.",
            ),
            (
                "nyquist_cutoff_2",
                "Explain what a single-pole RC filter can claim at Nyquist and what it cannot prove about alias-free sampling.",
                "Practice keeping attenuation estimates separate from full alias-energy proof.",
            ),
        ],
    }
    return [
        AdaptivePracticePrompt(
            id=prompt_id,
            target_misconception=focus_issue,
            prompt=prompt,
            goal=goal,
            representation_mode=representation_mode,
        )
        for prompt_id, prompt, goal in prompts[focus_issue]
    ]


def _update_profile(
    profile: StudentProfile,
    frame: StudentFrame,
    circuit: CircuitProblem,
    hint_level: int,
    answer_revealed: bool,
) -> StudentProfile:
    updated = profile.model_copy(deep=True)
    for misconception in frame.likely_misconceptions:
        updated.recurring_misconceptions[misconception] = (
            updated.recurring_misconceptions.get(misconception, 0) + 1
        )

    for strength in _strengths_from_frame(frame, circuit):
        if strength not in updated.strengths:
            updated.strengths.append(strength)

    updated.hint_budget_used += hint_level
    if answer_revealed:
        updated.completed_attempts += 1
    updated.independence_level = _independence_score(updated.hint_budget_used, answer_revealed)
    return updated


def _strengths_from_frame(frame: StudentFrame, circuit: CircuitProblem) -> list[str]:
    strengths: list[str] = []
    if frame.suspected_method == "voltage_divider" and circuit.topology_id == "voltage_divider":
        strengths.append("recognizes voltage divider structure")
    if frame.suspected_method == "nodal_analysis" and _is_bridge_like(circuit):
        strengths.append("chooses nodal analysis for coupled networks")
    if frame.suspected_method == "ac_phasor" and circuit.analysis_type in {
        "ac_steady_state",
        "ac_single_frequency",
        "ac_sweep",
    }:
        strengths.append("recognizes frequency-domain analysis")
    if frame.suspected_method == "rc_transient" and circuit.analysis_type == "rc_transient":
        strengths.append("recognizes first-order transient structure")
    if "unit_prefix_language" in frame.evidence:
        strengths.append("notices unit scale needs checking")
    return strengths


def _independence_score(hint_budget_used: int, answer_revealed: bool) -> str:
    if answer_revealed or hint_budget_used >= 8:
        return "low"
    if hint_budget_used >= 3:
        return "medium"
    return "high"


def _confidence_calibration(frame: StudentFrame, focus_issue: str) -> str | None:
    if frame.confidence == "unknown":
        return None
    if frame.confidence == "high" and focus_issue not in {"generic_next_step", "no_commitment"}:
        return "High confidence with a local issue flagged; justify the assumption before calculating."
    if frame.confidence == "low" and focus_issue == "generic_next_step":
        return "Low confidence, but the chosen frame is plausible; name the evidence that supports it."
    if frame.confidence == "medium":
        return "Confidence logged; final calibration waits until a verified reveal."
    return "Confidence logged for reflection."


def _build_reflection(
    frame: StudentFrame,
    focus_issue: str,
    hint_level: int,
    answer_revealed: bool,
    profile: StudentProfile,
    has_commitment: bool,
) -> ReflectionJournalEntry:
    if not has_commitment:
        return ReflectionJournalEntry(
            summary="No student-owned reasoning has been committed yet.",
            today_i_learned=[
                "A useful tutor turn starts with my own unknown, method, or assumption."
            ],
            next_practice_focus=["Commit an unknown, method, or assumption before asking for the answer."],
        )
    if answer_revealed:
        return ReflectionJournalEntry(
            summary=(
                "You reached verified reveal after committing your own frame. "
                f"Hint budget used so far: {profile.hint_budget_used}."
            ),
            today_i_learned=_journal_lessons(frame, focus_issue, profile),
            corrected_misconceptions=[
                MISCONCEPTION_LABELS[item]
                for item in frame.likely_misconceptions
                if item in MISCONCEPTION_LABELS
            ],
            next_practice_focus=_practice_focus(focus_issue),
        )
    if focus_issue == "generic_next_step":
        return ReflectionJournalEntry(
            summary="Your current frame is ready for the next student-chosen move; final answers remain hidden.",
            today_i_learned=[
                "My current frame is plausible enough to choose the next reasoning move."
            ],
            next_practice_focus=["Choose the next method step and state why it follows."],
        )
    return ReflectionJournalEntry(
        summary=(
            "Your attempt surfaced one productive local issue. "
            f"CiTT gave a level {hint_level} nudge without revealing final values."
        ),
        today_i_learned=_journal_lessons(frame, focus_issue, profile),
        next_practice_focus=_practice_focus(focus_issue),
    )


def _journal_lessons(
    frame: StudentFrame,
    focus_issue: str,
    profile: StudentProfile,
) -> list[str]:
    lessons: list[str] = []
    if focus_issue == "common_mode_as_differential":
        lessons.extend(
            [
                "I should separate differential input from common-mode input before applying ideal gain.",
                "Common-mode reasoning belongs with rejection, mismatch, input range, and nonideal checks.",
            ]
        )
    elif focus_issue == "sign_convention":
        lessons.extend(
            [
                "I should declare current direction before writing KCL.",
                "A negative solved current means my chosen reference direction was opposite the actual current.",
            ]
        )
    elif focus_issue == "inappropriate_divider_shortcut":
        lessons.extend(
            [
                "I should inspect all branches touching a node before using a divider shortcut.",
                "A coupled bridge node usually needs KCL rather than an isolated divider formula.",
            ]
        )
    elif focus_issue == "capacitor_dc_behavior":
        lessons.append("I should classify capacitor behavior by analysis type: DC, AC, or transient.")
    elif focus_issue == "ideal_op_amp_input_current":
        lessons.append("In the ideal op-amp model, input current is not a loading branch in KCL.")
    elif focus_issue == "unit_prefix":
        lessons.append("I should convert prefixes to base SI units before substituting numbers.")
    elif focus_issue == "aliasing_nyquist_misread":
        lessons.append("I should compare cutoff with Nyquist before making anti-aliasing claims.")
    else:
        lessons.append("I should connect my next step to the requested quantity and reference direction.")

    if frame.confidence == "high" and focus_issue in MISCONCEPTION_LABELS:
        lessons.append("High confidence needs evidence; it is not a substitute for a reference or unit check.")
    if profile.independence_level == "low":
        lessons.append("I used substantial hint support, so the next practice should start with a smaller hint.")
    return lessons


def _practice_focus(focus_issue: str) -> list[str]:
    if focus_issue in MISCONCEPTION_LABELS:
        return [MISCONCEPTION_LABELS[focus_issue]]
    return ["reference node, sign convention, and requested quantity"]


def _is_bridge_like(circuit: CircuitProblem) -> bool:
    return "bridge" in (circuit.topology_id or circuit.id or "").lower()


def _is_differential_circuit(circuit: CircuitProblem) -> bool:
    marker = (circuit.topology_id or circuit.id or "").lower()
    return "ecg" in marker or "instrumentation" in marker or "differential" in marker


def _is_differential_bme(circuit: CircuitProblem, packet: SolutionPacket) -> bool:
    if not _is_differential_circuit(circuit):
        return False
    observation_ids = {observation.id for observation in packet.tutor_observations}
    return {"differential_input_voltage", "common_mode_input_voltage"} <= observation_ids


def _looks_like_common_mode_gain_error(normalized_text: str) -> bool:
    return (
        _contains_any(normalized_text, ["common-mode", "common mode", "commonmode", "cm"])
        and _contains_any(normalized_text, ["gain", "amplify", "multiply", "output"])
        and not _contains_any(normalized_text, ["reject", "cmrr", "separate", "difference"])
    )


def _has_ideal_op_amp(circuit: CircuitProblem) -> bool:
    return any(component.type in {"ideal_op_amp", "op_amp_ideal"} for component in circuit.components)


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
