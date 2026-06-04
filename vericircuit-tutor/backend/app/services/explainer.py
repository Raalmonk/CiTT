from __future__ import annotations

from app.models.solution_packet import SolutionPacket


def _format_value(value: float, unit: str) -> str:
    abs_value = abs(value)
    if unit == "A" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mA"
    if unit == "W" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mW"
    return f"{value:.6g} {unit}"


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

    lines: list[str] = []
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

