from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import (
    CalculationTrace,
    QuantityValue,
    RCTransientResponse,
    TransientPoint,
)
from app.services.mna_solver import solve_mna


SUPPORTED_TRANSIENT_COMPONENTS = {
    "resistor",
    "voltage_source",
    "current_source",
    "capacitor",
    "inductor",
}
DEFAULT_TRANSIENT_STOP_S = 1e-3
TRANSIENT_REL_TOL = 1e-5
TRANSIENT_ABS_TOL = 1e-8


@dataclass
class RCTransientSolveResult:
    success: bool
    message: str | None = None
    transient_response: RCTransientResponse | None = None
    requested_answers: dict[str, QuantityValue] = field(default_factory=dict)
    calculation_trace: CalculationTrace = field(default_factory=CalculationTrace)


@dataclass
class _TransientState:
    capacitor_voltages: dict[str, float]
    inductor_currents: dict[str, float]


@dataclass
class _StepResult:
    state: _TransientState
    node_voltages: dict[str, float]
    unknown_order: list[str]
    matrix: np.ndarray
    rhs: np.ndarray
    solution: np.ndarray


def _quantity(value: float, unit: str, explanation_key: str) -> QuantityValue:
    return QuantityValue(value=float(value), unit=unit, explanation_key=explanation_key)


def _capacitor_voltage(capacitor: Component, node_voltages: dict[str, float]) -> float:
    return node_voltages[capacitor.nodes[0]] - node_voltages[capacitor.nodes[1]]


def _capacitors(problem: CircuitProblem) -> list[Component]:
    return [component for component in problem.components if component.type == "capacitor"]


def _inductors(problem: CircuitProblem) -> list[Component]:
    return [component for component in problem.components if component.type == "inductor"]


def _target_capacitor(problem: CircuitProblem) -> Component | None:
    capacitors = _capacitors(problem)
    if not capacitors:
        return None
    capacitor_id = problem.transient.capacitor_id if problem.transient else None
    if capacitor_id is None:
        return capacitors[0] if len(capacitors) == 1 else None
    return next((component for component in capacitors if component.id == capacitor_id), None)


def _is_first_order_rc(problem: CircuitProblem) -> bool:
    return (
        len(_capacitors(problem)) == 1
        and not _inductors(problem)
        and all(component.type in SUPPORTED_TRANSIENT_COMPONENTS for component in problem.components)
    )


def _component_for_dc_final(component: Component) -> Component | None:
    if component.type == "capacitor":
        return None
    if component.type == "inductor":
        return component.model_copy(update={"type": "voltage_source", "value": 0.0, "unit": "V"})
    return component.model_copy(deep=True)


def _dc_final_voltage(problem: CircuitProblem, capacitor: Component) -> tuple[bool, float, str | None]:
    dc_components = [
        dc_component
        for component in problem.components
        if (dc_component := _component_for_dc_final(component)) is not None
    ]
    dc_problem = problem.model_copy(
        deep=True,
        update={
            "analysis_type": "dc_operating_point",
            "components": dc_components,
            "goals": [],
            "unsupported_features": [],
            "ambiguities": [],
        },
    )
    dc_result = solve_mna(dc_problem)
    if not dc_result.success:
        return False, 0.0, dc_result.message
    return True, _capacitor_voltage(capacitor, dc_result.node_voltages), None


def _deactivated_components(problem: CircuitProblem, capacitor: Component) -> list[Component]:
    components: list[Component] = []
    for component in problem.components:
        if component.type == "capacitor":
            continue
        if component.type == "current_source":
            continue
        if component.type == "voltage_source":
            components.append(component.model_copy(update={"value": 0.0}))
            continue
        if component.type == "inductor":
            components.append(
                component.model_copy(update={"type": "voltage_source", "value": 0.0, "unit": "V"})
            )
            continue
        components.append(component.model_copy(deep=True))
    return components


def _thevenin_resistance(problem: CircuitProblem, capacitor: Component) -> tuple[bool, float, str | None]:
    positive_node, negative_node = capacitor.nodes
    test_source = Component(
        id="I_TEST_RC_TRANSIENT",
        type="current_source",
        nodes=[negative_node, positive_node],
        value=1.0,
        unit="A",
    )
    test_problem = problem.model_copy(
        deep=True,
        update={
            "analysis_type": "dc_operating_point",
            "components": [*_deactivated_components(problem, capacitor), test_source],
            "goals": [],
            "unsupported_features": [],
            "ambiguities": [],
        },
    )
    test_result = solve_mna(test_problem)
    if not test_result.success:
        return False, 0.0, test_result.message

    resistance = (
        test_result.node_voltages[positive_node] - test_result.node_voltages[negative_node]
    )
    if not math.isfinite(resistance) or resistance <= 0:
        return False, 0.0, "Equivalent resistance seen by the capacitor must be positive."
    return True, float(resistance), None


def _stamp_admittance(
    matrix: np.ndarray,
    idx_a: int | None,
    idx_b: int | None,
    admittance: float,
) -> None:
    if idx_a is not None:
        matrix[idx_a, idx_a] += admittance
    if idx_b is not None:
        matrix[idx_b, idx_b] += admittance
    if idx_a is not None and idx_b is not None:
        matrix[idx_a, idx_b] -= admittance
        matrix[idx_b, idx_a] -= admittance


def _stamp_current_source(
    rhs: np.ndarray,
    idx_a: int | None,
    idx_b: int | None,
    current_a_to_b: float,
) -> None:
    if idx_a is not None:
        rhs[idx_a] -= current_a_to_b
    if idx_b is not None:
        rhs[idx_b] += current_a_to_b


def _solve_transient_step(
    problem: CircuitProblem,
    state: _TransientState,
    dt_s: float,
) -> tuple[bool, _StepResult | None, str | None]:
    ground = problem.ground_node
    non_ground_nodes = [node for node in problem.nodes if node != ground]
    node_index = {node: idx for idx, node in enumerate(non_ground_nodes)}
    voltage_sources = [
        component for component in problem.components if component.type == "voltage_source"
    ]
    inductors = _inductors(problem)
    source_index = {
        component.id: len(non_ground_nodes) + idx
        for idx, component in enumerate(voltage_sources)
    }
    inductor_index = {
        component.id: len(non_ground_nodes) + len(voltage_sources) + idx
        for idx, component in enumerate(inductors)
    }
    unknown_order = [
        *(f"V({node})" for node in non_ground_nodes),
        *(f"I({component.id})" for component in voltage_sources),
        *(f"I({component.id})" for component in inductors),
    ]
    size = len(unknown_order)
    if size == 0:
        return False, None, "Transient circuit has no unknowns to solve."

    matrix = np.zeros((size, size), dtype=float)
    rhs = np.zeros(size, dtype=float)

    for component in problem.components:
        if component.type not in SUPPORTED_TRANSIENT_COMPONENTS:
            return (
                False,
                None,
                f"Unsupported component type {component.type!r} reached the transient solver.",
            )
        node_a, node_b = component.nodes[0], component.nodes[1]
        idx_a = node_index.get(node_a)
        idx_b = node_index.get(node_b)

        if component.type == "resistor":
            _stamp_admittance(matrix, idx_a, idx_b, 1.0 / component.value)
        elif component.type == "capacitor":
            conductance = component.value / dt_s
            previous_voltage = state.capacitor_voltages.get(component.id, 0.0)
            _stamp_admittance(matrix, idx_a, idx_b, conductance)
            # Backward Euler capacitor companion:
            # i_n = C/dt * v_n - C/dt * v_{n-1}.
            # The history term is a Norton source from node b to node a.
            if idx_a is not None:
                rhs[idx_a] += conductance * previous_voltage
            if idx_b is not None:
                rhs[idx_b] -= conductance * previous_voltage
        elif component.type == "current_source":
            _stamp_current_source(rhs, idx_a, idx_b, component.value)
        elif component.type == "voltage_source":
            branch_idx = source_index[component.id]
            if idx_a is not None:
                matrix[idx_a, branch_idx] += 1.0
                matrix[branch_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, branch_idx] -= 1.0
                matrix[branch_idx, idx_b] -= 1.0
            rhs[branch_idx] = component.value
        elif component.type == "inductor":
            branch_idx = inductor_index[component.id]
            resistance = component.value / dt_s
            previous_current = state.inductor_currents.get(component.id, 0.0)
            if idx_a is not None:
                matrix[idx_a, branch_idx] += 1.0
                matrix[branch_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, branch_idx] -= 1.0
                matrix[branch_idx, idx_b] -= 1.0
            matrix[branch_idx, branch_idx] -= resistance
            rhs[branch_idx] = -resistance * previous_current

    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as exc:
        return False, None, f"Transient MNA matrix is singular or ill-conditioned: {exc}"

    node_voltages = {ground: 0.0}
    for node, idx in node_index.items():
        node_voltages[node] = float(solution[idx])

    next_state = _TransientState(
        capacitor_voltages={
            component.id: float(_capacitor_voltage(component, node_voltages))
            for component in _capacitors(problem)
        },
        inductor_currents={
            component.id: float(solution[inductor_index[component.id]])
            for component in inductors
        },
    )
    return (
        True,
        _StepResult(
            state=next_state,
            node_voltages=node_voltages,
            unknown_order=unknown_order,
            matrix=matrix,
            rhs=rhs,
            solution=solution,
        ),
        None,
    )


def _lc_period_s(problem: CircuitProblem, capacitor: Component) -> float | None:
    inductors = _inductors(problem)
    if not inductors:
        return None
    inductance = min(component.value for component in inductors)
    period = 2.0 * math.pi * math.sqrt(inductance * capacitor.value)
    return period if math.isfinite(period) and period > 0 else None


def _sample_times(
    problem: CircuitProblem,
    capacitor: Component,
    is_first_order: bool,
    tau_s: float | None,
) -> list[float]:
    time_points = [0.0]
    if is_first_order and tau_s is not None and tau_s > 0:
        time_points.extend([tau_s, 5.0 * tau_s])
    else:
        period = _lc_period_s(problem, capacitor)
        if period is not None:
            time_points.extend(
                [0.25 * period, 0.5 * period, period, 2.0 * period, 5.0 * period]
            )
        else:
            time_points.extend([DEFAULT_TRANSIENT_STOP_S / 5.0, DEFAULT_TRANSIENT_STOP_S])
    if problem.transient:
        time_points.extend(problem.transient.time_points_s)
    return sorted({round(value, 15) for value in time_points if value >= 0.0})


def _base_step_s(
    sample_times: list[float],
    problem: CircuitProblem,
    capacitor: Component,
    tau_s: float | None,
) -> float:
    positive_times = [time for time in sample_times if time > 0.0]
    max_time = max(positive_times, default=DEFAULT_TRANSIENT_STOP_S)
    candidates = [max_time / 200.0]
    if tau_s is not None and tau_s > 0.0:
        candidates.append(tau_s / 40.0)
    period = _lc_period_s(problem, capacitor)
    if period is not None:
        candidates.append(period / 80.0)
    intervals = [
        later - earlier
        for earlier, later in zip(sample_times, sample_times[1:])
        if later > earlier
    ]
    if intervals:
        candidates.append(min(intervals) / 10.0)
    step = min(value for value in candidates if value > 0.0 and math.isfinite(value))
    return max(step, max_time * 1e-12, 1e-15)


def _target_voltage(state: _TransientState, capacitor: Component) -> float:
    return state.capacitor_voltages.get(capacitor.id, 0.0)


def _initial_state(problem: CircuitProblem, target_capacitor: Component) -> _TransientState:
    target_initial_voltage = problem.transient.initial_voltage_v if problem.transient else 0.0
    return _TransientState(
        capacitor_voltages={
            capacitor.id: float(target_initial_voltage if capacitor.id == target_capacitor.id else 0.0)
            for capacitor in _capacitors(problem)
        },
        inductor_currents={inductor.id: 0.0 for inductor in _inductors(problem)},
    )


def _integrate_samples(
    problem: CircuitProblem,
    target_capacitor: Component,
    sample_times: list[float],
    initial_state: _TransientState,
    base_step_s: float,
) -> tuple[bool, list[TransientPoint], _StepResult | None, str | None]:
    samples: list[TransientPoint] = [
        TransientPoint(time_s=0.0, voltage_v=float(_target_voltage(initial_state, target_capacitor)))
    ]
    state = initial_state
    current_time = 0.0
    next_step = base_step_s
    last_step_result: _StepResult | None = None
    max_time = max(sample_times, default=0.0)
    min_step = max(max_time * 1e-12, 1e-15)

    for sample_time in sample_times:
        if sample_time <= 0.0:
            continue
        while current_time < sample_time - min_step:
            remaining = sample_time - current_time
            step = min(next_step, remaining)
            while True:
                ok, full_step, message = _solve_transient_step(problem, state, step)
                if not ok or full_step is None:
                    return False, samples, last_step_result, message
                ok, half_step, message = _solve_transient_step(problem, state, step / 2.0)
                if not ok or half_step is None:
                    return False, samples, last_step_result, message
                ok, half_step_2, message = _solve_transient_step(
                    problem, half_step.state, step / 2.0
                )
                if not ok or half_step_2 is None:
                    return False, samples, last_step_result, message

                full_voltage = _target_voltage(full_step.state, target_capacitor)
                refined_voltage = _target_voltage(half_step_2.state, target_capacitor)
                error = abs(refined_voltage - full_voltage)
                tolerance = TRANSIENT_ABS_TOL + TRANSIENT_REL_TOL * max(
                    1.0, abs(refined_voltage)
                )
                if error <= tolerance or step <= min_step:
                    state = half_step_2.state
                    current_time += step
                    last_step_result = half_step_2
                    next_step = step * 2.0 if error < tolerance / 8.0 else step
                    break
                step /= 2.0
            next_step = min(next_step, base_step_s)
        samples.append(
            TransientPoint(
                time_s=float(sample_time),
                voltage_v=float(_target_voltage(state, target_capacitor)),
            )
        )

    return True, samples, last_step_result, None


def solve_rc_transient(problem: CircuitProblem) -> RCTransientSolveResult:
    trace = CalculationTrace(
        solver_name="internal_transient_mna_be_v1",
        solver_method="Backward Euler companion-model transient integration",
        solver_backend="numpy.linalg.solve",
        answer_source="rc_transient_solver",
        verification_source="transient_numerical_checks",
    )

    capacitor = _target_capacitor(problem)
    if capacitor is None:
        return RCTransientSolveResult(
            success=False,
            message=(
                "Transient analysis requires at least one capacitor and a unique target "
                "capacitor, or transient.capacitor_id when multiple capacitors are present."
            ),
            calculation_trace=trace,
        )

    final_ok, final_voltage, final_message = _dc_final_voltage(problem, capacitor)
    if not final_ok:
        return RCTransientSolveResult(
            success=False,
            message=f"Could not compute final capacitor voltage: {final_message}",
            calculation_trace=trace,
        )

    is_first_order = _is_first_order_rc(problem)
    resistance: float | None = None
    tau: float | None = None
    if is_first_order:
        resistance_ok, resistance_value, resistance_message = _thevenin_resistance(
            problem, capacitor
        )
        if not resistance_ok:
            return RCTransientSolveResult(
                success=False,
                message=f"Could not compute RC time constant: {resistance_message}",
                calculation_trace=trace,
            )
        resistance = resistance_value
        tau = resistance * capacitor.value

    initial_state = _initial_state(problem, capacitor)
    sample_times = _sample_times(problem, capacitor, is_first_order, tau)
    ok, samples, last_step_result, message = _integrate_samples(
        problem=problem,
        target_capacitor=capacitor,
        sample_times=sample_times,
        initial_state=initial_state,
        base_step_s=_base_step_s(sample_times, problem, capacitor, tau),
    )
    if not ok:
        return RCTransientSolveResult(
            success=False,
            message=message or "Transient numerical integration failed.",
            calculation_trace=trace,
        )
    if last_step_result is not None:
        trace.unknown_order = last_step_result.unknown_order
        trace.mna_matrix = last_step_result.matrix.tolist()
        trace.rhs_vector = last_step_result.rhs.tolist()
        trace.solution_vector = last_step_result.solution.tolist()

    initial_voltage = _target_voltage(initial_state, capacitor)
    formula = (
        "Numerical Backward Euler transient integration using companion models "
        "for capacitors and inductors."
    )
    response = RCTransientResponse(
        capacitor_id=capacitor.id,
        positive_node=capacitor.nodes[0],
        negative_node=capacitor.nodes[1],
        initial_voltage_v=float(initial_voltage),
        final_voltage_v=float(final_voltage),
        resistance_ohm=float(resistance or 0.0),
        capacitance_f=float(capacitor.value),
        time_constant_s=float(tau or 0.0),
        formula=formula,
        sample_points=samples,
        analysis_method="backward_euler_companion_model",
        is_first_order=bool(is_first_order),
    )
    requested_answers = {
        "initial_voltage": _quantity(initial_voltage, "V", "rc_transient:initial_voltage"),
        "final_voltage": _quantity(final_voltage, "V", "rc_transient:final_voltage"),
    }
    if is_first_order and tau is not None and resistance is not None:
        requested_answers["time_constant"] = _quantity(tau, "s", "rc_transient:time_constant")
        requested_answers["thevenin_resistance"] = _quantity(
            resistance,
            "ohm",
            "rc_transient:thevenin_resistance",
        )
    return RCTransientSolveResult(
        success=True,
        transient_response=response,
        requested_answers=requested_answers,
        calculation_trace=trace,
    )
