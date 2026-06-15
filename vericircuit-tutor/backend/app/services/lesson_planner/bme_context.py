from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, TutorStep
from app.services.lesson_planner import common
from app.services.lesson_planner.motifs import CircuitMotifs


def attach_bme_context_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    steps: list[TutorStep],
    motifs: CircuitMotifs,
) -> list[TutorStep]:
    metadata = circuit.bme_metadata
    if metadata is None or not steps:
        return steps

    enhanced = [step.model_copy(deep=True) for step in steps]
    first = enhanced[0]
    first.why_it_matters = _append_sentence(first.why_it_matters, metadata.biomedical_context)

    context_focus = _context_focus(circuit, motifs, enhanced)
    values = _context_observations(packet, [
        "differential_input_voltage",
        "common_mode_input_voltage",
        "cmrr_mismatch_percent",
        "cmrr_common_mode_leakage_output",
        "cmrr_mismatch_estimate_db",
        "adc_sampling_frequency",
        "adc_nyquist_frequency",
        "adc_attenuation_at_nyquist",
        "real_op_amp_saturation_warning",
        "noise_budget_bandwidth",
    ])

    enhanced.insert(
        max(1, len(enhanced) - 1),
        TutorStep(
            id="bme_context_boundary",
            title="Connect the circuit result to the biomedical context",
            body="The electrical result is one part of a larger biomedical measurement chain.",
            look_at=metadata.signal_chain_role,
            why_it_matters=metadata.biomedical_context,
            common_mistake=(metadata.common_lab_mistakes[0] if metadata.common_lab_mistakes else None),
            focus=context_focus,
            verified_values=values,
            caution=metadata.safety_note,
            next_action="Keep the ideal circuit result separate from real hardware limits.",
        ),
    )
    return enhanced


def _context_observations(packet: SolutionPacket, observation_ids: list[str]):
    values = []
    lookup = common.observation_lookup(packet)
    for observation_id in observation_ids:
        observation = lookup.get(observation_id)
        if observation is not None:
            values.append(observation)
    for observation in packet.tutor_observations:
        if observation.id.startswith(("photodiode_shot_noise_", "thermal_noise_")):
            values.append(observation)
    return values


def _append_sentence(original: str | None, addition: str) -> str:
    if not original:
        return addition
    if original.endswith("."):
        return f"{original} {addition}"
    return f"{original}. {addition}"


def _context_focus(circuit: CircuitProblem, motifs: CircuitMotifs, steps: list[TutorStep]):
    if motifs.differential_amp is not None:
        motif = motifs.differential_amp
        components = [
            motif.op_amp_id,
            motif.feedback_resistor_id,
            motif.positive_input_resistor_id,
            motif.negative_input_resistor_id,
        ]
        if motif.reference_resistor_id:
            components.append(motif.reference_resistor_id)
        return common.focus(
            circuit,
            components=components,
            nodes=[motif.output_node, motif.op_amp_plus_node, motif.op_amp_minus_node],
            current_paths=[component for component in components if component != motif.op_amp_id],
            goals=[goal.id for goal in circuit.goals],
        )
    if motifs.transimpedance is not None:
        motif = motifs.transimpedance
        return common.focus(
            circuit,
            components=[motif.op_amp_id, motif.current_source_id, motif.feedback_resistor_id],
            nodes=[motif.summing_node, motif.output_node],
            current_paths=[motif.current_source_id, motif.feedback_resistor_id],
            goals=[goal.id for goal in circuit.goals],
        )
    if motifs.rc_low_passes:
        motif = motifs.rc_low_passes[0]
        return common.focus(
            circuit,
            components=[motif.resistor_id, motif.capacitor_id],
            nodes=[motif.output_node, motif.ground_node],
            current_paths=[motif.resistor_id, motif.capacitor_id],
            goals=[goal.id for goal in circuit.goals],
        )
    return steps[-1].focus
