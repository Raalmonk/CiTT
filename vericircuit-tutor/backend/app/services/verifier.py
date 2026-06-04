from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import CheckResult, SolutionPacket, VerificationReport
from app.services.validator import NORMALIZED_UNITS, reachable_from_ground


def _check(name: str, passed: bool, message: str, value: float | str | None = None) -> CheckResult:
    return CheckResult(name=name, passed=passed, message=message, value=value)


def verify_solution(
    problem: CircuitProblem,
    solution: SolutionPacket,
    current_tol: float = 1e-8,
    power_tol: float = 1e-8,
) -> VerificationReport:
    checks: list[CheckResult] = []

    ground_exists = problem.ground_node in problem.nodes
    checks.append(
        _check(
            "ground_exists",
            ground_exists,
            f"Ground node {problem.ground_node!r} is present."
            if ground_exists
            else "Ground node is missing.",
        )
    )

    nodes_valid = all(
        node in problem.nodes for component in problem.components for node in component.nodes
    )
    checks.append(
        _check(
            "component_nodes_valid",
            nodes_valid,
            "All component nodes appear in the Circuit IR node list.",
        )
    )

    reachable = reachable_from_ground(problem)
    connected = all(
        node in reachable
        for component in problem.components
        for node in component.nodes
        if node != problem.ground_node
    )
    checks.append(
        _check(
            "graph_connected_to_ground",
            connected,
            "All component nodes are in the ground-connected graph.",
            value=len(reachable),
        )
    )

    units_normalized = all(
        component.unit == NORMALIZED_UNITS.get(component.type)
        for component in problem.components
    )
    checks.append(
        _check(
            "units_normalized",
            units_normalized,
            "Component values use normalized SI units.",
        )
    )

    node_residuals = {node: 0.0 for node in problem.nodes if node != problem.ground_node}
    for component in problem.components:
        result = solution.component_results.get(component.id)
        if result is None:
            continue
        current = result.current.value
        node_a, node_b = component.nodes
        if node_a != problem.ground_node:
            node_residuals[node_a] += current
        if node_b != problem.ground_node:
            node_residuals[node_b] -= current

    max_kcl_residual = max((abs(value) for value in node_residuals.values()), default=0.0)
    kcl_passed = max_kcl_residual <= current_tol
    checks.append(
        _check(
            "kcl_residuals",
            kcl_passed,
            "KCL residuals are within tolerance."
            if kcl_passed
            else "KCL residuals exceed tolerance.",
            value=max_kcl_residual,
        )
    )

    signed_power_sum = sum(
        result.power.value for result in solution.component_results.values()
    )
    power_balance_error = abs(signed_power_sum)
    power_passed = power_balance_error <= power_tol
    checks.append(
        _check(
            "power_balance",
            power_passed,
            "Signed component powers sum to zero within tolerance."
            if power_passed
            else "Power supplied and absorbed do not balance within tolerance.",
            value=power_balance_error,
        )
    )

    requested_goal_ids = {goal.id for goal in problem.goals}
    answer_ids = set(solution.requested_answers)
    requested_answers_present = requested_goal_ids <= answer_ids
    checks.append(
        _check(
            "requested_answers_present",
            requested_answers_present,
            "Every requested goal has a verified answer."
            if requested_answers_present
            else "One or more requested goals is missing an answer.",
        )
    )

    passed = all(check.passed for check in checks)
    return VerificationReport(
        passed=passed,
        max_kcl_residual_a=float(max_kcl_residual),
        power_balance_error_w=float(power_balance_error),
        checks=checks,
    )

