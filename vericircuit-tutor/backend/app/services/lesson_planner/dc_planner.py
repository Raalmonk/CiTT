from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, TutorObservation, TutorStep
from app.services.lesson_planner import common
from app.services.lesson_planner.graph import CircuitGraph
from app.services.lesson_planner.motifs import (
    CircuitMotifs,
    DifferentialAmpMotif,
    TransimpedanceMotif,
    VoltageDividerMotif,
)


def build_dc_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
    motifs: CircuitMotifs,
) -> list[TutorStep]:
    if motifs.differential_amp is not None:
        return _differential_amp_steps(circuit, packet, graph, motifs.differential_amp)

    if motifs.transimpedance is not None:
        return _transimpedance_steps(circuit, packet, motifs.transimpedance)

    divider = _select_voltage_divider(circuit, motifs)
    if divider is not None:
        return _voltage_divider_steps(circuit, packet, divider)

    return _generic_dc_steps(circuit, packet, graph)


def _select_voltage_divider(
    circuit: CircuitProblem,
    motifs: CircuitMotifs,
) -> VoltageDividerMotif | None:
    if not motifs.voltage_dividers:
        return None
    for goal in circuit.goals:
        for motif in motifs.voltage_dividers:
            if goal.quantity == "node_voltage" and goal.target == motif.output_node:
                return motif
            if goal.quantity in {"component_voltage", "component_current", "component_power"} and goal.target in {
                motif.upper_resistor_id,
                motif.lower_resistor_id,
            }:
                return motif
    return motifs.voltage_dividers[0]


def _goal_ids_for_target(circuit: CircuitProblem, targets: set[str]) -> list[str]:
    return [goal.id for goal in circuit.goals if goal.target in targets or goal.id in targets]


def _voltage_divider_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    motif: VoltageDividerMotif,
) -> list[TutorStep]:
    lower_goals = _goal_ids_for_target(circuit, {motif.output_node, motif.lower_resistor_id})
    all_goals = [goal.id for goal in circuit.goals]
    current_value = (
        common.requested_answer(packet, "circuit_current", "Circuit current")
        or common.component_current(packet, motif.upper_resistor_id, f"{motif.upper_resistor_id} current")
        or common.component_current(packet, motif.lower_resistor_id, f"{motif.lower_resistor_id} current")
    )
    answer_values = [
        common.requested_answer_for_goal(packet, goal_id)
        for goal_id in (lower_goals or all_goals)
    ]

    return [
        TutorStep(
            id="divider_reference",
            title="Anchor the source and reference node",
            body="The source defines the top node of the divider relative to ground.",
            look_at=(
                f"Look at {motif.source_id}, node {motif.top_node}, and ground. "
                "The source fixes the voltage span that the resistors divide."
            ),
            why_it_matters="A divider only makes sense after the voltage reference is clear.",
            common_mistake="Starting with resistor arithmetic before checking which node the source fixes.",
            focus=common.focus(
                circuit,
                components=[motif.source_id],
                nodes=[motif.top_node, motif.ground_node],
                current_paths=[motif.source_id],
            ),
            verified_values=common.only_present(
                [common.node_voltage(packet, motif.top_node, "Top node voltage")]
            ),
            next_action="Follow the same series current through the two divider resistors.",
        ),
        TutorStep(
            id="divider_series_path",
            title="Follow the series current",
            body="The two resistors form one path from the source node to ground.",
            look_at=(
                f"Look at {motif.upper_resistor_id} and {motif.lower_resistor_id}. "
                f"The only middle node is {motif.output_node}."
            ),
            why_it_matters="Because the resistors are in series, one current explains both voltage drops.",
            common_mistake="Treating the two resistors like independent parallel branches.",
            focus=common.focus(
                circuit,
                components=[motif.upper_resistor_id, motif.lower_resistor_id],
                nodes=[motif.top_node, motif.output_node, motif.ground_node],
                current_paths=[motif.upper_resistor_id, motif.lower_resistor_id],
            ),
            verified_values=common.only_present([current_value]),
            next_action="Use the output-node reference to read the requested value.",
        ),
        TutorStep(
            id="divider_output",
            title="Read the divider output",
            body="The requested divider output is read at the middle node or across the lower resistor.",
            look_at=(
                f"Look at {motif.output_node} relative to {motif.ground_node}. "
                "That is the output side of the divider."
            ),
            why_it_matters="The answer is tied to the requested reference, not automatically to the full source voltage.",
            common_mistake="Reporting the source voltage or reversing the polarity of the requested output.",
            focus=common.focus(
                circuit,
                components=[motif.lower_resistor_id],
                nodes=[motif.output_node, motif.ground_node],
                current_paths=[motif.lower_resistor_id],
                goals=lower_goals or all_goals,
            ),
            verified_values=common.only_present(
                [
                    *answer_values,
                    common.node_voltage(packet, motif.output_node, "Output node voltage"),
                ]
            ),
            next_action="Check what the internal verification badge does and does not prove.",
        ),
        common.verification_step(circuit, packet),
    ]


def _differential_observations(
    graph: CircuitGraph,
    motif: DifferentialAmpMotif,
) -> list[TutorObservation]:
    positive_source = graph.component(motif.positive_source_id)
    negative_source = graph.component(motif.negative_source_id)
    if positive_source is None or negative_source is None:
        return []
    differential = positive_source.value - negative_source.value
    common_mode = 0.5 * (positive_source.value + negative_source.value)
    observations = [
        TutorObservation(
            id="differential_input_voltage",
            label="Differential input voltage",
            value=float(differential),
            unit="V",
            note="Computed deterministically from the two input source values in Circuit IR.",
        ),
        TutorObservation(
            id="common_mode_input_voltage",
            label="Common-mode input voltage",
            value=float(common_mode),
            unit="V",
            note="Average of the two input source values in Circuit IR.",
        ),
    ]
    if abs(common_mode) > 1e-15:
        observations.append(
            TutorObservation(
                id="differential_to_common_mode_ratio",
                label="Differential/common-mode ratio",
                value=float(abs(differential / common_mode)),
                unit="V/V",
                note="Shows the desired signal size relative to common-mode level.",
            )
        )
    return observations


def _differential_amp_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
    motif: DifferentialAmpMotif,
) -> list[TutorStep]:
    resistor_focus = [
        motif.positive_input_resistor_id,
        motif.negative_input_resistor_id,
        motif.feedback_resistor_id,
    ]
    if motif.reference_resistor_id:
        resistor_focus.append(motif.reference_resistor_id)

    answer_values = common.all_requested_observations(packet)
    return [
        TutorStep(
            id="differential_sources",
            title="Identify the differential input pair",
            body="The input information is the difference between two source nodes, not either source alone.",
            look_at=(
                f"Look at {motif.positive_source_id} and {motif.negative_source_id}. "
                "Treat them as a pair."
            ),
            why_it_matters="Differential amplifiers are built to amplify the difference while rejecting common-mode level.",
            common_mistake="Measuring each input to ground and forgetting the differential signal.",
            focus=common.focus(
                circuit,
                components=[motif.positive_source_id, motif.negative_source_id],
                nodes=[motif.positive_input_node, motif.negative_input_node],
            ),
            verified_values=_differential_observations(graph, motif),
            next_action="Trace how the resistor network feeds that pair into the op-amp.",
        ),
        TutorStep(
            id="differential_feedback_network",
            title="Follow the feedback network",
            body="The input and feedback resistors set the ideal differential behavior around the op-amp.",
            look_at="Look at the input resistors, feedback resistor, and op-amp input nodes together.",
            why_it_matters="Resistor ratios decide whether the circuit behaves like a useful differential amplifier.",
            common_mistake="Calling it common-mode rejection without checking the matching network.",
            focus=common.focus(
                circuit,
                components=[*resistor_focus, motif.op_amp_id],
                nodes=[motif.op_amp_plus_node, motif.op_amp_minus_node, motif.output_node],
                current_paths=resistor_focus,
            ),
            verified_values=[],
            next_action="Read the solver-backed output node.",
        ),
        TutorStep(
            id="differential_output",
            title="Read the verified output",
            body="The output node is the verified answer for the ideal closed-loop model.",
            look_at=f"Look at {motif.output_node}, the output node of {motif.op_amp_id}.",
            why_it_matters="This connects the input difference to the signal-chain output.",
            common_mistake="Forgetting the output reference or interpreting the sign without checking polarity.",
            focus=common.focus(
                circuit,
                components=[motif.op_amp_id, motif.feedback_resistor_id],
                nodes=[motif.output_node],
                current_paths=[motif.feedback_resistor_id],
                goals=[goal.id for goal in circuit.goals],
            ),
            verified_values=answer_values,
            next_action="Separate the ideal result from real hardware limitations.",
        ),
        common.verification_step(circuit, packet),
    ]


def _transimpedance_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    motif: TransimpedanceMotif,
) -> list[TutorStep]:
    current_goals = _goal_ids_for_target(circuit, {motif.current_source_id})
    output_goals = _goal_ids_for_target(circuit, {motif.output_node})
    return [
        TutorStep(
            id="tia_input_current",
            title="Start from input current",
            body="A transimpedance stage begins with current and converts it into voltage.",
            look_at=f"Look at {motif.current_source_id}. The input signal is current, not voltage.",
            why_it_matters="The rest of the circuit exists to turn that current into a readable output voltage.",
            common_mistake="Trying to assign a sensor voltage before following the current path.",
            focus=common.focus(
                circuit,
                components=[motif.current_source_id],
                nodes=[motif.summing_node, motif.reference_node],
                current_paths=[motif.current_source_id],
                goals=current_goals,
            ),
            verified_values=common.only_present(
                [
                    *[common.requested_answer_for_goal(packet, goal_id) for goal_id in current_goals],
                    common.component_current(packet, motif.current_source_id, f"{motif.current_source_id} current"),
                ]
            ),
            next_action="Move to the summing node at the op-amp input.",
        ),
        TutorStep(
            id="tia_summing_node",
            title="Inspect the summing node",
            body="Feedback makes the inverting input the current-balance point in the ideal model.",
            look_at=f"Look at node {motif.summing_node}, where input current and feedback meet.",
            why_it_matters="If the op-amp holds this node near reference, input current must flow through feedback.",
            common_mistake="Calling the node ground without checking the feedback model.",
            focus=common.focus(
                circuit,
                components=[motif.op_amp_id, motif.current_source_id, motif.feedback_resistor_id],
                nodes=[motif.summing_node, motif.reference_node],
                current_paths=[motif.current_source_id, motif.feedback_resistor_id],
            ),
            verified_values=common.only_present(
                [common.node_voltage(packet, motif.summing_node, "Summing-node voltage")]
            ),
            next_action="Follow that current through the feedback resistor.",
        ),
        TutorStep(
            id="tia_feedback_conversion",
            title="Convert current through feedback",
            body="The feedback resistor is the transimpedance element.",
            look_at=f"Look at {motif.feedback_resistor_id} between the summing node and output.",
            why_it_matters="Current through this resistor creates the output voltage.",
            common_mistake="Remembering the gain magnitude but losing the polarity set by current direction.",
            focus=common.focus(
                circuit,
                components=[motif.feedback_resistor_id, motif.op_amp_id],
                nodes=[motif.summing_node, motif.output_node],
                current_paths=[motif.feedback_resistor_id],
                goals=output_goals,
            ),
            verified_values=common.only_present(
                [common.requested_answer_for_goal(packet, goal_id) for goal_id in output_goals]
            ),
            next_action="Check whether the ideal output fits real hardware limits.",
        ),
        common.verification_step(circuit, packet),
    ]


def _target_neighborhood(circuit: CircuitProblem, graph: CircuitGraph) -> tuple[list[str], list[str], list[str]]:
    components, nodes, goals = common.goal_focus_ids(circuit)
    for node in list(nodes):
        components.extend(component.id for component in graph.components_at(node))
    for component_id in list(components):
        component = graph.component(component_id)
        if component:
            nodes.extend(component.nodes)
    return list(dict.fromkeys(components)), list(dict.fromkeys(nodes)), goals


def _generic_dc_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
) -> list[TutorStep]:
    source_components = common.source_ids(circuit)
    target_components, target_nodes, goal_ids = _target_neighborhood(circuit, graph)
    return [
        TutorStep(
            id="dc_sources_and_ground",
            title="Identify sources and ground",
            body="Start by finding the reference node and the components that impose known currents or voltages.",
            look_at="Look at the sources and the ground node before reading any requested answer.",
            why_it_matters="Ground and source references define the signs and node voltages used by the solver.",
            common_mistake="Solving a numeric answer without checking the reference node.",
            focus=common.focus(
                circuit,
                components=source_components,
                nodes=[circuit.ground_node],
                current_paths=source_components,
            ),
            verified_values=[],
            next_action="Move from the sources toward the requested target.",
        ),
        TutorStep(
            id="dc_target_neighborhood",
            title="Inspect the target neighborhood",
            body="The requested quantity is controlled by the components directly connected to its target node or branch.",
            look_at="Look at the highlighted target and its immediate neighboring components.",
            why_it_matters="A good circuit explanation narrows attention before showing the final number.",
            common_mistake="Jumping to the answer without understanding what local branch or node it belongs to.",
            focus=common.focus(
                circuit,
                components=target_components,
                nodes=target_nodes,
                current_paths=target_components,
                goals=goal_ids,
            ),
            verified_values=[],
            next_action="Read the verified requested value.",
        ),
        TutorStep(
            id="dc_requested_answer",
            title="Read the verified answer",
            body="The requested values are taken from the solved and internally verified packet.",
            look_at="Look at the highlighted requested target and the verified quantity below.",
            why_it_matters="The number shown here comes from the solver packet, not a direct LLM calculation.",
            common_mistake="Copying a number without checking which reference or sign convention it uses.",
            focus=common.focus(
                circuit,
                components=target_components,
                nodes=target_nodes,
                current_paths=target_components,
                goals=goal_ids,
            ),
            verified_values=common.all_requested_observations(packet),
            next_action="Check the verification boundary.",
        ),
        common.verification_step(circuit, packet),
    ]
