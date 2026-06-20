from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field

import numpy as np

from app.models.circuit_ir import (
    CircuitProblem,
    Component,
    is_nonideal_op_amp_type,
    is_op_amp_type,
)
from app.models.solution_packet import (
    ACComponentResult,
    CalculationTrace,
    ComplexQuantityValue,
)
from app.services.mna_solver import nonideal_open_loop_gain


AC_SIGN_CONVENTION = (
    "Phasor voltage is V(nodes[0]) - V(nodes[1]); phasor current is positive "
    "from nodes[0] to nodes[1]."
)


@dataclass
class ACSolveResult:
    success: bool
    message: str | None = None
    frequency_hz: float | None = None
    node_voltages: dict[str, ComplexQuantityValue] = field(default_factory=dict)
    component_results: dict[str, ACComponentResult] = field(default_factory=dict)
    requested_answers: dict[str, ComplexQuantityValue] = field(default_factory=dict)
    calculation_trace: CalculationTrace = field(default_factory=CalculationTrace)


def complex_quantity(
    value: complex,
    unit: str,
    explanation_key: str | None = None,
    reference: dict[str, str] | None = None,
) -> ComplexQuantityValue:
    magnitude = abs(value)
    phase_deg = 0.0 if magnitude <= 1e-15 else math.degrees(cmath.phase(value))
    return ComplexQuantityValue(
        real=float(value.real),
        imag=float(value.imag),
        magnitude=float(magnitude),
        phase_deg=float(phase_deg),
        unit=unit,
        explanation_key=explanation_key,
        reference=reference,
    )


def quantity_to_complex(value: ComplexQuantityValue) -> complex:
    return complex(value.real, value.imag)


def _node_voltage(node: str, voltages: dict[str, complex]) -> complex:
    if node not in voltages:
        raise KeyError(f"Node {node!r} was not solved and cannot be used as a voltage reference.")
    return voltages[node]


def _component_voltage(nodes: list[str], voltages: dict[str, complex]) -> complex:
    return _node_voltage(nodes[0], voltages) - _node_voltage(nodes[1], voltages)


def _op_amp_output_voltage(nodes: list[str], voltages: dict[str, complex]) -> complex:
    return _node_voltage(nodes[2], voltages) - _node_voltage(nodes[3], voltages)


def _phasor(magnitude: float | None, phase_deg: float | None) -> complex:
    if magnitude is None:
        return 0.0 + 0.0j
    phase_rad = math.radians(phase_deg or 0.0)
    return magnitude * complex(math.cos(phase_rad), math.sin(phase_rad))


def _stamp_admittance(
    matrix: np.ndarray,
    node_index: dict[str, int],
    node_a: str,
    node_b: str,
    admittance: complex,
) -> None:
    idx_a = node_index.get(node_a)
    idx_b = node_index.get(node_b)
    if idx_a is not None:
        matrix[idx_a, idx_a] += admittance
    if idx_b is not None:
        matrix[idx_b, idx_b] += admittance
    if idx_a is not None and idx_b is not None:
        matrix[idx_a, idx_b] -= admittance
        matrix[idx_b, idx_a] -= admittance


def nonideal_frequency_gain(component: Component, frequency_hz: float) -> complex:
    dc_gain = nonideal_open_loop_gain(component)
    if component.gain_bandwidth_hz is not None:
        pole_hz = component.gain_bandwidth_hz / dc_gain
    else:
        pole_hz = component.bandwidth_hz
    if pole_hz is None or pole_hz <= 0:
        return complex(dc_gain, 0.0)
    return dc_gain / (1.0 + 1j * (frequency_hz / pole_hz))


def _build_requested_answers(
    problem: CircuitProblem,
    node_voltages: dict[str, complex],
    component_results: dict[str, ACComponentResult],
) -> dict[str, ComplexQuantityValue]:
    answers: dict[str, ComplexQuantityValue] = {}
    components_by_id = {component.id: component for component in problem.components}

    for goal in problem.goals:
        key = f"{goal.quantity}:{goal.target}"
        if goal.quantity == "node_voltage":
            value = node_voltages[goal.target]
            answers[goal.id] = complex_quantity(
                value,
                "V",
                explanation_key=key,
                reference={"positive_node": goal.target, "negative_node": problem.ground_node},
            )
            continue

        component = components_by_id[goal.target]
        result = component_results[goal.target]

        if goal.quantity == "component_voltage":
            if goal.reference and {"positive_node", "negative_node"} <= set(goal.reference):
                value = (
                    _node_voltage(str(goal.reference["positive_node"]), node_voltages)
                    - _node_voltage(str(goal.reference["negative_node"]), node_voltages)
                )
                reference = {
                    "positive_node": str(goal.reference["positive_node"]),
                    "negative_node": str(goal.reference["negative_node"]),
                }
            else:
                value = quantity_to_complex(result.voltage)
                if is_op_amp_type(component.type):
                    reference = {
                        "positive_node": component.nodes[2],
                        "negative_node": component.nodes[3],
                    }
                else:
                    reference = {
                        "positive_node": component.nodes[0],
                        "negative_node": component.nodes[1],
                    }
            answers[goal.id] = complex_quantity(value, "V", explanation_key=key, reference=reference)
        elif goal.quantity == "component_current":
            answers[goal.id] = complex_quantity(
                quantity_to_complex(result.current),
                "A",
                explanation_key=key,
                reference=result.current.reference,
            )
        elif goal.quantity in {"component_power", "source_power"}:
            power = quantity_to_complex(result.voltage) * quantity_to_complex(result.current).conjugate()
            answers[goal.id] = complex_quantity(
                power,
                "VA",
                explanation_key=key,
                reference={"component": component.id},
            )

    return answers


def solve_ac(problem: CircuitProblem, frequency_hz: float | None = None) -> ACSolveResult:
    frequency = frequency_hz if frequency_hz is not None else problem.frequency_hz
    if frequency is None or frequency <= 0:
        return ACSolveResult(success=False, message="AC analysis requires frequency_hz > 0.")

    ground = problem.ground_node
    non_ground_nodes = [node for node in problem.nodes if node != ground]
    node_index = {node: idx for idx, node in enumerate(non_ground_nodes)}
    voltage_sources = [
        component for component in problem.components if component.type == "voltage_source"
    ]
    op_amps = [component for component in problem.components if is_op_amp_type(component.type)]
    source_index = {
        component.id: len(non_ground_nodes) + idx
        for idx, component in enumerate(voltage_sources)
    }
    op_amp_index = {
        component.id: len(non_ground_nodes) + len(voltage_sources) + idx
        for idx, component in enumerate(op_amps)
    }
    unknown_order = [
        *(f"V({node})" for node in non_ground_nodes),
        *(f"I({component.id})" for component in voltage_sources),
        *(f"I({component.id}_out)" for component in op_amps),
    ]
    trace = CalculationTrace(
        solver_name="internal_ac_phasor_mna_v1",
        solver_method="Complex Modified Nodal Analysis",
        answer_source="ac_solver",
        verification_source="ac_verifier.py",
        unknown_order=unknown_order,
    )

    size = len(non_ground_nodes) + len(voltage_sources) + len(op_amps)
    if size == 0:
        return ACSolveResult(
            success=False,
            message="Circuit has no unknowns to solve.",
            frequency_hz=frequency,
            calculation_trace=trace,
        )

    matrix = np.zeros((size, size), dtype=complex)
    rhs = np.zeros(size, dtype=complex)
    omega = 2.0 * math.pi * frequency

    for component in problem.components:
        idx_a = node_index.get(component.nodes[0])
        idx_b = node_index.get(component.nodes[1])

        if component.type == "resistor":
            admittance = 1.0 / component.value
            _stamp_admittance(matrix, node_index, component.nodes[0], component.nodes[1], admittance)
        elif component.type == "capacitor":
            admittance = 1j * omega * component.value
            _stamp_admittance(matrix, node_index, component.nodes[0], component.nodes[1], admittance)
        elif component.type == "inductor":
            admittance = 1.0 / (1j * omega * component.value)
            _stamp_admittance(matrix, node_index, component.nodes[0], component.nodes[1], admittance)
        elif component.type == "current_source":
            current = _phasor(component.ac_magnitude, component.ac_phase_deg)
            if idx_a is not None:
                rhs[idx_a] -= current
            if idx_b is not None:
                rhs[idx_b] += current
        elif component.type == "voltage_source":
            vs_idx = source_index[component.id]
            if idx_a is not None:
                matrix[idx_a, vs_idx] += 1.0
                matrix[vs_idx, idx_a] += 1.0
            if idx_b is not None:
                matrix[idx_b, vs_idx] -= 1.0
                matrix[vs_idx, idx_b] -= 1.0
            rhs[vs_idx] = _phasor(component.ac_magnitude, component.ac_phase_deg)
        elif is_op_amp_type(component.type):
            if len(component.nodes) != 4:
                return ACSolveResult(
                    success=False,
                    message=(
                        f"{component.id} op-amp must have nodes "
                        "[non_inverting, inverting, output, reference]."
                    ),
                    frequency_hz=frequency,
                    calculation_trace=trace,
                )
            vp, vm, out, ref = component.nodes
            op_idx = op_amp_index[component.id]
            idx_vp = node_index.get(vp)
            idx_vm = node_index.get(vm)
            idx_out = node_index.get(out)
            idx_ref = node_index.get(ref)

            if component.input_resistance_ohm is not None:
                _stamp_admittance(
                    matrix,
                    node_index,
                    vp,
                    vm,
                    1.0 / component.input_resistance_ohm,
                )
            if component.compensation_capacitance_f is not None:
                _stamp_admittance(
                    matrix,
                    node_index,
                    out,
                    ref,
                    1j * omega * component.compensation_capacitance_f,
                )

            if idx_out is not None:
                matrix[idx_out, op_idx] += 1.0
            if idx_ref is not None:
                matrix[idx_ref, op_idx] -= 1.0
            if is_nonideal_op_amp_type(component.type):
                gain = nonideal_frequency_gain(component, frequency)
                if component.output_resistance_ohm is not None:
                    output_conductance = 1.0 / component.output_resistance_ohm
                    gm = gain * output_conductance
                    if idx_out is not None:
                        matrix[op_idx, idx_out] -= output_conductance
                    if idx_ref is not None:
                        matrix[op_idx, idx_ref] += output_conductance
                    if idx_vp is not None:
                        matrix[op_idx, idx_vp] += gm
                    if idx_vm is not None:
                        matrix[op_idx, idx_vm] -= gm
                    matrix[op_idx, op_idx] += 1.0
                else:
                    if idx_out is not None:
                        matrix[op_idx, idx_out] += 1.0
                    if idx_ref is not None:
                        matrix[op_idx, idx_ref] -= 1.0
                    if idx_vp is not None:
                        matrix[op_idx, idx_vp] -= gain
                    if idx_vm is not None:
                        matrix[op_idx, idx_vm] += gain
            else:
                if idx_vp is not None:
                    matrix[op_idx, idx_vp] += 1.0
                if idx_vm is not None:
                    matrix[op_idx, idx_vm] -= 1.0
        else:
            return ACSolveResult(
                success=False,
                message=f"Unsupported component type {component.type!r} reached the AC solver.",
                frequency_hz=frequency,
                calculation_trace=trace,
            )

    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as exc:
        message = f"AC MNA matrix is singular or ill-conditioned: {exc}"
        if op_amps:
            message += (
                " Ideal op-amp circuit may require a closed-loop feedback path "
                "or additional constraints."
            )
        return ACSolveResult(
            success=False,
            message=message,
            frequency_hz=frequency,
            calculation_trace=trace,
        )

    node_voltage_values: dict[str, complex] = {ground: 0.0 + 0.0j}
    for node, idx in node_index.items():
        node_voltage_values[node] = complex(solution[idx])

    voltage_source_currents = {
        component.id: complex(solution[source_index[component.id]])
        for component in voltage_sources
    }
    op_amp_output_currents = {
        component.id: complex(solution[op_amp_index[component.id]])
        for component in op_amps
    }

    component_results: dict[str, ACComponentResult] = {}
    for component in problem.components:
        voltage = (
            _op_amp_output_voltage(component.nodes, node_voltage_values)
            if is_op_amp_type(component.type)
            else _component_voltage(component.nodes, node_voltage_values)
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

        if component.type == "resistor":
            current = voltage / component.value
        elif component.type == "capacitor":
            current = 1j * omega * component.value * voltage
        elif component.type == "inductor":
            current = voltage / (1j * omega * component.value)
        elif component.type == "current_source":
            current = _phasor(component.ac_magnitude, component.ac_phase_deg)
        elif component.type == "voltage_source":
            current = voltage_source_currents[component.id]
        elif is_op_amp_type(component.type):
            current = op_amp_output_currents[component.id]
        else:
            return ACSolveResult(
                success=False,
                message=f"Unsupported component type {component.type!r} reached AC result derivation.",
                frequency_hz=frequency,
                calculation_trace=trace,
            )

        component_results[component.id] = ACComponentResult(
            voltage=complex_quantity(voltage, "V", reference=reference),
            current=complex_quantity(current, "A", reference=current_reference),
            complex_power=complex_quantity(
                voltage * current.conjugate(),
                "VA",
                reference={"component": component.id},
            ),
        )

    node_voltages = {
        node: complex_quantity(value, "V", reference={"positive_node": node, "negative_node": ground})
        for node, value in node_voltage_values.items()
    }
    requested_answers = _build_requested_answers(
        problem,
        node_voltage_values,
        component_results,
    )
    return ACSolveResult(
        success=True,
        frequency_hz=frequency,
        node_voltages=node_voltages,
        component_results=component_results,
        requested_answers=requested_answers,
        calculation_trace=trace,
    )


def generate_sweep_frequencies(problem: CircuitProblem) -> list[float]:
    if problem.sweep is None:
        return []
    sweep = problem.sweep
    if sweep.scale == "linear":
        count = max(2, sweep.points_per_decade)
        return [float(value) for value in np.linspace(sweep.start_hz, sweep.stop_hz, count)]

    decades = math.log10(sweep.stop_hz / sweep.start_hz)
    steps = max(1, math.ceil(decades * sweep.points_per_decade))
    ratio = sweep.stop_hz / sweep.start_hz
    return [
        float(sweep.start_hz * (ratio ** (idx / steps)))
        for idx in range(steps + 1)
    ]
