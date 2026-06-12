from __future__ import annotations

import math

from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import (
    ACFrequencyPoint,
    CalculationTrace,
    CheckResult,
    SolutionPacket,
    TutorObservation,
    VerificationBadge,
    VerificationReport,
)
from app.services.ac_solver import generate_sweep_frequencies, solve_ac
from app.services.ac_verifier import verify_ac_solution
from app.services.mna_solver import solve_mna
from app.services.netlist_generator import generate_netlist
from app.services.rc_transient_solver import solve_rc_transient
from app.services.validator import validate_circuit
from app.services.verifier import verify_solution


def _component_by_id(circuit: CircuitProblem, component_id: str) -> Component | None:
    return next((component for component in circuit.components if component.id == component_id), None)


def _cutoff_frequency_hz(resistor: Component | None, capacitor: Component | None) -> float | None:
    if resistor is None or capacitor is None:
        return None
    if resistor.value <= 0 or capacitor.value <= 0:
        return None
    return 1.0 / (2.0 * math.pi * resistor.value * capacitor.value)


def _first_ac_source_magnitude(circuit: CircuitProblem) -> float | None:
    for component in circuit.components:
        if component.type in {"voltage_source", "current_source"} and component.ac_magnitude:
            return float(component.ac_magnitude)
    return None


def _first_ac_answer(packet: SolutionPacket):
    return next(iter(packet.ac_requested_answers.values()), None)


def _add_cutoff_observation(
    observations: list[TutorObservation],
    observation_id: str,
    label: str,
    cutoff_hz: float | None,
) -> None:
    if cutoff_hz is None:
        return
    observations.append(
        TutorObservation(
            id=observation_id,
            label=label,
            value=float(cutoff_hz),
            unit="Hz",
            note="Computed from the template R and C values before being written to the Solution Packet.",
        )
    )


def _build_ac_filter_observations(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[TutorObservation]:
    observations: list[TutorObservation] = []
    topology = circuit.topology_id or circuit.id
    title = circuit.title.lower()
    source_magnitude = _first_ac_source_magnitude(circuit)
    first_answer = _first_ac_answer(packet)

    if packet.frequency_hz is not None:
        observations.append(
            TutorObservation(
                id="analysis_frequency",
                label="Analysis frequency",
                value=float(packet.frequency_hz),
                unit="Hz",
            )
        )

    if first_answer is not None:
        observations.append(
            TutorObservation(
                id="requested_magnitude",
                label="Requested phasor magnitude",
                value=float(first_answer.magnitude),
                unit=first_answer.unit,
            )
        )
        observations.append(
            TutorObservation(
                id="requested_phase",
                label="Requested phasor phase",
                value=float(first_answer.phase_deg),
                unit="deg",
            )
        )

    if first_answer is not None and source_magnitude and source_magnitude > 0:
        observations.append(
            TutorObservation(
                id="transfer_magnitude_ratio",
                label="Output magnitude divided by source magnitude",
                value=float(first_answer.magnitude / source_magnitude),
                unit="V/V",
                note="For these voltage-source templates, the ratio is normalized to the source AC magnitude.",
            )
        )

    if "band_pass" in topology or "band-pass" in title or "band pass" in title:
        observations.append(
            TutorObservation(
                id="filter_behavior",
                label="Filter behavior",
                note="band-pass",
            )
        )
        _add_cutoff_observation(
            observations,
            "high_pass_cutoff_frequency",
            "High-pass corner frequency",
            _cutoff_frequency_hz(_component_by_id(circuit, "RHP"), _component_by_id(circuit, "CHP")),
        )
        _add_cutoff_observation(
            observations,
            "low_pass_cutoff_frequency",
            "Low-pass corner frequency",
            _cutoff_frequency_hz(_component_by_id(circuit, "RLP"), _component_by_id(circuit, "CLP")),
        )
    elif "low_pass" in topology or "low-pass" in title or "low pass" in title:
        observations.append(
            TutorObservation(
                id="filter_behavior",
                label="Filter behavior",
                note="low-pass",
            )
        )
        resistor = next((component for component in circuit.components if component.type == "resistor"), None)
        capacitor = next((component for component in circuit.components if component.type == "capacitor"), None)
        _add_cutoff_observation(
            observations,
            "low_pass_cutoff_frequency",
            "Low-pass corner frequency",
            _cutoff_frequency_hz(resistor, capacitor),
        )
        observations.append(
            TutorObservation(
                id="first_order_corner_ratio",
                label="First-order corner magnitude ratio",
                value=float(1.0 / math.sqrt(2.0)),
                unit="V/V",
                note="Canonical first-order RC marker included in the packet for tutor explanation.",
            )
        )

    return observations


def _build_rc_transient_observations(packet: SolutionPacket) -> list[TutorObservation]:
    response = packet.transient_response
    if response is None:
        return []

    observations = [
        TutorObservation(
            id="time_constant",
            label="Time constant",
            value=float(response.time_constant_s),
            unit="s",
        )
    ]
    tau_sample = next(
        (
            point
            for point in response.sample_points
            if abs(point.time_s - response.time_constant_s) <= max(1e-15, response.time_constant_s * 1e-9)
        ),
        None,
    )
    if tau_sample is not None:
        observations.append(
            TutorObservation(
                id="tau_marker_voltage",
                label="Capacitor voltage at one tau",
                value=float(tau_sample.voltage_v),
                unit="V",
            )
        )
    return observations


def _build_tutor_observations(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorObservation]:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return []
    if packet.ac_requested_answers:
        return _build_ac_filter_observations(circuit, packet)
    if packet.transient_response:
        return _build_rc_transient_observations(packet)
    return []


def _attach_tutor_context(circuit: CircuitProblem, packet: SolutionPacket) -> SolutionPacket:
    packet.bme_metadata = circuit.bme_metadata
    packet.tutor_observations = _build_tutor_observations(circuit, packet)
    return packet


def _failed_packet(
    circuit: CircuitProblem,
    status: str,
    message: str,
    checks: list[CheckResult],
    warnings: list[str] | None = None,
    calculation_trace: CalculationTrace | None = None,
) -> SolutionPacket:
    netlist = ""
    try:
        netlist = generate_netlist(circuit)
    except Exception as exc:  # pragma: no cover - defensive only
        warnings = [*(warnings or []), f"Could not generate netlist: {exc}"]

    badge_label = {
        "ambiguous": "AMBIGUOUS",
        "unsupported": "UNSUPPORTED",
    }.get(status, "FAIL")

    return SolutionPacket(
        circuit_id=circuit.id,
        status=status,  # type: ignore[arg-type]
        verification=VerificationReport(
            passed=False,
            checks=[
                *checks,
                CheckResult(name="pipeline", passed=False, message=message),
            ],
        ),
        verification_badge=VerificationBadge(
            label=badge_label,  # type: ignore[arg-type]
            message=message,
        ),
        calculation_trace=calculation_trace or CalculationTrace(),
        generated_netlist=netlist,
        warnings=warnings or [message],
        assumptions_used=circuit.assumptions,
        bme_metadata=circuit.bme_metadata,
    )


def solve_circuit(problem: CircuitProblem, parser_used: str | None = None) -> SolutionPacket:
    validation = validate_circuit(problem)
    circuit = validation.circuit or problem

    if not validation.valid:
        validation_message = "Circuit IR failed validation."
        if validation.errors:
            validation_message += " " + " ".join(validation.errors)
        return _failed_packet(
            circuit=circuit,
            status=validation.status,
            message=validation_message,
            checks=validation.checks,
            warnings=[*validation.warnings, *validation.errors],
            calculation_trace=CalculationTrace(parser_used=parser_used),
        )

    if circuit.analysis_type in {"ac_steady_state", "ac_single_frequency"}:
        solve_result = solve_ac(circuit)
        if not solve_result.success:
            return _failed_packet(
                circuit=circuit,
                status="invalid",
                message=solve_result.message or "AC circuit could not be solved.",
                checks=validation.checks,
                warnings=[
                    *validation.warnings,
                    solve_result.message or "AC circuit could not be solved.",
                ],
                calculation_trace=solve_result.calculation_trace.model_copy(
                    update={"parser_used": parser_used}
                ),
            )

        trace = solve_result.calculation_trace.model_copy(update={"parser_used": parser_used})
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status="solved",
            ac_node_voltages=solve_result.node_voltages,
            ac_component_results=solve_result.component_results,
            ac_requested_answers=solve_result.requested_answers,
            frequency_hz=solve_result.frequency_hz,
            calculation_trace=trace,
            generated_netlist=generate_netlist(circuit),
            warnings=validation.warnings,
            assumptions_used=circuit.assumptions,
        )
        packet.verification = verify_ac_solution(circuit, packet)
        packet.verification_badge = VerificationBadge(
            label="PASS" if packet.verification.passed else "FAIL",
            message=(
                "AC phasor solver output passed validation, complex KCL, finite-value, "
                "and requested-answer checks."
                if packet.verification.passed
                else "AC solver output was produced, but one or more verification checks failed."
            ),
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type == "ac_sweep":
        points: list[ACFrequencyPoint] = []
        warnings = [*validation.warnings]
        max_kcl_residual = 0.0
        all_points_passed = True
        trace = CalculationTrace(
            parser_used=parser_used,
            solver_name="internal_ac_mna_v1",
            solver_method="Complex Modified Nodal Analysis sweep",
            answer_source="ac_solver",
            verification_source="ac_verifier.py",
        )

        for frequency in generate_sweep_frequencies(circuit):
            solve_result = solve_ac(circuit, frequency_hz=frequency)
            if not solve_result.success:
                all_points_passed = False
                message = solve_result.message or f"AC sweep point {frequency:g} Hz failed."
                warnings.append(f"{frequency:g} Hz: {message}")
                points.append(
                    ACFrequencyPoint(
                        frequency_hz=frequency,
                        verification=VerificationReport(
                            passed=False,
                            checks=[
                                CheckResult(
                                    name="ac_solve",
                                    passed=False,
                                    message=message,
                                    value=frequency,
                                )
                            ],
                        ),
                    )
                )
                continue

            point_packet = SolutionPacket(
                circuit_id=circuit.id,
                status="solved",
                ac_node_voltages=solve_result.node_voltages,
                ac_component_results=solve_result.component_results,
                ac_requested_answers=solve_result.requested_answers,
                frequency_hz=frequency,
            )
            verification = verify_ac_solution(circuit, point_packet)
            max_kcl_residual = max(max_kcl_residual, verification.max_kcl_residual_a)
            if not verification.passed:
                all_points_passed = False
            points.append(
                ACFrequencyPoint(
                    frequency_hz=frequency,
                    node_voltages=solve_result.node_voltages,
                    component_results=solve_result.component_results,
                    requested_answers=solve_result.requested_answers,
                    verification=verification,
                )
            )

        sweep_checks = [
            *validation.checks,
            CheckResult(
                name="ac_sweep_points_present",
                passed=bool(points),
                message="AC sweep produced frequency points."
                if points
                else "AC sweep produced no frequency points.",
                value=len(points),
            ),
            CheckResult(
                name="ac_sweep_points_passed",
                passed=all_points_passed and bool(points),
                message="Every AC sweep point passed verification."
                if all_points_passed and points
                else "One or more AC sweep points failed solving or verification.",
                value=max_kcl_residual,
            ),
        ]
        verification = VerificationReport(
            passed=all(check.passed for check in sweep_checks),
            max_kcl_residual_a=max_kcl_residual,
            power_balance_error_w=0.0,
            checks=sweep_checks,
        )
        status = "solved" if verification.passed else "invalid"
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status=status,  # type: ignore[arg-type]
            ac_sweep=points,
            verification=verification,
            verification_badge=VerificationBadge(
                label="PASS" if verification.passed else "FAIL",
                message=(
                    "AC sweep passed validation and every frequency point passed AC verification."
                    if verification.passed
                    else "AC sweep was attempted, but one or more points failed."
                ),
            ),
            calculation_trace=trace,
            generated_netlist=generate_netlist(circuit),
            warnings=warnings,
            assumptions_used=circuit.assumptions,
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type == "rc_transient":
        solve_result = solve_rc_transient(circuit)
        if not solve_result.success:
            return _failed_packet(
                circuit=circuit,
                status="invalid",
                message=solve_result.message or "RC transient template could not be solved.",
                checks=validation.checks,
                warnings=[
                    *validation.warnings,
                    solve_result.message or "RC transient template could not be solved.",
                ],
                calculation_trace=solve_result.calculation_trace.model_copy(
                    update={"parser_used": parser_used}
                ),
            )

        checks = [
            *validation.checks,
            CheckResult(
                name="rc_transient_template",
                passed=True,
                message=(
                    "First-order RC transient template was generated from initial condition, "
                    "DC final value, and Thevenin resistance."
                ),
                value=solve_result.transient_response.time_constant_s
                if solve_result.transient_response
                else None,
            ),
        ]
        verification = VerificationReport(
            passed=all(check.passed for check in checks),
            checks=checks,
        )
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status="solved" if verification.passed else "invalid",
            requested_answers=solve_result.requested_answers,
            transient_response=solve_result.transient_response,
            verification=verification,
            verification_badge=VerificationBadge(
                label="PASS" if verification.passed else "FAIL",
                message=(
                    "RC transient template passed validation and generated time constant, "
                    "initial/final conditions, and voltage samples."
                    if verification.passed
                    else "RC transient template was produced, but one or more checks failed."
                ),
            ),
            calculation_trace=solve_result.calculation_trace.model_copy(
                update={"parser_used": parser_used}
            ),
            generated_netlist=generate_netlist(circuit),
            warnings=validation.warnings,
            assumptions_used=circuit.assumptions,
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type != "dc_operating_point":
        return _failed_packet(
            circuit=circuit,
            status="unsupported",
            message=f"Unsupported analysis type {circuit.analysis_type!r}.",
            checks=validation.checks,
            warnings=[*validation.warnings, f"Unsupported analysis type {circuit.analysis_type!r}."],
            calculation_trace=CalculationTrace(parser_used=parser_used),
        )

    solve_result = solve_mna(circuit)
    if not solve_result.success:
        return _failed_packet(
            circuit=circuit,
            status="invalid",
            message=solve_result.message or "Circuit could not be solved.",
            checks=validation.checks,
            warnings=[*validation.warnings, solve_result.message or "Circuit could not be solved."],
            calculation_trace=solve_result.calculation_trace.model_copy(
                update={"parser_used": parser_used}
            ),
        )

    trace = solve_result.calculation_trace.model_copy(update={"parser_used": parser_used})
    packet = SolutionPacket(
        circuit_id=circuit.id,
        status="solved",
        node_voltages=solve_result.node_voltages,
        component_results=solve_result.component_results,
        requested_answers=solve_result.requested_answers,
        calculation_trace=trace,
        generated_netlist=generate_netlist(circuit),
        warnings=validation.warnings,
        assumptions_used=circuit.assumptions,
    )
    packet.verification = verify_solution(circuit, packet)
    packet.verification_badge = VerificationBadge(
        label="PASS" if packet.verification.passed else "FAIL",
        message=(
            "Solver output passed validation, KCL, power-balance, unit, and requested-answer checks."
            if packet.verification.passed
            else "Solver output was produced, but one or more verification checks failed."
        ),
    )
    return _attach_tutor_context(circuit, packet)
