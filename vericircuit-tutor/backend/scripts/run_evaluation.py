from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "fixtures" / "benchmark_cases" / "core_cases.json"


def _within(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def _check_expected_answers(packet, expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for answer_id, spec in expected.items():
        answer = packet.requested_answers.get(answer_id)
        if answer is None:
            failures.append(f"missing requested answer {answer_id}")
            continue
        if answer.unit != spec["unit"]:
            failures.append(f"{answer_id} unit {answer.unit!r} != {spec['unit']!r}")
        if not _within(answer.value, float(spec["value"]), float(spec["tolerance"])):
            failures.append(f"{answer_id} value {answer.value} outside tolerance")
    return failures


def _check_expected_ac_answers(packet, expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for answer_id, spec in expected.items():
        answer = packet.ac_requested_answers.get(answer_id)
        if answer is None:
            failures.append(f"missing AC requested answer {answer_id}")
            continue
        tolerance = float(spec["tolerance"])
        if answer.unit != spec["unit"]:
            failures.append(f"{answer_id} unit {answer.unit!r} != {spec['unit']!r}")
        if not _within(answer.magnitude, float(spec["magnitude"]), tolerance):
            failures.append(f"{answer_id} magnitude {answer.magnitude} outside tolerance")
        if not _within(answer.phase_deg, float(spec["phase_deg"]), tolerance):
            failures.append(f"{answer_id} phase {answer.phase_deg} outside tolerance")
    return failures


def _check_expected_transient(packet, expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    response = packet.transient_response
    if response is None:
        return ["missing transient response"]
    for field, spec in expected.items():
        actual = getattr(response, field)
        if not _within(float(actual), float(spec["value"]), float(spec["tolerance"])):
            failures.append(f"{field} {actual} outside tolerance")
    return failures


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("mode") == "gemini_mock":
        return {
            "id": case["id"],
            "status": "skipped",
            "reason": "mocked Gemini fixtures are validated by pytest, not by network evaluation",
        }

    parsed = parse_problem(case["problem_text"], mode=case.get("mode", "demo"))
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)
    failures: list[str] = []
    if packet.status != case["expected_status"]:
        failures.append(f"status {packet.status!r} != {case['expected_status']!r}")
    if packet.verification_badge.label != case["expected_badge"]:
        failures.append(f"badge {packet.verification_badge.label!r} != {case['expected_badge']!r}")
    failures.extend(_check_expected_answers(packet, case.get("expected_answers", {})))
    failures.extend(_check_expected_ac_answers(packet, case.get("expected_ac_answers", {})))
    if "expected_transient" in case:
        failures.extend(_check_expected_transient(packet, case["expected_transient"]))
    if packet.status == "solved" and packet.verification_badge.label == "PASS" and packet.lesson_packet is None:
        failures.append("missing structured lesson_packet for solved PASS case")
    if packet.status != "solved" and packet.lesson_packet is not None:
        failures.append("lesson_packet should not be generated for unsolved case")

    return {
        "id": case["id"],
        "status": "passed" if not failures else "failed",
        "parser_used": parsed.parser_used,
        "packet_status": packet.status,
        "badge": packet.verification_badge.label,
        "failures": failures,
    }


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = [evaluate_case(case) for case in cases]
    failed = [result for result in results if result["status"] == "failed"]
    report = {
        "case_count": len(results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": len(failed),
        "skipped": sum(result["status"] == "skipped" for result in results),
        "results": results,
    }
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
