from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import (
    CheckResult,
    SolutionPacket,
    VerificationBadge,
    VerificationReport,
)
from app.services.mna_solver import solve_mna
from app.services.netlist_generator import generate_netlist
from app.services.validator import validate_circuit
from app.services.verifier import verify_solution


def _failed_packet(
    circuit: CircuitProblem,
    status: str,
    message: str,
    checks: list[CheckResult],
    warnings: list[str] | None = None,
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
        generated_netlist=netlist,
        warnings=warnings or [message],
        assumptions_used=circuit.assumptions,
    )


def solve_circuit(problem: CircuitProblem) -> SolutionPacket:
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
        )

    solve_result = solve_mna(circuit)
    if not solve_result.success:
        return _failed_packet(
            circuit=circuit,
            status="invalid",
            message=solve_result.message or "Circuit could not be solved.",
            checks=validation.checks,
            warnings=[*validation.warnings, solve_result.message or "Circuit could not be solved."],
        )

    packet = SolutionPacket(
        circuit_id=circuit.id,
        status="solved",
        node_voltages=solve_result.node_voltages,
        component_results=solve_result.component_results,
        requested_answers=solve_result.requested_answers,
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
