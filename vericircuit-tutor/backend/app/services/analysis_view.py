from __future__ import annotations

from app.models.analysis_view import (
    AnalysisView,
    ComponentFlow,
    NodeKclReport,
    NodeKclTerm,
)
from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import SolutionPacket


KCL_TOLERANCE_A = 1e-8
ZERO_CURRENT_TOLERANCE_A = 1e-12
BLOCKED_REASON = "Analysis view is unavailable because the solution is not verified."


def _direction_for_current(component: Component, current_a: float) -> tuple[str, str, bool]:
    if current_a > ZERO_CURRENT_TOLERANCE_A:
        return component.nodes[0], component.nodes[1], False
    if current_a < -ZERO_CURRENT_TOLERANCE_A:
        return component.nodes[1], component.nodes[0], False
    return component.nodes[0], component.nodes[1], True


def _kcl_direction(signed_current_leaving_a: float) -> str:
    if signed_current_leaving_a > ZERO_CURRENT_TOLERANCE_A:
        return "leaving"
    if signed_current_leaving_a < -ZERO_CURRENT_TOLERANCE_A:
        return "entering"
    return "zero"


def _other_node(component: Component, node: str) -> str:
    if node == component.nodes[0]:
        return component.nodes[1]
    return component.nodes[0]


def build_analysis_view(circuit: CircuitProblem, packet: SolutionPacket) -> AnalysisView:
    badge = packet.verification_badge.label
    if badge != "PASS":
        return AnalysisView(
            status="blocked",
            badge=badge,
            reason=BLOCKED_REASON,
            component_flows={},
            node_kcl={},
        )

    component_flows: dict[str, ComponentFlow] = {}
    for component in circuit.components:
        result = packet.component_results[component.id]
        current_a = result.current.value
        direction_from, direction_to, is_zero_current = _direction_for_current(
            component,
            current_a,
        )
        component_flows[component.id] = ComponentFlow(
            component_id=component.id,
            component_type=component.type,
            nodes=component.nodes,
            current_a=current_a,
            abs_current_a=abs(current_a),
            direction_from=direction_from,
            direction_to=direction_to,
            voltage_v=result.voltage.value,
            power_w=result.power.value,
            is_zero_current=is_zero_current,
            sign_convention=result.sign_convention,
        )

    node_kcl: dict[str, NodeKclReport] = {}
    for node in circuit.nodes:
        terms: list[NodeKclTerm] = []
        sum_leaving_a = 0.0
        for component in circuit.components:
            if node not in component.nodes:
                continue

            current_a = packet.component_results[component.id].current.value
            signed_current_leaving_a = current_a if node == component.nodes[0] else -current_a
            direction = _kcl_direction(signed_current_leaving_a)
            terms.append(
                NodeKclTerm(
                    component_id=component.id,
                    other_node=_other_node(component, node),
                    signed_current_leaving_a=signed_current_leaving_a,
                    abs_current_a=abs(signed_current_leaving_a),
                    direction=direction,  # type: ignore[arg-type]
                    description=(
                        f"{component.id}: {direction} relative to node {node} "
                        "using positive current from nodes[0] to nodes[1]."
                    ),
                )
            )
            sum_leaving_a += signed_current_leaving_a

        residual_a = abs(sum_leaving_a)
        node_kcl[node] = NodeKclReport(
            node=node,
            voltage_v=packet.node_voltages.get(node, 0.0),
            terms=terms,
            sum_leaving_a=sum_leaving_a,
            residual_a=residual_a,
            passed=residual_a <= KCL_TOLERANCE_A,
        )

    return AnalysisView(
        status="available",
        badge=badge,
        reason=None,
        component_flows=component_flows,
        node_kcl=node_kcl,
    )
