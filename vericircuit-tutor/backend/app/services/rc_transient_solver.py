from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import (
    CalculationTrace,
    QuantityValue,
    RCTransientResponse,
    TransientPoint,
)
from app.services.mna_solver import solve_mna


@dataclass
class RCTransientSolveResult:
    success: bool
    message: str | None = None
    transient_response: RCTransientResponse | None = None
    requested_answers: dict[str, QuantityValue] = field(default_factory=dict)
    calculation_trace: CalculationTrace = field(default_factory=CalculationTrace)


def _quantity(value: float, unit: str, explanation_key: str) -> QuantityValue:
    return QuantityValue(value=float(value), unit=unit, explanation_key=explanation_key)


def _capacitor_voltage(capacitor: Component, node_voltages: dict[str, float]) -> float:
    return node_voltages[capacitor.nodes[0]] - node_voltages[capacitor.nodes[1]]


def _target_capacitor(problem: CircuitProblem) -> Component | None:
    capacitors = [component for component in problem.components if component.type == "capacitor"]
    if not capacitors:
        return None
    capacitor_id = problem.transient.capacitor_id if problem.transient else None
    if capacitor_id is None:
        return capacitors[0] if len(capacitors) == 1 else None
    return next((component for component in capacitors if component.id == capacitor_id), None)


def _dc_final_voltage(problem: CircuitProblem, capacitor: Component) -> tuple[bool, float, str | None]:
    dc_problem = problem.model_copy(
        deep=True,
        update={"analysis_type": "dc_operating_point", "goals": []},
    )
    dc_result = solve_mna(dc_problem)
    if not dc_result.success:
        return False, 0.0, dc_result.message
    return True, _capacitor_voltage(capacitor, dc_result.node_voltages), None


def _deactivated_components(problem: CircuitProblem, capacitor: Component) -> list[Component]:
    components: list[Component] = []
    for component in problem.components:
        if component.id == capacitor.id:
            continue
        if component.type == "current_source":
            continue
        if component.type == "voltage_source":
            components.append(component.model_copy(update={"value": 0.0}))
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


def solve_rc_transient(problem: CircuitProblem) -> RCTransientSolveResult:
    trace = CalculationTrace(
        solver_name="internal_rc_transient_template_v1",
        solver_method="First-order RC transient template",
        solver_backend="internal_mna_v1",
        answer_source="rc_transient_solver",
        verification_source="rc_transient_template_checks",
    )

    capacitor = _target_capacitor(problem)
    if capacitor is None:
        return RCTransientSolveResult(
            success=False,
            message="RC transient template requires exactly one target capacitor.",
            calculation_trace=trace,
        )

    final_ok, final_voltage, final_message = _dc_final_voltage(problem, capacitor)
    if not final_ok:
        return RCTransientSolveResult(
            success=False,
            message=f"Could not compute final capacitor voltage: {final_message}",
            calculation_trace=trace,
        )

    resistance_ok, resistance, resistance_message = _thevenin_resistance(problem, capacitor)
    if not resistance_ok:
        return RCTransientSolveResult(
            success=False,
            message=f"Could not compute RC time constant: {resistance_message}",
            calculation_trace=trace,
        )

    initial_voltage = problem.transient.initial_voltage_v if problem.transient else 0.0
    capacitance = capacitor.value
    tau = resistance * capacitance
    time_points = [0.0, tau, 5.0 * tau]
    if problem.transient:
        time_points.extend(problem.transient.time_points_s)
    sample_times = sorted({round(value, 15) for value in time_points if value >= 0})
    samples = [
        TransientPoint(
            time_s=float(time_s),
            voltage_v=float(
                final_voltage + (initial_voltage - final_voltage) * math.exp(-time_s / tau)
            ),
        )
        for time_s in sample_times
    ]

    formula = (
        f"V_C(t) = {final_voltage:.12g} + "
        f"({initial_voltage:.12g} - {final_voltage:.12g}) exp(-t/{tau:.12g}) V"
    )
    response = RCTransientResponse(
        capacitor_id=capacitor.id,
        positive_node=capacitor.nodes[0],
        negative_node=capacitor.nodes[1],
        initial_voltage_v=float(initial_voltage),
        final_voltage_v=float(final_voltage),
        resistance_ohm=float(resistance),
        capacitance_f=float(capacitance),
        time_constant_s=float(tau),
        formula=formula,
        sample_points=samples,
    )
    requested_answers = {
        "initial_voltage": _quantity(initial_voltage, "V", "rc_transient:initial_voltage"),
        "final_voltage": _quantity(final_voltage, "V", "rc_transient:final_voltage"),
        "time_constant": _quantity(tau, "s", "rc_transient:time_constant"),
        "thevenin_resistance": _quantity(resistance, "ohm", "rc_transient:thevenin_resistance"),
    }
    return RCTransientSolveResult(
        success=True,
        transient_response=response,
        requested_answers=requested_answers,
        calculation_trace=trace,
    )
