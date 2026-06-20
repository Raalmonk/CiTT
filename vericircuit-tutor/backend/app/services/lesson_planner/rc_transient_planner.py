from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, TutorObservation, TutorStep
from app.services.lesson_planner import common
from app.services.lesson_planner.graph import CircuitGraph
from app.services.lesson_planner.motifs import CircuitMotifs


def build_rc_transient_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
    _motifs: CircuitMotifs,
) -> list[TutorStep]:
    response = packet.transient_response
    if response is None:
        return _generic_rc_steps(circuit, packet, graph)
    if not response.is_first_order or response.time_constant_s <= 0:
        return _generic_rc_steps(circuit, packet, graph)

    capacitor_id = response.capacitor_id
    capacitor = graph.component(capacitor_id)
    capacitor_nodes = capacitor.nodes if capacitor else [response.positive_node, response.negative_node]
    resistor_id = _resistor_connected_to_capacitor(graph, capacitor_id)
    time_constant = common.packet_observation(packet, "time_constant") or TutorObservation(
        id="time_constant",
        label="Time constant",
        value=float(response.time_constant_s),
        unit="s",
        note="Computed by the deterministic RC transient solver.",
    )

    return [
        TutorStep(
            id="rc_initial_condition",
            title="Identify the capacitor and initial condition",
            body="A first-order RC transient starts from the capacitor voltage at t = 0+.",
            look_at=f"Look at {capacitor_id} and its two terminals.",
            why_it_matters="The capacitor voltage cannot jump instantly, so the initial voltage anchors the curve.",
            common_mistake="Starting with the final value and forgetting the initial capacitor condition.",
            focus=common.focus(
                circuit,
                components=[capacitor_id],
                nodes=capacitor_nodes,
                goals=[goal.id for goal in circuit.goals if goal.target == capacitor_id],
            ),
            verified_values=[
                TutorObservation(
                    id="initial_capacitor_voltage",
                    label="Initial capacitor voltage",
                    value=float(response.initial_voltage_v),
                    unit="V",
                    note="Initial condition from the RC transient packet.",
                )
            ],
            next_action="Find the final DC value the capacitor moves toward.",
        ),
        TutorStep(
            id="rc_final_value",
            title="Find the final DC value",
            body="After a long time, the capacitor approaches the solved final voltage.",
            look_at="Look at the same capacitor terminals, now as the long-time endpoint.",
            why_it_matters="The transient is motion from the initial value toward the final value.",
            common_mistake="Using the source voltage directly when the final capacitor voltage is set by the whole network.",
            focus=common.focus(circuit, components=[capacitor_id], nodes=capacitor_nodes),
            verified_values=[
                TutorObservation(
                    id="final_capacitor_voltage",
                    label="Final capacitor voltage",
                    value=float(response.final_voltage_v),
                    unit="V",
                    note="Final value from the RC transient packet.",
                )
            ],
            next_action="Use the resistance seen by the capacitor to get tau.",
        ),
        TutorStep(
            id="rc_time_constant",
            title="Compute the time constant",
            body="The time constant tau is R seen by the capacitor times C.",
            look_at="Look at the resistor path that charges or discharges the capacitor.",
            why_it_matters="Tau sets the time scale of the exponential response.",
            common_mistake="Using any resistor in the drawing instead of the resistance seen by the capacitor.",
            focus=common.focus(
                circuit,
                components=[item for item in [resistor_id, capacitor_id] if item],
                nodes=capacitor_nodes,
                current_paths=[item for item in [resistor_id] if item],
            ),
            verified_values=[
                TutorObservation(
                    id="thevenin_resistance",
                    label="Resistance seen by capacitor",
                    value=float(response.resistance_ohm),
                    unit="ohm",
                    note="Deterministic RC transient solver result.",
                ),
                time_constant,
            ],
            next_action="Read the exponential response samples.",
        ),
        TutorStep(
            id="rc_exponential_motion",
            title="Read the exponential motion",
            body="The curve moves from initial to final with the time constant tau.",
            look_at="Keep the capacitor highlighted while reading the time-domain answer.",
            why_it_matters="This explains the shape of the curve, not just one final number.",
            common_mistake="Expecting a linear ramp in a first-order RC circuit.",
            focus=common.focus(
                circuit,
                components=[capacitor_id],
                nodes=capacitor_nodes,
                goals=[goal.id for goal in circuit.goals],
            ),
            verified_values=common.all_requested_observations(packet)
            or common.only_present([common.packet_observation(packet, "tau_marker_voltage")]),
            next_action="Check the verification boundary.",
        ),
        common.verification_step(circuit, packet),
    ]


def _resistor_connected_to_capacitor(graph: CircuitGraph, capacitor_id: str) -> str | None:
    capacitor = graph.component(capacitor_id)
    if capacitor is None:
        return None
    for node in capacitor.nodes:
        for component in graph.components_at(node):
            if component.type == "resistor":
                return component.id
    return None


def _generic_rc_steps(
    circuit: CircuitProblem,
    packet: SolutionPacket,
    graph: CircuitGraph,
) -> list[TutorStep]:
    component_focus, node_focus, goal_ids = common.goal_focus_ids(circuit)
    if not component_focus:
        component_focus = [component.id for component in graph.components_of_type("capacitor")]
    return [
        TutorStep(
            id="rc_requested_target",
            title="Identify the transient target",
            body="The transient lesson starts from the capacitor or requested target.",
            look_at="Look at the highlighted capacitor or requested branch.",
            why_it_matters="The state variables determine the shape of the time-domain response.",
            common_mistake="Treating a transient result like a static DC answer.",
            focus=common.focus(circuit, components=component_focus, nodes=node_focus, goals=goal_ids),
            verified_values=common.all_requested_observations(packet),
            next_action="Check the verification boundary.",
        ),
        common.verification_step(circuit, packet),
    ]
