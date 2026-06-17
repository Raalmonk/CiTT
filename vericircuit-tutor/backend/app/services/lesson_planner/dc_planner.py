from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class CurrentDividerMotif:
    source_id: str
    top_node: str
    ground_node: str
    branch_resistor_ids: list[str]


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

    if _is_bridge_like(circuit, graph):
        return _bridge_like_steps(circuit, packet, graph)

    divider = _select_voltage_divider(circuit, motifs)
    if divider is not None:
        return _voltage_divider_steps(circuit, packet, divider)

    current_divider = _detect_current_divider(graph)
    if current_divider is not None:
        return _current_divider_steps(circuit, packet, current_divider)

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
                motif.source_id,
                motif.upper_resistor_id,
                motif.lower_resistor_id,
            }:
                return motif
    if not circuit.goals and len(motifs.voltage_dividers) == 1:
        return motifs.voltage_dividers[0]
    return None


def _goal_ids_for_target(circuit: CircuitProblem, targets: set[str]) -> list[str]:
    return [goal.id for goal in circuit.goals if goal.target in targets or goal.id in targets]


def _detect_current_divider(graph: CircuitGraph) -> CurrentDividerMotif | None:
    for source in graph.current_sources_to_ground():
        top_node = graph.source_node(source)
        if top_node is None:
            continue
        branches = [
            component.id
            for component in graph.components_between(top_node, graph.ground, "resistor")
        ]
        if len(branches) >= 2:
            return CurrentDividerMotif(
                source_id=source.id,
                top_node=top_node,
                ground_node=graph.ground,
                branch_resistor_ids=branches,
            )
    return None


def _current_divider_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    motif: CurrentDividerMotif,
) -> list[TutorStep]:
    all_goals = [goal.id for goal in circuit.goals]
    branch_goal_ids = _goal_ids_for_target(circuit, set(motif.branch_resistor_ids))
    top_goal_ids = _goal_ids_for_target(circuit, {motif.top_node})
    branch_values = [
        common.requested_answer_for_goal(packet, goal_id)
        for goal_id in (branch_goal_ids or all_goals)
    ]
    return [
        TutorStep(
            id="current_divider_source",
            title="Anchor the current source and common node",
            body="The source injects current into a node shared by the parallel resistor branches.",
            look_at=f"Look at {motif.source_id}, node {motif.top_node}, and ground.",
            why_it_matters="A current divider starts with a known total current entering a shared node.",
            common_mistake="Treating the source current as if it flows through every branch in full.",
            focus=common.focus(
                circuit,
                components=[motif.source_id],
                nodes=[motif.top_node, motif.ground_node],
                current_paths=[motif.source_id],
                goals=top_goal_ids,
            ),
            verified_values=common.only_present(
                [common.node_voltage(packet, motif.top_node, "Common branch voltage")]
            ),
            next_action="Move from the common node into the parallel branches.",
        ),
        TutorStep(
            id="current_divider_parallel_branches",
            title="Compare the parallel branch paths",
            body="Each resistor connects across the same two nodes, so each branch sees the same voltage.",
            look_at="Look at the resistor branches between the common node and ground.",
            why_it_matters="The branch currents differ because the resistances differ, not because the branch voltage differs.",
            common_mistake="Dividing current equally without checking branch resistance.",
            focus=common.focus(
                circuit,
                components=motif.branch_resistor_ids,
                nodes=[motif.top_node, motif.ground_node],
                current_paths=motif.branch_resistor_ids,
            ),
            verified_values=common.only_present(
                [
                    common.component_current(packet, branch_id, f"{branch_id} current")
                    for branch_id in motif.branch_resistor_ids
                ]
            ),
            next_action="Read the requested branch currents and node voltage.",
        ),
        TutorStep(
            id="current_divider_requested_values",
            title="Read the current-divider answers",
            body="The requested node voltage and branch currents are extracted from the verified packet.",
            look_at="Look at the highlighted branches and requested goals.",
            why_it_matters="The answer belongs to a branch direction and reference node, not only a magnitude.",
            common_mistake="Forgetting the stated current direction through each resistor.",
            focus=common.focus(
                circuit,
                components=motif.branch_resistor_ids,
                nodes=[motif.top_node, motif.ground_node],
                current_paths=motif.branch_resistor_ids,
                goals=all_goals,
            ),
            verified_values=common.only_present(
                [
                    *branch_values,
                    *[common.requested_answer_for_goal(packet, goal_id) for goal_id in top_goal_ids],
                ]
            ),
            next_action="Check KCL: the branch currents should account for the source current.",
        ),
        common.verification_step(circuit, packet),
    ]


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


def _source_nodes(graph: CircuitGraph) -> list[str]:
    nodes = []
    for source in [*graph.voltage_sources_to_ground(), *graph.current_sources_to_ground()]:
        node = graph.source_node(source)
        if node is not None:
            nodes.append(node)
    return list(dict.fromkeys(nodes))


def _interior_nodes(circuit: CircuitProblem, graph: CircuitGraph) -> list[str]:
    source_node_ids = set(_source_nodes(graph))
    return [
        node
        for node in circuit.nodes
        if node != circuit.ground_node and node not in source_node_ids
    ]


def _relationship_focus(
    circuit: CircuitProblem,
    graph: CircuitGraph,
) -> tuple[list[str], list[str]]:
    nodes = _interior_nodes(circuit, graph) or [
        node for node in circuit.nodes if node != circuit.ground_node
    ]
    components = []
    for node in nodes:
        components.extend(component.id for component in graph.components_at(node))
    return list(dict.fromkeys(components)), nodes


def _bridge_coupling_components(graph: CircuitGraph) -> list[str]:
    source_node_ids = set(_source_nodes(graph))
    coupling = []
    for component in graph.components_of_type("resistor"):
        if len(component.nodes) != 2 or graph.ground in component.nodes:
            continue
        if any(node in source_node_ids for node in component.nodes):
            continue
        if all(len(graph.components_at(node)) >= 3 for node in component.nodes):
            coupling.append(component.id)
    return coupling


def _is_bridge_like(circuit: CircuitProblem, graph: CircuitGraph) -> bool:
    key = f"{circuit.topology_id or ''} {circuit.id}".lower()
    return "bridge" in key or bool(_bridge_coupling_components(graph))


def _source_reference_step(circuit: CircuitProblem, graph: CircuitGraph) -> TutorStep:
    source_components = common.source_ids(circuit)
    source_nodes = _source_nodes(graph)
    return TutorStep(
        id="dc_sources_and_ground",
        title="Identify sources and ground",
        body="Start by finding the reference node and the components that impose known currents or voltages.",
        look_at="Look at the sources, their non-ground terminals, and the ground node.",
        why_it_matters="These references define every node voltage and current sign used later.",
        common_mistake="Solving from a familiar pattern before checking the actual reference node.",
        focus=common.focus(
            circuit,
            components=source_components,
            nodes=[*source_nodes, circuit.ground_node],
            current_paths=source_components,
        ),
        verified_values=[],
        next_action="Use those anchors to decide which nodes must be solved together.",
    )


def _bridge_like_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
) -> list[TutorStep]:
    relationship_components, relationship_nodes = _relationship_focus(circuit, graph)
    coupling_components = _bridge_coupling_components(graph)
    target_components, target_nodes, goal_ids = _target_neighborhood(circuit, graph)
    all_goals = [goal.id for goal in circuit.goals]
    return [
        _source_reference_step(circuit, graph),
        TutorStep(
            id="dc_coupled_node_map",
            title="Map the coupled interior nodes",
            body=(
                "Cut the circuit around the interior nodes. The highlighted coupling branch means those "
                "node voltages must be solved together instead of as independent dividers."
            ),
            look_at="Look at the interior nodes and the branch that ties them together.",
            why_it_matters="A coupling branch lets the answer at one node depend on the neighboring node.",
            common_mistake="Using a divider shortcut on each side while ignoring the bridge branch.",
            focus=common.focus(
                circuit,
                components=relationship_components,
                nodes=relationship_nodes,
                current_paths=coupling_components or relationship_components,
            ),
            verified_values=[],
            next_action="Zoom into the requested node or bridge branch and write its current balance.",
        ),
        TutorStep(
            id="dc_target_kcl_neighborhood",
            title="Inspect the target KCL neighborhood",
            body="The requested value is controlled by the branches directly attached to the highlighted node or component.",
            look_at="Look at the target node or branch and the neighboring elements that set its current balance.",
            why_it_matters="This is where the symbolic KCL equation should be written before reading any number.",
            common_mistake="Reading a current direction without checking the requested from-node and to-node.",
            focus=common.focus(
                circuit,
                components=target_components,
                nodes=target_nodes,
                current_paths=target_components,
                goals=goal_ids,
            ),
            verified_values=[],
            next_action="After the node relationships are clear, read the verified requested values.",
        ),
        TutorStep(
            id="dc_requested_answer",
            title="Read the verified requested values",
            body="The requested values are taken from the solved and internally verified packet.",
            look_at="Look at the highlighted requested targets and the verified quantities below.",
            why_it_matters="The values belong to the stated node references and branch directions.",
            common_mistake="Copying a magnitude while losing the sign convention.",
            focus=common.focus(
                circuit,
                components=target_components,
                nodes=target_nodes,
                current_paths=target_components,
                goals=goal_ids or all_goals,
            ),
            verified_values=common.all_requested_observations(packet),
            next_action="Check the verification boundary.",
        ),
        common.verification_step(circuit, packet),
    ]


def _generic_dc_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
) -> list[TutorStep]:
    relationship_components, relationship_nodes = _relationship_focus(circuit, graph)
    target_components, target_nodes, goal_ids = _target_neighborhood(circuit, graph)
    return [
        _source_reference_step(circuit, graph),
        TutorStep(
            id="dc_node_relationships",
            title="Map the node relationships",
            body="Treat the highlighted non-reference nodes as unknowns connected by branch laws and KCL.",
            look_at="Look at how each highlighted branch connects one node voltage to another reference or node.",
            why_it_matters="For a general circuit, the explanation should follow the graph before choosing a shortcut.",
            common_mistake="Assuming series or parallel behavior without checking shared nodes.",
            focus=common.focus(
                circuit,
                components=relationship_components,
                nodes=relationship_nodes,
                current_paths=relationship_components,
            ),
            verified_values=[],
            next_action="Now narrow attention to the requested target neighborhood.",
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
