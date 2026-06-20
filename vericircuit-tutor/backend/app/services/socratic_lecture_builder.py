from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import (
    SocraticLecturePacket,
    SocraticLecturePrompt,
    SocraticLectureStage,
    SocraticModeProfile,
    SolutionPacket,
    TutorFocus,
)


def build_socratic_lecture_packet(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> SocraticLecturePacket | None:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return None

    domain = _domain_label(circuit, packet)
    stages = _build_stages(circuit, packet)
    return SocraticLecturePacket(
        mode="worked_example",
        source_pattern=(
            "Medical instrumentation textbook pattern: context -> measurand -> "
            "instrument chain -> equivalent model -> prediction -> calculation -> "
            "verification/nonideality -> transfer."
        ),
        opening_contract=(
            "Do not start by revealing the answer. First require the student to name "
            f"what is being measured or delivered in this {domain} problem, choose a "
            "model, and make a qualitative prediction."
        ),
        textbook_pacing_summary=_textbook_pacing_summary(circuit, packet),
        mode_profiles=_mode_profiles(),
        stages=stages,
        gemini_prompt=_gemini_prompt(circuit, packet, stages),
        safety_notes=_safety_notes(circuit, packet),
    )


def _build_stages(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[SocraticLectureStage]:
    stages = [
        _orient_stage(circuit, packet),
        _representation_stage(circuit, packet),
        _model_stage(circuit, packet),
        _prediction_stage(circuit, packet),
        _commit_stage(circuit, packet),
        _compare_stage(circuit, packet),
    ]
    if _needs_nonideality_stage(circuit, packet):
        stages.append(_nonideality_stage(circuit, packet))
    stages.append(_transfer_stage(circuit, packet))
    return stages


def _orient_stage(circuit: CircuitProblem, packet: SolutionPacket) -> SocraticLectureStage:
    focus = _goal_focus(circuit)
    return SocraticLectureStage(
        id="orient_measurand",
        title="Orient to the measurand",
        goal="The student names the physical signal, requested quantity, and reference before any value is shown.",
        pace="observe",
        prompts=[
            SocraticLecturePrompt(
                id="name_target_and_reference",
                phase="orient",
                tutor_move="Ask what the problem is trying to measure, compute, or deliver.",
                student_task="Name the target quantity and its reference node, frequency, time origin, or patient/load path.",
                expected_student_evidence="A target such as node voltage, component current, transfer magnitude, time constant, sampling limit, noise term, or safety current path.",
                if_correct="Move to the representation stage and ask where that target lives in the circuit or signal chain.",
                if_stuck="Offer choices: node voltage, component current, transfer behavior, transient behavior, sensor output, noise/interference, or safety path.",
                unlocks=["schematic_focus", "problem_goal"],
                value_refs=_goal_value_refs(packet),
                focus=focus,
            )
        ],
        advance_when="Student can point to the requested quantity and reference.",
        common_failure="Student starts substituting numbers before naming what the number represents.",
        instructor_note="This mirrors the textbook's habit of naming the measurand before the model.",
    )


def _representation_stage(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> SocraticLectureStage:
    if circuit.bme_metadata is not None:
        title = "Trace the biomedical signal chain"
        goal = "The student identifies source, sensor/electrode, conditioning block, and the idealized block currently solved."
        tutor_move = "Ask the student to trace the signal from body/source to the solved circuit block."
        student_task = "Name two signal-chain blocks and the block CiTT is solving."
        expected = "Mentions source/sensor/electrode plus amplifier/filter/ADC/protection or display/control."
        stuck = "Ask which block touches the body and which block changes voltage, current, frequency, or digital code."
        unlocks = ["biomedical_context", "schematic_focus"]
    else:
        title = "Represent the circuit before equations"
        goal = "The student identifies the reference node, source direction, target branch, and relevant topology."
        tutor_move = "Ask the student to mark ground, source direction, and the target component or node."
        student_task = "Name ground, source/reference direction, and the branch or node to watch."
        expected = "Mentions ground/reference and the target node/component path."
        stuck = "Ask what would change if the ground symbol moved, or which component touches the target node."
        unlocks = ["schematic_focus"]

    return SocraticLectureStage(
        id="represent_system",
        title=title,
        goal=goal,
        pace="observe",
        prompts=[
            SocraticLecturePrompt(
                id="mark_representation",
                phase="represent",
                tutor_move=tutor_move,
                student_task=student_task,
                expected_student_evidence=expected,
                if_correct="Proceed to model choice.",
                if_stuck=stuck,
                unlocks=unlocks,
                plot_ids=_plots_for(packet, ["dc_node", "bme_differential", "bme_sampling"]),
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student maps the target onto either circuit topology or biomedical signal chain.",
        common_failure="Student treats the schematic as decoration instead of the source of sign/reference constraints.",
        instructor_note="The textbook often uses a figure or block diagram before algebra.",
    )


def _model_stage(circuit: CircuitProblem, packet: SolutionPacket) -> SocraticLectureStage:
    question, evidence, stuck = _model_text(circuit, packet)
    return SocraticLectureStage(
        id="choose_model",
        title="Choose the model",
        goal="The student chooses the analysis model and states one assumption or boundary.",
        pace="commit",
        prompts=[
            SocraticLecturePrompt(
                id="state_model",
                phase="model",
                tutor_move=question,
                student_task="State the model family and one simplifying assumption.",
                expected_student_evidence=evidence,
                if_correct="Ask for a qualitative prediction before arithmetic.",
                if_stuck=stuck,
                unlocks=["model_card", "equation_family"],
                plot_ids=_plots_for(packet, ["ac_sweep", "transient", "bme_sampling"]),
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student identifies the model family and at least one assumption.",
        common_failure="Student tries to reuse a memorized formula without checking whether the mode is DC, AC, transient, sampled, or safety-related.",
    )


def _prediction_stage(circuit: CircuitProblem, packet: SolutionPacket) -> SocraticLectureStage:
    prompt = _prediction_prompt(circuit, packet)
    return SocraticLectureStage(
        id="predict_before_calculating",
        title="Predict before calculating",
        goal="The student predicts sign, direction, magnitude trend, phase trend, settling direction, or failure mode before seeing values.",
        pace="predict",
        prompts=[
            SocraticLecturePrompt(
                id="qualitative_prediction",
                phase="predict",
                tutor_move=prompt,
                student_task="Make a qualitative prediction and name the limiting case you used.",
                expected_student_evidence="A direction, comparison, limiting value, or expected shape.",
                if_correct="Unlock the local equation or verified plot comparison.",
                if_stuck="Ask for only high/low, larger/smaller, lead/lag, rise/fall, pass/attenuate, reject/leak, or safe/unsafe.",
                unlocks=["teaching_plot_preview"],
                plot_ids=_plots_for(packet, ["dc_component", "ac_sweep", "transient", "bme_noise", "bme_cmrr"]),
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student gives a physically plausible qualitative expectation.",
        common_failure="Student computes without a sanity check, so mistakes in sign, unit prefix, or model choice go unnoticed.",
    )


def _commit_stage(circuit: CircuitProblem, packet: SolutionPacket) -> SocraticLectureStage:
    return SocraticLectureStage(
        id="commit_minimal_equation",
        title="Commit to a minimal equation",
        goal="The student writes the smallest useful relation before the verified result is revealed.",
        pace="calculate",
        prompts=[
            SocraticLecturePrompt(
                id="first_equation",
                phase="commit",
                tutor_move="Ask for one local equation, sign convention, or transfer relation, not a full solution dump.",
                student_task="Write the first equation or choose the equation family.",
                expected_student_evidence="KCL, divider/current path, impedance relation, first-order transient relation, sensor conversion, sampling relation, or safety current/energy relation.",
                if_correct="Compare the equation's qualitative consequence with the verified packet.",
                if_stuck="Offer a representation cue instead of the final equation.",
                reveal_policy="value_refs_only",
                unlocks=["equation_path", "value_ref_names"],
                value_refs=_goal_value_refs(packet),
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student commits a local equation or explicitly chooses the correct equation family.",
        common_failure="Student asks for the answer without committing to a model.",
        instructor_note="End-of-chapter practice should stop here until the student commits.",
    )


def _compare_stage(circuit: CircuitProblem, packet: SolutionPacket) -> SocraticLectureStage:
    return SocraticLectureStage(
        id="compare_verified_view",
        title="Compare with verified views",
        goal="The student connects their model to solver-backed plots, checks, and value references.",
        pace="interpret",
        prompts=[
            SocraticLecturePrompt(
                id="connect_plot_or_check",
                phase="compare",
                tutor_move="Ask which plot, verification check, or value reference confirms the prediction.",
                student_task="Pick one verified view and explain whether it matches the prediction.",
                expected_student_evidence="Mentions a plot id, value ref, KCL/power check, phase/magnitude trend, or transient shape.",
                if_correct="Allow verified reveal if the student asks, then move to nonideality or transfer.",
                if_stuck="Point to one available plot or check and ask only what trend it shows.",
                reveal_policy="allow_verified_reveal",
                unlocks=["verified_values", "verification_checks"],
                plot_ids=[plot.id for plot in packet.teaching_plots],
                value_refs=_goal_value_refs(packet),
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student can connect reasoning to a solver-backed artifact.",
        common_failure="Student treats the verified answer as authority but cannot explain which model feature produced it.",
    )


def _nonideality_stage(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> SocraticLectureStage:
    return SocraticLectureStage(
        id="nonideality_and_safety",
        title="Check nonideality and safety boundary",
        goal="The student names the real-world limitation that the ideal circuit hides.",
        pace="interpret",
        prompts=[
            SocraticLecturePrompt(
                id="name_real_boundary",
                phase="check",
                tutor_move="Ask what would corrupt the measurement or make the device unsafe outside the ideal model.",
                student_task="Name one relevant boundary: loading, offset, drift, noise, artifact, saturation, CMRR leakage, aliasing, isolation, leakage current, or delivered energy.",
                expected_student_evidence="A nonideality tied to this circuit or biomedical context.",
                if_correct="Move to transfer: change one constraint and predict the first affected quantity.",
                if_stuck="Offer the textbook checklist: sensor/electrode, signal conditioning, dynamic response, interference, noise, safety.",
                reveal_policy="value_refs_only",
                unlocks=["bme_context", "safety_notes"],
                plot_ids=_plots_for(packet, ["bme_noise", "bme_cmrr", "bme_sampling"]),
                value_refs=[observation.id for observation in packet.tutor_observations],
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student names one limitation and relates it to this measurement chain.",
        common_failure="Student treats an educational ideal-circuit answer as a real device guarantee.",
    )


def _transfer_stage(circuit: CircuitProblem, packet: SolutionPacket) -> SocraticLectureStage:
    return SocraticLectureStage(
        id="transfer_variant",
        title="Transfer to a nearby variant",
        goal="The student turns the worked problem into a reusable rule.",
        pace="transfer",
        prompts=[
            SocraticLecturePrompt(
                id="change_one_constraint",
                phase="transfer",
                tutor_move="Ask what changes first if one component, frequency, sampling rate, sensor impedance, or safety path changes.",
                student_task="Choose one constraint to vary and predict the first affected quantity.",
                expected_student_evidence="Names a changed gain, cutoff, time constant, noise, loading, CMRR, aliasing margin, power, or safety current path.",
                if_correct="Suggest an end-of-chapter style practice variant.",
                if_stuck="Ask which axis would move on the most relevant plot.",
                reveal_policy="allow_verified_reveal",
                unlocks=["practice_variant"],
                plot_ids=[plot.id for plot in packet.teaching_plots],
                value_refs=_goal_value_refs(packet),
                focus=_goal_focus(circuit),
            )
        ],
        advance_when="Student states a reusable rule or variant prediction.",
        common_failure="Student can reproduce the calculation but cannot transfer the model.",
    )


def _domain_label(circuit: CircuitProblem, packet: SolutionPacket) -> str:
    if circuit.bme_metadata is not None:
        return "biomedical signal-chain"
    if packet.transient_response is not None:
        return "transient"
    if packet.ac_sweep or packet.ac_requested_answers:
        return "frequency-domain"
    if any(component.type in {"op_amp_ideal", "op_amp_nonideal"} for component in circuit.components):
        return "amplifier"
    return "circuit"


def _textbook_pacing_summary(circuit: CircuitProblem, packet: SolutionPacket) -> list[str]:
    pacing = [
        "Begin with context and measurand, not arithmetic.",
        "Force a representation checkpoint before formulas.",
        "Ask for a qualitative prediction before numeric substitution.",
        "Use verified plots/checks as interpretation artifacts, not decorations.",
    ]
    if circuit.bme_metadata is not None:
        pacing.append("Add biomedical chain, interference, noise, and safety boundary checks.")
    if packet.ac_sweep or packet.ac_requested_answers:
        pacing.append("Treat magnitude and phase as a pair; ask for limiting frequency behavior.")
    if packet.transient_response is not None:
        pacing.append("Tie initial condition, final value, and storage-element time scale together.")
    return pacing


def _mode_profiles() -> list[SocraticModeProfile]:
    return [
        SocraticModeProfile(
            mode="first_exposure",
            tutor_posture="Teach vocabulary and representation before formulas.",
            reveal_rule="Reveal concepts early, formulas after model choice, final values after prediction and equation commitment.",
            pace_notes=[
                "Use one question per turn.",
                "Offer choices when the student lacks a frame.",
                "Use plots before algebra when possible.",
            ],
        ),
        SocraticModeProfile(
            mode="worked_example",
            tutor_posture="Mirror the textbook example: scene, knowns, unknown, model, calculation, interpretation.",
            reveal_rule="Pause before each transition; reveal the next move only after a prediction.",
            pace_notes=[
                "Keep the derivation segmented.",
                "Ask what the next line should accomplish before showing it.",
            ],
        ),
        SocraticModeProfile(
            mode="end_of_chapter_practice",
            tutor_posture="Assume prior exposure and require student commitment.",
            reveal_rule="No equation or final answer until the student states model, reference/sign, and first local equation.",
            pace_notes=[
                "Use hint levels.",
                "Diagnose one blocker at a time.",
                "End with transfer or error analysis.",
            ],
        ),
        SocraticModeProfile(
            mode="review_debug",
            tutor_posture="Start from the student's attempted reasoning and find one local blocker.",
            reveal_rule="Use the hidden verified packet only to check local consistency.",
            pace_notes=[
                "Do not correct every mistake at once.",
                "Return a next action the student can perform.",
            ],
        ),
    ]


def _model_text(circuit: CircuitProblem, packet: SolutionPacket) -> tuple[str, str, str]:
    if packet.transient_response is not None:
        return (
            "Ask which storage element sets the time behavior and what the initial/final values mean.",
            "Mentions capacitor/inductor storage, initial value, final value, and time evolution.",
            "Ask whether the output should move instantly, exponentially, or with ringing.",
        )
    if packet.ac_sweep or packet.ac_requested_answers:
        return (
            "Ask which components become complex impedances and whether the answer is magnitude, phase, or both.",
            "Mentions impedance, frequency, magnitude/phase, cutoff, or sweep behavior.",
            "Ask what a capacitor or inductor becomes at very low and very high frequency.",
        )
    if circuit.bme_metadata is not None:
        return (
            "Ask which biomedical idealization is being made and which sensor/electrode or amplifier nonideality is being ignored.",
            "Mentions signal-chain role, ideal circuit boundary, and one real-world limitation.",
            "Ask what block touches the body and what block CiTT is actually solving.",
        )
    if any(component.type in {"op_amp_ideal", "op_amp_nonideal"} for component in circuit.components):
        return (
            "Ask which op-amp assumption is active and which feedback path sets the gain.",
            "Mentions virtual short/input current assumptions or nonideal output limits.",
            "Ask where feedback returns from output to input.",
        )
    return (
        "Ask whether this is a current path, divider, coupled nodal network, or source transformation problem.",
        "Mentions KCL/current path/reference node/sign convention.",
        "Ask which node or branch cannot be ignored.",
    )


def _prediction_prompt(circuit: CircuitProblem, packet: SolutionPacket) -> str:
    if packet.transient_response is not None:
        return "Ask whether the waveform should rise, fall, settle, overshoot, or ring before reading samples."
    if packet.ac_sweep:
        return "Ask what should happen to magnitude and phase at low frequency, near cutoff, and high frequency."
    if packet.ac_requested_answers:
        return "Ask whether the output should be attenuated or amplified and whether it should lead or lag."
    if circuit.bme_metadata is not None:
        return "Ask which is larger: the desired differential signal, common-mode interference, noise, or output swing limit."
    return "Ask the student to predict current direction, relative node levels, and which component supplies or absorbs power."


def _needs_nonideality_stage(circuit: CircuitProblem, packet: SolutionPacket) -> bool:
    if circuit.bme_metadata is not None or packet.tutor_observations:
        return True
    return any(
        component.type
        in {
            "op_amp_nonideal",
            "capacitor",
            "inductor",
            "diode",
        }
        for component in circuit.components
    )


def _safety_notes(circuit: CircuitProblem, packet: SolutionPacket) -> list[str]:
    notes = [
        "Solver-backed values are educational circuit results, not medical-device certification.",
    ]
    if circuit.bme_metadata is not None:
        notes.append("Biomedical context must stay separate from patient safety or regulatory claims.")
    if _domain_label(circuit, packet) in {"biomedical signal-chain", "transient"}:
        notes.append("Ask about saturation, protection, and real-world limits before transferring the result.")
    return notes


def _gemini_prompt(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    stages: list[SocraticLectureStage],
) -> str:
    stage_lines = "\n".join(
        f"- {stage.id}: {stage.goal} Advance when: {stage.advance_when}"
        for stage in stages
    )
    plot_ids = ", ".join(plot.id for plot in packet.teaching_plots) or "none"
    value_refs = ", ".join(_goal_value_refs(packet)) or "none"
    return f"""
You are CiTT's Socratic guided-lecture planner.

Circuit:
- id: {circuit.id}
- title: {circuit.title}
- analysis_type: {circuit.analysis_type}
- topology_id: {circuit.topology_id}
- biomedical_context: {circuit.bme_metadata is not None}

Available verified artifacts:
- teaching_plot_ids: {plot_ids}
- answer_value_refs: {value_refs}
- tutor_observation_ids: {", ".join(observation.id for observation in packet.tutor_observations) or "none"}

Use this textbook-inspired pace:
{stage_lines}

Rules:
- Do not invent numeric values.
- Do not reveal final values unless the current stage reveal_policy allows it.
- Ask one local question at a time.
- First-exposure mode: teach vocabulary and representation before formulas.
- End-of-chapter mode: require a student commitment before equations or final values.
- Use solver-backed value_refs and teaching_plot_ids only as references to verified artifacts.
""".strip()


def _goal_focus(circuit: CircuitProblem) -> TutorFocus:
    component_ids = {component.id for component in circuit.components}
    components: list[str] = []
    nodes: list[str] = []
    goals: list[str] = []
    for goal in circuit.goals:
        goals.append(goal.id)
        if goal.target in component_ids:
            components.append(goal.target)
        elif goal.target:
            nodes.append(goal.target)
    return TutorFocus(
        components=_unique(components),
        nodes=_unique(nodes),
        current_paths=_unique(components),
        goals=_unique(goals),
    )


def _goal_value_refs(packet: SolutionPacket) -> list[str]:
    refs = list(packet.requested_answers)
    refs.extend(f"{key}_magnitude" for key in packet.ac_requested_answers)
    refs.extend(f"{key}_phase" for key in packet.ac_requested_answers)
    if packet.transient_response is not None:
        refs.extend(["initial_voltage", "final_voltage", "time_constant"])
    return _unique(refs)


def _plots_for(packet: SolutionPacket, needles: list[str]) -> list[str]:
    ids: list[str] = []
    for plot in packet.teaching_plots:
        normalized = plot.id.lower()
        if any(needle in normalized for needle in needles):
            ids.append(plot.id)
    return ids


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values
