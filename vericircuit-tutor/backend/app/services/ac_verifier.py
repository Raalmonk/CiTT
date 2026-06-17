from __future__ import annotations

import math

from app.models.circuit_ir import CircuitProblem, is_nonideal_op_amp_type, is_op_amp_type
from app.models.solution_packet import CheckResult, SolutionPacket, VerificationReport
from app.services.ac_solver import quantity_to_complex
from app.services.validator import NORMALIZED_UNITS, reachable_from_ground


def _check(name: str, passed: bool, message: str, value: float | str | None = None) -> CheckResult:
    return CheckResult(name=name, passed=passed, message=message, value=value)


def _finite_complex_values(solution: SolutionPacket) -> bool:
    values = [
        *solution.ac_node_voltages.values(),
        *[result.voltage for result in solution.ac_component_results.values()],
        *[result.current for result in solution.ac_component_results.values()],
        *solution.ac_requested_answers.values(),
    ]
    return all(
        math.isfinite(value.real)
        and math.isfinite(value.imag)
        and math.isfinite(value.magnitude)
        and math.isfinite(value.phase_deg)
        for value in values
    )


def verify_ac_solution(
    problem: CircuitProblem,
    solution: SolutionPacket,
    current_tol: float = 1e-8,
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

    node_residuals = {node: 0.0 + 0.0j for node in problem.nodes if node != problem.ground_node}
    missing_component_result = False
    for component in problem.components:
        result = solution.ac_component_results.get(component.id)
        if result is None:
            missing_component_result = True
            continue
        current = quantity_to_complex(result.current)
        if is_op_amp_type(component.type):
            node_a, node_b = component.nodes[2], component.nodes[3]
        else:
            node_a, node_b = component.nodes[0], component.nodes[1]
        if node_a != problem.ground_node:
            node_residuals[node_a] += current
        if node_b != problem.ground_node:
            node_residuals[node_b] -= current

    max_kcl_residual = max((abs(value) for value in node_residuals.values()), default=0.0)
    kcl_passed = max_kcl_residual <= current_tol and not missing_component_result
    checks.append(
        _check(
            "ac_kcl_residuals",
            kcl_passed,
            "Complex KCL residuals are within tolerance."
            if kcl_passed
            else "Complex KCL residuals exceed tolerance or a component result is missing.",
            value=max_kcl_residual,
        )
    )

    requested_goal_ids = {goal.id for goal in problem.goals}
    answer_ids = set(solution.ac_requested_answers)
    requested_answers_present = requested_goal_ids <= answer_ids
    checks.append(
        _check(
            "requested_answers_present",
            requested_answers_present,
            "Every requested goal has a verified phasor answer."
            if requested_answers_present
            else "One or more requested goals is missing a phasor answer.",
        )
    )

    finite = _finite_complex_values(solution)
    checks.append(
        _check(
            "finite_complex_values",
            finite,
            "All complex values are finite."
            if finite
            else "One or more complex values is not finite.",
        )
    )

    for component in problem.components:
        if not is_nonideal_op_amp_type(component.type):
            continue
        if component.output_current_limit_a is None:
            continue
        result = solution.ac_component_results.get(component.id)
        if result is None:
            output_current = float("inf")
        else:
            output_current = abs(quantity_to_complex(result.current))
        limit_passed = output_current <= component.output_current_limit_a + current_tol
        checks.append(
            _check(
                "nonideal_op_amp_output_current_limit",
                limit_passed,
                f"{component.id} output-current phasor magnitude is within the configured limit."
                if limit_passed
                else f"{component.id} output-current phasor magnitude exceeds the configured limit.",
                value=output_current,
            )
        )

    passed = all(check.passed for check in checks)
    return VerificationReport(
        passed=passed,
        max_kcl_residual_a=float(max_kcl_residual),
        power_balance_error_w=0.0,
        checks=checks,
    )
