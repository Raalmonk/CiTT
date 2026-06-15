from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, TutorObservation, TutorStep
from app.services.lesson_planner import common
from app.services.lesson_planner.graph import CircuitGraph
from app.services.lesson_planner.motifs import CircuitMotifs, RCLowPassMotif


def build_ac_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
    motifs: CircuitMotifs,
) -> list[TutorStep]:
    low_pass = _select_low_pass(circuit, motifs)
    if low_pass is not None:
        return _rc_low_pass_steps(circuit, packet, graph, low_pass)
    return _generic_ac_steps(circuit, packet, graph)


def _select_low_pass(circuit: CircuitProblem, motifs: CircuitMotifs) -> RCLowPassMotif | None:
    if not motifs.rc_low_passes:
        return None
    for goal in circuit.goals:
        for motif in motifs.rc_low_passes:
            if goal.quantity == "node_voltage" and goal.target == motif.output_node:
                return motif
            if goal.quantity in {"component_voltage", "component_current", "component_power"} and goal.target in {
                motif.resistor_id,
                motif.capacitor_id,
            }:
                return motif
    return motifs.rc_low_passes[0]


def _goal_ids_for_output(circuit: CircuitProblem, motif: RCLowPassMotif) -> list[str]:
    return [
        goal.id
        for goal in circuit.goals
        if goal.target in {motif.output_node, motif.resistor_id, motif.capacitor_id}
    ]


def _analysis_frequency_observation(packet: SolutionPacket):
    if packet.frequency_hz is None:
        return None
    return common.packet_observation(packet, "analysis_frequency") or TutorObservation(
        id="analysis_frequency",
        label="Analysis frequency",
        value=float(packet.frequency_hz),
        unit="Hz",
    )


def _rc_low_pass_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
    motif: RCLowPassMotif,
) -> list[TutorStep]:
    output_goal_ids = _goal_ids_for_output(circuit, motif) or [goal.id for goal in circuit.goals]
    output_values = []
    for goal_id in output_goal_ids:
        output_values.extend(
            [
                common.ac_answer_magnitude(packet, goal_id, "Output magnitude"),
                common.ac_answer_phase(packet, goal_id),
            ]
        )
    resistor = graph.component(motif.resistor_id)
    capacitor = graph.component(motif.capacitor_id)

    steps = [
        TutorStep(
            id="ac_source_frequency",
            title="Identify the source phasor and frequency",
            body="AC lessons start with the source phasor and the frequency where the circuit is being evaluated.",
            look_at=f"Look at {motif.source_id} and the input node {motif.input_node}.",
            why_it_matters="Capacitor and inductor behavior depends on frequency, so this is not a DC reading.",
            common_mistake="Reading the AC result like a DC node voltage and dropping the frequency context.",
            focus=common.focus(
                circuit,
                components=[motif.source_id],
                nodes=[motif.input_node, motif.ground_node],
                current_paths=[motif.source_id],
            ),
            verified_values=common.only_present([_analysis_frequency_observation(packet)]),
            next_action="Move to the RC pair that creates the low-pass pole.",
        ),
        TutorStep(
            id="ac_low_pass_pole",
            title="Locate the RC low-pass pole",
            body="The resistor from input to output and the capacitor from output to ground form a first-order low-pass.",
            look_at=f"Look at {motif.resistor_id} feeding {motif.output_node}, then {motif.capacitor_id} to ground.",
            why_it_matters="At higher frequency, the capacitor gives more signal a path to ground instead of the output.",
            common_mistake="Using 1/(RC) as Hz instead of 1/(2*pi*RC).",
            focus=common.focus(
                circuit,
                components=[motif.resistor_id, motif.capacitor_id],
                nodes=[motif.output_node, motif.ground_node],
                current_paths=[motif.resistor_id, motif.capacitor_id],
            ),
            verified_values=common.only_present(
                [
                    common.packet_observation(packet, "low_pass_cutoff_frequency")
                    or common.cutoff_frequency_observation(resistor, capacitor),
                    common.packet_observation(packet, "first_order_corner_ratio"),
                ]
            ),
            next_action="Read the phasor output at the requested node.",
        ),
        TutorStep(
            id="ac_output_phasor",
            title="Read the output magnitude and phase",
            body="The output is a phasor, so magnitude and phase describe the signal together.",
            look_at=f"Look at output node {motif.output_node} relative to {motif.ground_node}.",
            why_it_matters="A filter can change timing as well as amplitude.",
            common_mistake="Reporting only magnitude and forgetting phase near the cutoff region.",
            focus=common.focus(
                circuit,
                components=[motif.resistor_id, motif.capacitor_id],
                nodes=[motif.output_node, motif.ground_node],
                current_paths=[motif.capacitor_id],
                goals=output_goal_ids,
            ),
            verified_values=common.only_present(output_values),
            next_action="Check whether the result needs measurement-system context.",
        ),
        common.verification_step(circuit, packet),
    ]
    return steps


def _generic_ac_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
) -> list[TutorStep]:
    component_focus, node_focus, goal_ids = common.goal_focus_ids(circuit)
    source_components = common.source_ids(circuit)
    for node in list(node_focus):
        component_focus.extend(component.id for component in graph.components_at(node))
    component_focus = list(dict.fromkeys(component_focus))
    return [
        TutorStep(
            id="ac_source_frequency",
            title="Identify source phasor and frequency",
            body="AC answers depend on the source phasor and analysis frequency.",
            look_at="Look at the AC source and the frequency before reading the requested output.",
            why_it_matters="Capacitors and inductors change impedance with frequency.",
            common_mistake="Treating a phasor answer as if it were a DC scalar.",
            focus=common.focus(
                circuit,
                components=source_components,
                nodes=[circuit.ground_node],
                current_paths=source_components,
            ),
            verified_values=common.only_present([_analysis_frequency_observation(packet)]),
            next_action="Move to the requested output neighborhood.",
        ),
        TutorStep(
            id="ac_requested_output",
            title="Read the requested phasor",
            body="The requested AC quantity is read from the verified complex solution packet.",
            look_at="Look at the highlighted target and read magnitude plus phase.",
            why_it_matters="Magnitude and phase together describe the filtered or shifted signal.",
            common_mistake="Copying magnitude without phase or reference node.",
            focus=common.focus(
                circuit,
                components=component_focus,
                nodes=node_focus,
                current_paths=component_focus,
                goals=goal_ids,
            ),
            verified_values=common.all_requested_observations(packet),
            next_action="Check the internal verification boundary.",
        ),
        common.verification_step(circuit, packet),
    ]
