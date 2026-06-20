from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from app.models.circuit_ir import CircuitProblem, Component, is_nonideal_op_amp_type, is_op_amp_type
from app.models.solution_packet import CalculationTrace, ComponentResult, QuantityValue
from app.services.mna_solver import (
    SOURCE_SIGN_CONVENTION,
    nonideal_open_loop_gain,
)


DEFAULT_DIODE_IS_A = 1e-12
DEFAULT_DIODE_N = 1.0
DEFAULT_THERMAL_VOLTAGE_V = 0.025852
NEWTON_TOL = 1e-10
NEWTON_MAX_ITERATIONS = 500


@dataclass
class NonlinearSolveResult:
    success: bool
    message: str | None = None
    node_voltages: dict[str, float] = field(default_factory=dict)
    component_results: dict[str, ComponentResult] = field(default_factory=dict)
    requested_answers: dict[str, QuantityValue] = field(default_factory=dict)
    calculation_trace: CalculationTrace = field(default_factory=CalculationTrace)
    warnings: list[str] = field(default_factory=list)
    iterations: int = 0


def _quantity(
    value: float,
    unit: str,
    explanation_key: str | None = None,
    reference: dict[str, str] | None = None,
) -> QuantityValue:
    return QuantityValue(
        value=float(value),
        unit=unit,
        explanation_key=explanation_key,
        reference=reference,
    )


def _stamp_conductance(
    matrix: np.ndarray,
    node_index: dict[str, int],
    node_a: str,
    node_b: str,
    conductance: float,
) -> None:
    idx_a = node_index.get(node_a)
    idx_b = node_index.get(node_b)
    if idx_a is not None:
        matrix[idx_a, idx_a] += conductance
    if idx_b is not None:
        matrix[idx_b, idx_b] += conductance
    if idx_a is not None and idx_b is not None:
        matrix[idx_a, idx_b] -= conductance
        matrix[idx_b, idx_a] -= conductance


def _node_value(node: str, ground: str, node_index: dict[str, int], solution: np.ndarray) -> float:
    if node == ground:
        return 0.0
    return float(solution[node_index[node]])


def _diode_params(component: Component) -> tuple[float, float, float]:
    saturation_current = component.saturation_current_a or DEFAULT_DIODE_IS_A
    emission = component.emission_coefficient or DEFAULT_DIODE_N
    thermal_voltage = component.thermal_voltage_v or DEFAULT_THERMAL_VOLTAGE_V
    return float(saturation_current), float(emission), float(thermal_voltage)


def _diode_current_and_conductance(component: Component, voltage: float) -> tuple[float, float]:
    saturation_current, emission, thermal_voltage = _diode_params(component)
    scale = emission * thermal_voltage
    exponent = max(min(voltage / scale, 80.0), -80.0)
    exp_value = math.exp(exponent)
    current = saturation_current * (exp_value - 1.0)
    conductance = saturation_current * exp_value / scale
    return current, conductance


def _stamp_linear_network(
    problem: CircuitProblem,
    node_index: dict[str, int],
    voltage_source_index: dict[str, int],
    inductor_index: dict[str, int],
    op_amp_index: dict[str, int],
    size: int,
) -> tuple[np.ndarray, np.ndarray, str | None]:
    matrix = np.zeros((size, size), dtype=float)
    rhs = np.zeros(size, dtype=float)

    for component in problem.components:
        node_a, node_b = component.nodes[0], component.nodes[1]
        idx_a = node_index.get(node_a)
        idx_b = node_index.get(node_b)

        if component.type == "resistor":
            _stamp_conductance(matrix, node_index, node_a, node_b, 1.0 / component.value)
        elif component.type == "capacitor":
            continue
        elif component.type == "diode":
            # Nonlinear stamp is added in the Newton loop.
            continue
        elif component.type == "inductor":
            branch_idx = inductor_index[component.id]
            if idx_a is not None:
                matrix[idx_a, branch_idx] += 1.0
                matrix[branch_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, branch_idx] -= 1.0
                matrix[branch_idx, idx_b] -= 1.0
        elif component.type == "current_source":
            if idx_a is not None:
                rhs[idx_a] -= component.value
            if idx_b is not None:
                rhs[idx_b] += component.value
        elif component.type == "voltage_source":
            branch_idx = voltage_source_index[component.id]
            if idx_a is not None:
                matrix[idx_a, branch_idx] += 1.0
                matrix[branch_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, branch_idx] -= 1.0
                matrix[branch_idx, idx_b] -= 1.0
            rhs[branch_idx] = component.value
        elif is_op_amp_type(component.type):
            vp, vm, out, ref = component.nodes
            branch_idx = op_amp_index[component.id]
            idx_vp = node_index.get(vp)
            idx_vm = node_index.get(vm)
            idx_out = node_index.get(out)
            idx_ref = node_index.get(ref)
            if component.input_resistance_ohm is not None:
                _stamp_conductance(
                    matrix,
                    node_index,
                    vp,
                    vm,
                    1.0 / component.input_resistance_ohm,
                )
            if idx_out is not None:
                matrix[idx_out, branch_idx] += 1.0
            if idx_ref is not None:
                matrix[idx_ref, branch_idx] -= 1.0
            if is_nonideal_op_amp_type(component.type):
                output_resistance = component.output_resistance_ohm
                gain = nonideal_open_loop_gain(component)
                offset = component.input_offset_voltage_v or 0.0
                if output_resistance is not None:
                    output_conductance = 1.0 / output_resistance
                    gm = gain * output_conductance
                    if idx_out is not None:
                        matrix[branch_idx, idx_out] -= output_conductance
                    if idx_ref is not None:
                        matrix[branch_idx, idx_ref] += output_conductance
                    if idx_vp is not None:
                        matrix[branch_idx, idx_vp] += gm
                    if idx_vm is not None:
                        matrix[branch_idx, idx_vm] -= gm
                    matrix[branch_idx, branch_idx] += 1.0
                    rhs[branch_idx] = -gm * offset
                else:
                    if idx_out is not None:
                        matrix[branch_idx, idx_out] += 1.0
                    if idx_ref is not None:
                        matrix[branch_idx, idx_ref] -= 1.0
                    if idx_vp is not None:
                        matrix[branch_idx, idx_vp] -= gain
                    if idx_vm is not None:
                        matrix[branch_idx, idx_vm] += gain
                    rhs[branch_idx] = gain * offset
            else:
                if idx_vp is not None:
                    matrix[branch_idx, idx_vp] += 1.0
                if idx_vm is not None:
                    matrix[branch_idx, idx_vm] -= 1.0
        else:
            return matrix, rhs, f"Unsupported component type {component.type!r} reached nonlinear solver."

    return matrix, rhs, None


def _residual_and_jacobian(
    problem: CircuitProblem,
    base_matrix: np.ndarray,
    base_rhs: np.ndarray,
    node_index: dict[str, int],
    solution: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    residual = base_matrix @ solution - base_rhs
    jacobian = np.array(base_matrix, dtype=float)
    ground = problem.ground_node

    for component in problem.components:
        if component.type != "diode":
            continue
        anode, cathode = component.nodes
        idx_a = node_index.get(anode)
        idx_b = node_index.get(cathode)
        voltage = (
            _node_value(anode, ground, node_index, solution)
            - _node_value(cathode, ground, node_index, solution)
        )
        current, conductance = _diode_current_and_conductance(component, voltage)
        if idx_a is not None:
            residual[idx_a] += current
            jacobian[idx_a, idx_a] += conductance
        if idx_b is not None:
            residual[idx_b] -= current
            jacobian[idx_b, idx_b] += conductance
        if idx_a is not None and idx_b is not None:
            jacobian[idx_a, idx_b] -= conductance
            jacobian[idx_b, idx_a] -= conductance

    return residual, jacobian


def _build_requested_answers(
    problem: CircuitProblem,
    node_voltages: dict[str, float],
    component_results: dict[str, ComponentResult],
) -> dict[str, QuantityValue]:
    answers: dict[str, QuantityValue] = {}
    components_by_id = {component.id: component for component in problem.components}
    for goal in problem.goals:
        key = f"{goal.quantity}:{goal.target}"
        if goal.quantity == "node_voltage":
            answers[goal.id] = _quantity(
                node_voltages[goal.target],
                "V",
                explanation_key=key,
                reference={"positive_node": goal.target, "negative_node": problem.ground_node},
            )
            continue
        component = components_by_id[goal.target]
        result = component_results[goal.target]
        if goal.quantity == "component_voltage":
            if goal.reference and {"positive_node", "negative_node"} <= set(goal.reference):
                positive = str(goal.reference["positive_node"])
                negative = str(goal.reference["negative_node"])
                answers[goal.id] = _quantity(
                    node_voltages[positive] - node_voltages[negative],
                    "V",
                    explanation_key=key,
                    reference={"positive_node": positive, "negative_node": negative},
                )
            else:
                answers[goal.id] = result.voltage
        elif goal.quantity == "component_current":
            answers[goal.id] = result.current
        elif goal.quantity in {"component_power", "source_power"}:
            answers[goal.id] = result.power
    return answers


def solve_nonlinear_dc(problem: CircuitProblem) -> NonlinearSolveResult:
    ground = problem.ground_node
    non_ground_nodes = [node for node in problem.nodes if node != ground]
    node_index = {node: idx for idx, node in enumerate(non_ground_nodes)}
    voltage_sources = [
        component for component in problem.components if component.type == "voltage_source"
    ]
    inductors = [component for component in problem.components if component.type == "inductor"]
    op_amps = [component for component in problem.components if is_op_amp_type(component.type)]
    voltage_source_index = {
        component.id: len(non_ground_nodes) + idx
        for idx, component in enumerate(voltage_sources)
    }
    inductor_index = {
        component.id: len(non_ground_nodes) + len(voltage_sources) + idx
        for idx, component in enumerate(inductors)
    }
    op_amp_index = {
        component.id: len(non_ground_nodes) + len(voltage_sources) + len(inductors) + idx
        for idx, component in enumerate(op_amps)
    }
    unknown_order = [
        *(f"V({node})" for node in non_ground_nodes),
        *(f"I({component.id})" for component in voltage_sources),
        *(f"I({component.id})" for component in inductors),
        *(f"I({component.id}_out)" for component in op_amps),
    ]
    size = len(unknown_order)
    trace = CalculationTrace(
        solver_name="internal_nonlinear_mna_v1",
        solver_method="Newton-Raphson nonlinear MNA with Shockley diode Jacobian",
        solver_backend="numpy.linalg.solve",
        answer_source="nonlinear_solver",
        verification_source="verifier.py",
        unknown_order=unknown_order,
    )
    if size == 0:
        return NonlinearSolveResult(
            success=False,
            message="Circuit has no unknowns to solve.",
            calculation_trace=trace,
        )

    base_matrix, base_rhs, error = _stamp_linear_network(
        problem,
        node_index,
        voltage_source_index,
        inductor_index,
        op_amp_index,
        size,
    )
    if error is not None:
        return NonlinearSolveResult(
            success=False,
            message=error,
            calculation_trace=trace.model_copy(
                update={"mna_matrix": base_matrix.tolist(), "rhs_vector": base_rhs.tolist()}
            ),
        )

    try:
        solution = np.linalg.solve(base_matrix, base_rhs)
    except np.linalg.LinAlgError:
        solution = np.zeros(size, dtype=float)

    final_residual = np.zeros(size, dtype=float)
    final_jacobian = np.array(base_matrix, dtype=float)
    for iteration in range(1, NEWTON_MAX_ITERATIONS + 1):
        residual, jacobian = _residual_and_jacobian(
            problem,
            base_matrix,
            base_rhs,
            node_index,
            solution,
        )
        final_residual = residual
        final_jacobian = jacobian
        residual_norm = float(np.linalg.norm(residual, ord=np.inf))
        if residual_norm <= NEWTON_TOL:
            break
        try:
            delta = np.linalg.solve(jacobian, -residual)
        except np.linalg.LinAlgError as exc:
            trace = trace.model_copy(
                update={
                    "mna_matrix": jacobian.tolist(),
                    "rhs_vector": (-residual).tolist(),
                    "solution_vector": solution.tolist(),
                }
            )
            return NonlinearSolveResult(
                success=False,
                message=f"Newton-Raphson Jacobian is singular or ill-conditioned: {exc}",
                calculation_trace=trace,
                iterations=iteration,
            )
        step = 1.0
        best_solution = solution + delta
        best_norm = math.inf
        for _ in range(12):
            candidate = solution + step * delta
            candidate_residual, _ = _residual_and_jacobian(
                problem,
                base_matrix,
                base_rhs,
                node_index,
                candidate,
            )
            candidate_norm = float(np.linalg.norm(candidate_residual, ord=np.inf))
            if candidate_norm < best_norm:
                best_norm = candidate_norm
                best_solution = candidate
            if candidate_norm < residual_norm:
                break
            step *= 0.5
        solution = best_solution
    else:
        trace = trace.model_copy(
            update={
                "mna_matrix": final_jacobian.tolist(),
                "rhs_vector": (-final_residual).tolist(),
                "solution_vector": solution.tolist(),
            }
        )
        return NonlinearSolveResult(
            success=False,
            message=(
                "Newton-Raphson nonlinear MNA did not converge within "
                f"{NEWTON_MAX_ITERATIONS} iterations."
            ),
            calculation_trace=trace,
            iterations=NEWTON_MAX_ITERATIONS,
        )

    trace = trace.model_copy(
        update={
            "mna_matrix": final_jacobian.tolist(),
            "rhs_vector": (-final_residual).tolist(),
            "solution_vector": solution.tolist(),
        }
    )

    node_voltages = {ground: 0.0}
    for node, idx in node_index.items():
        node_voltages[node] = float(solution[idx])

    component_results: dict[str, ComponentResult] = {}
    for component in problem.components:
        if is_op_amp_type(component.type):
            voltage = node_voltages[component.nodes[2]] - node_voltages[component.nodes[3]]
        else:
            voltage = node_voltages[component.nodes[0]] - node_voltages[component.nodes[1]]

        if component.type == "resistor":
            current = voltage / component.value
            sign = (
                "Passive sign convention: current is positive from nodes[0] "
                "to nodes[1], and resistor power is absorbed when positive."
            )
        elif component.type == "capacitor":
            current = 0.0
            sign = "DC operating point: ideal capacitor is treated as an open circuit."
        elif component.type == "inductor":
            current = float(solution[inductor_index[component.id]])
            sign = "DC operating point: ideal inductor is treated as a short circuit."
        elif component.type == "current_source":
            current = component.value
            sign = SOURCE_SIGN_CONVENTION
        elif component.type == "voltage_source":
            current = float(solution[voltage_source_index[component.id]])
            sign = SOURCE_SIGN_CONVENTION
        elif component.type == "diode":
            current, _ = _diode_current_and_conductance(component, voltage)
            sign = (
                "Shockley diode model: current is positive from anode nodes[0] "
                "to cathode nodes[1]. Newton-Raphson stamps the local dynamic conductance."
            )
        elif is_op_amp_type(component.type):
            current = float(solution[op_amp_index[component.id]])
            if is_nonideal_op_amp_type(component.type) and component.output_resistance_ohm is not None:
                sign = (
                    "Nonideal op-amp macromodel: output port is a VCCS plus finite output "
                    "resistance; current is positive from output to reference."
                )
            elif is_nonideal_op_amp_type(component.type):
                sign = (
                    "Nonideal op-amp model: voltage is V(output) - V(reference), "
                    "output current is positive from output to reference."
                )
            else:
                sign = "Ideal op-amp output current is positive from output to reference."
        else:
            return NonlinearSolveResult(
                success=False,
                message=f"Unsupported component type {component.type!r} reached result derivation.",
                calculation_trace=trace,
            )

        reference = (
            {"positive_node": component.nodes[2], "negative_node": component.nodes[3]}
            if is_op_amp_type(component.type)
            else {"positive_node": component.nodes[0], "negative_node": component.nodes[1]}
        )
        current_reference = (
            {"from_node": component.nodes[2], "to_node": component.nodes[3]}
            if is_op_amp_type(component.type)
            else {"from_node": component.nodes[0], "to_node": component.nodes[1]}
        )
        component_results[component.id] = ComponentResult(
            voltage=_quantity(voltage, "V", reference=reference),
            current=_quantity(current, "A", reference=current_reference),
            power=_quantity(voltage * current, "W", reference={"component": component.id}),
            sign_convention=sign,
        )

    requested_answers = _build_requested_answers(problem, node_voltages, component_results)
    return NonlinearSolveResult(
        success=True,
        node_voltages=node_voltages,
        component_results=component_results,
        requested_answers=requested_answers,
        calculation_trace=trace,
        warnings=[f"Newton-Raphson converged in {iteration} iterations."],
        iterations=iteration,
    )
