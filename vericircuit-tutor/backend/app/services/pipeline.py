from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import (
    ACFrequencyPoint,
    CalculationTrace,
    CheckResult,
    SolutionPacket,
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
        return packet

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
        return packet

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
        return packet

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
    return packet
