from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models.circuit_ir import CircuitProblem, Component, is_op_amp_type
from app.models.solution_packet import CalculationTrace, ComponentResult, QuantityValue, SolutionPacket, VerificationBadge
from app.services.mna_solver import SOURCE_SIGN_CONVENTION, solve_mna
from app.services.netlist_generator import generate_netlist
from app.services.validator import validate_circuit
from app.services.verifier import verify_solution


@dataclass
class IncrementalSolveResult:
    success: bool
    message: str
    packet: SolutionPacket | None = None
    incremental_used: bool = False


def solve_resistor_update_incremental(
    problem: CircuitProblem,
    *,
    component_id: str,
    new_value: float,
) -> IncrementalSolveResult:
    if problem.analysis_type != "dc_operating_point":
        return IncrementalSolveResult(
            success=False,
            message="Incremental update currently supports DC operating-point resistor edits only.",
        )
    if any(is_op_amp_type(component.type) for component in problem.components):
        return IncrementalSolveResult(
            success=False,
            message="Incremental update currently skips op-amp circuits because their extra constraints need a dedicated sensitivity path.",
        )
    if any(component.type == "diode" for component in problem.components):
        return IncrementalSolveResult(
            success=False,
            message="Incremental update currently skips nonlinear diode circuits; use the Newton-Raphson full solve path.",
        )
    component = next((item for item in problem.components if item.id == component_id), None)
    if component is None:
        return IncrementalSolveResult(success=False, message=f"Component {component_id!r} not found.")
    if component.type != "resistor":
        return IncrementalSolveResult(
            success=False,
            message="Incremental update currently supports resistor value changes only.",
        )
    if new_value <= 0:
        return IncrementalSolveResult(success=False, message="New resistor value must be positive.")

    validation = validate_circuit(problem)
    if not validation.valid or validation.circuit is None:
        return IncrementalSolveResult(
            success=False,
            message="Original circuit failed validation and cannot be incrementally updated.",
        )
    original = solve_mna(validation.circuit)
    if not original.success:
        return IncrementalSolveResult(
            success=False,
            message=original.message or "Original circuit could not be solved.",
        )

    trace = original.calculation_trace
    matrix = np.array(trace.mna_matrix, dtype=float)
    solution = np.array(trace.solution_vector, dtype=float)
    if matrix.size == 0 or solution.size == 0:
        return IncrementalSolveResult(
            success=False,
            message="Original solve trace does not contain an MNA matrix and solution vector.",
        )

    unknown_index = {name: idx for idx, name in enumerate(trace.unknown_order)}
    update_vector = np.zeros(matrix.shape[0], dtype=float)
    node_a, node_b = component.nodes[0], component.nodes[1]
    idx_a = unknown_index.get(f"V({node_a})")
    idx_b = unknown_index.get(f"V({node_b})")
    if idx_a is not None:
        update_vector[idx_a] += 1.0
    if idx_b is not None:
        update_vector[idx_b] -= 1.0
    if not np.any(update_vector):
        return IncrementalSolveResult(
            success=False,
            message="Resistor update has no non-ground voltage sensitivity in this circuit.",
        )

    delta_conductance = 1.0 / new_value - 1.0 / component.value
    try:
        sensitivity = np.linalg.solve(matrix, update_vector)
    except np.linalg.LinAlgError as exc:
        return IncrementalSolveResult(
            success=False,
            message=f"Could not compute Sherman-Morrison sensitivity: {exc}",
        )

    denominator = 1.0 + delta_conductance * float(update_vector @ sensitivity)
    if abs(denominator) <= 1e-15:
        return IncrementalSolveResult(
            success=False,
            message="Sherman-Morrison update is singular for this resistor change.",
        )
    updated_solution = solution - (
        delta_conductance
        * sensitivity
        * float(update_vector @ solution)
        / denominator
    )

    updated_problem = validation.circuit.model_copy(deep=True)
    updated_component = next(item for item in updated_problem.components if item.id == component_id)
    updated_component.value = float(new_value)
    packet = _packet_from_solution(updated_problem, trace, matrix, updated_solution)
    verification = verify_solution(updated_problem, packet)
    packet.verification = verification
    packet.verification_badge = VerificationBadge(
        label="PASS" if verification.passed else "FAIL",
        message=(
            "Incremental Sherman-Morrison resistor update passed verification."
            if verification.passed
            else "Incremental resistor update produced a packet, but verification failed."
        ),
    )
    return IncrementalSolveResult(
        success=verification.passed,
        message=packet.verification_badge.message,
        packet=packet,
        incremental_used=True,
    )


def _packet_from_solution(
    problem: CircuitProblem,
    original_trace: CalculationTrace,
    matrix: np.ndarray,
    solution: np.ndarray,
) -> SolutionPacket:
    ground = problem.ground_node
    unknown_index = {name: idx for idx, name in enumerate(original_trace.unknown_order)}
    node_voltages = {ground: 0.0}
    for node in problem.nodes:
        idx = unknown_index.get(f"V({node})")
        if idx is not None:
            node_voltages[node] = float(solution[idx])

    component_results: dict[str, ComponentResult] = {}
    for component in problem.components:
        voltage = node_voltages[component.nodes[0]] - node_voltages[component.nodes[1]]
        if component.type == "resistor":
            current = voltage / component.value
            sign = (
                "Passive sign convention: current is positive from nodes[0] "
                "to nodes[1], and resistor power is absorbed when positive."
            )
        elif component.type == "capacitor":
            current = 0.0
            sign = (
                "DC operating point: ideal capacitor is treated as an open circuit. "
                "Voltage is V(nodes[0]) - V(nodes[1]); current is 0 A."
            )
        elif component.type == "inductor":
            current = float(solution[unknown_index[f"I({component.id})"]])
            sign = (
                "DC operating point: ideal inductor is treated as a short circuit. "
                "Voltage is constrained to 0 V; current is positive from nodes[0] to nodes[1]."
            )
        elif component.type == "voltage_source":
            current = float(solution[unknown_index[f"I({component.id})"]])
            sign = SOURCE_SIGN_CONVENTION
        elif component.type == "current_source":
            current = component.value
            sign = SOURCE_SIGN_CONVENTION
        else:
            current = 0.0
            sign = "Unsupported in incremental result derivation."
        component_results[component.id] = ComponentResult(
            voltage=_quantity(
                voltage,
                "V",
                {"positive_node": component.nodes[0], "negative_node": component.nodes[1]},
            ),
            current=_quantity(
                current,
                "A",
                {"from_node": component.nodes[0], "to_node": component.nodes[1]},
            ),
            power=_quantity(voltage * current, "W", {"component": component.id}),
            sign_convention=sign,
        )

    requested_answers = {}
    for goal in problem.goals:
        if goal.quantity == "node_voltage":
            requested_answers[goal.id] = _quantity(
                node_voltages[goal.target],
                "V",
                {"positive_node": goal.target, "negative_node": ground},
            )
        elif goal.target in component_results:
            result = component_results[goal.target]
            if goal.quantity == "component_voltage":
                requested_answers[goal.id] = result.voltage
            elif goal.quantity == "component_current":
                requested_answers[goal.id] = result.current
            elif goal.quantity in {"component_power", "source_power"}:
                requested_answers[goal.id] = result.power

    trace = original_trace.model_copy(
        update={
            "solver_name": "internal_mna_incremental_v1",
            "solver_method": "Sherman-Morrison rank-1 resistor conductance update",
            "mna_matrix": matrix.tolist(),
            "solution_vector": solution.tolist(),
            "answer_source": "incremental_solver",
        }
    )
    return SolutionPacket(
        circuit_id=problem.id,
        status="solved",
        node_voltages=node_voltages,
        component_results=component_results,
        requested_answers=requested_answers,
        calculation_trace=trace,
        generated_netlist=generate_netlist(problem),
        assumptions_used=problem.assumptions,
        bme_metadata=problem.bme_metadata,
    )


def _quantity(value: float, unit: str, reference: dict[str, str]) -> QuantityValue:
    return QuantityValue(value=float(value), unit=unit, reference=reference)
