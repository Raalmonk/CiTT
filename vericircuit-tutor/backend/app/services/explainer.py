from __future__ import annotations

from app.models.solution_packet import SolutionPacket


def _format_value(value: float, unit: str) -> str:
    abs_value = abs(value)
    if unit == "A" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mA"
    if unit == "W" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mW"
    return f"{value:.6g} {unit}"


def _format_complex(magnitude: float, phase_deg: float, unit: str) -> str:
    return f"{magnitude:.6g} {unit} angle {phase_deg:.6g} deg"


def explain_solution(packet: SolutionPacket) -> str:
    if packet.status != "solved":
        return (
            "VeriCircuit Tutor did not generate a numerical explanation because the "
            f"solution packet status is {packet.status!r}. The solver and verifier "
            "must produce verified values before the tutor explains them."
        )

    if not packet.verification.passed:
        return (
            "The numerical solver returned values, but the verification report did "
            "not pass. The tutor explanation is withheld so unverified numbers are "
            "not presented as final answers."
        )

    if packet.ac_requested_answers or packet.ac_sweep:
        lines: list[str] = []
        lines.append(
            "Method: the circuit was converted to Circuit IR, solved with complex "
            "Modified Nodal Analysis for sinusoidal steady state, and then checked "
            "with deterministic complex KCL and finite-value tests."
        )
        if packet.frequency_hz is not None:
            lines.append(f"Analysis frequency: {packet.frequency_hz:.6g} Hz.")
        if packet.ac_requested_answers:
            answer_lines = []
            for goal_id, answer in packet.ac_requested_answers.items():
                answer_lines.append(
                    f"{goal_id}: {_format_complex(answer.magnitude, answer.phase_deg, answer.unit)}"
                )
            lines.append("Requested phasor answers: " + "; ".join(answer_lines) + ".")
        if packet.ac_sweep:
            lines.append(
                f"AC sweep produced {len(packet.ac_sweep)} verified frequency points. "
                "The UI table reports magnitude and phase for the requested phasor at each point."
            )
        passed_checks = [
            check.name for check in packet.verification.checks if check.passed
        ]
        lines.append(
            "Verification passed: "
            + ", ".join(passed_checks)
            + f". Max complex KCL residual = {packet.verification.max_kcl_residual_a:.3g} A. "
            + "AC complex power is not verified in this MVP."
        )
        return "\n\n".join(lines)

    lines = []
    lines.append(
        "Method: the circuit was converted to Circuit IR, solved with Modified "
        "Nodal Analysis, and then checked with deterministic KCL and power-balance "
        "tests."
    )

    if packet.node_voltages:
        formatted_nodes = [
            f"{node} = {_format_value(value, 'V')}"
            for node, value in sorted(packet.node_voltages.items())
        ]
        lines.append("Verified node voltages: " + "; ".join(formatted_nodes) + ".")

    if packet.requested_answers:
        answer_lines = []
        for goal_id, answer in packet.requested_answers.items():
            answer_lines.append(f"{goal_id}: {_format_value(answer.value, answer.unit)}")
        lines.append("Requested answers: " + "; ".join(answer_lines) + ".")

    passed_checks = [
        check.name for check in packet.verification.checks if check.passed
    ]
    lines.append(
        "Verification passed: "
        + ", ".join(passed_checks)
        + f". Max KCL residual = {packet.verification.max_kcl_residual_a:.3g} A; "
        + f"power-balance error = {packet.verification.power_balance_error_w:.3g} W."
    )

    lines.append(
        "Sign convention: component voltage is V(nodes[0]) - V(nodes[1]), current "
        "is positive from nodes[0] to nodes[1], and signed power is voltage times "
        "current. Negative source power means the source supplies power."
    )
    return "\n\n".join(lines)
