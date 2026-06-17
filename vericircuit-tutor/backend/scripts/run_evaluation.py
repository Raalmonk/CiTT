from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


CASES_DIR = ROOT / "tests" / "fixtures" / "benchmark_cases"


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


def _check_bme_expectations(packet, case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if case.get("requires_bme_metadata"):
        metadata = packet.bme_metadata
        if metadata is None:
            return ["missing BME metadata"]
        required_fields = {
            "biomedical_context": metadata.biomedical_context,
            "signal_chain_role": metadata.signal_chain_role,
            "typical_signal_range": metadata.typical_signal_range,
            "safety_note": metadata.safety_note,
        }
        for field, value in required_fields.items():
            if not value:
                failures.append(f"BME metadata missing {field}")
        if not metadata.what_students_should_learn:
            failures.append("BME metadata missing what_students_should_learn")
        if not metadata.common_lab_mistakes:
            failures.append("BME metadata missing common_lab_mistakes")
        if not metadata.real_world_nonidealities:
            failures.append("BME metadata missing real_world_nonidealities")

    expected_observations = set(case.get("expected_tutor_observations", []))
    if expected_observations:
        observed = {observation.id for observation in packet.tutor_observations}
        missing = sorted(expected_observations - observed)
        failures.extend(f"missing tutor observation {observation_id}" for observation_id in missing)

    return failures


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("mode") == "gemini_mock":
        return {
            "id": case["id"],
            "category": case.get("category", "uncategorized"),
            "source_file": case.get("source_file"),
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
    failures.extend(_check_bme_expectations(packet, case))
    if packet.status == "solved" and packet.verification_badge.label == "PASS" and packet.lesson_packet is None:
        failures.append("missing structured lesson_packet for solved PASS case")
    if packet.status != "solved" and packet.lesson_packet is not None:
        failures.append("lesson_packet should not be generated for unsolved case")

    return {
        "id": case["id"],
        "category": case.get("category", "uncategorized"),
        "source_file": case.get("source_file"),
        "circuit_id": parsed.circuit.id,
        "status": "passed" if not failures else "failed",
        "parser_used": parsed.parser_used,
        "packet_status": packet.status,
        "badge": packet.verification_badge.label,
        "failures": failures,
    }


def _load_cases() -> tuple[list[dict[str, Any]], list[str]]:
    cases: list[dict[str, Any]] = []
    case_files = sorted(CASES_DIR.glob("*_cases.json"))
    for path in case_files:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        for case in loaded:
            cases.append({"source_file": path.name, **case})
    return cases, [path.name for path in case_files]


def _summarize_by_category(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for result in results:
        counts[str(result["category"])][str(result["status"])] += 1
    return {
        category: {
            "passed": status_counts["passed"],
            "failed": status_counts["failed"],
            "skipped": status_counts["skipped"],
        }
        for category, status_counts in sorted(counts.items())
    }


def _build_report() -> dict[str, Any]:
    cases, case_files = _load_cases()
    results = [evaluate_case(case) for case in cases]
    failed = [result for result in results if result["status"] == "failed"]
    return {
        "case_files": case_files,
        "case_count": len(results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": len(failed),
        "skipped": sum(result["status"] == "skipped" for result in results),
        "summary_by_category": _summarize_by_category(results),
        "results": results,
    }


def _format_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# VeriCircuit Tutor Evaluation Report",
        "",
        f"- Case files: {', '.join(report['case_files'])}",
        f"- Cases: {report['case_count']}",
        f"- Passed: {report['passed']}",
        f"- Failed: {report['failed']}",
        f"- Skipped: {report['skipped']}",
        "",
        "## Summary By Category",
        "",
        "| Category | Passed | Failed | Skipped |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category, counts in report["summary_by_category"].items():
        lines.append(
            f"| {category} | {counts['passed']} | {counts['failed']} | {counts['skipped']} |"
        )

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Category | Circuit | Parser | Packet Status | Badge | Result |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for result in report["results"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(result["id"]),
                    str(result.get("category", "")),
                    str(result.get("circuit_id", "")),
                    str(result.get("parser_used", "")),
                    str(result.get("packet_status", "")),
                    str(result.get("badge", "")),
                    str(result["status"]),
                ]
            )
            + " |"
        )

    failed_results = [result for result in report["results"] if result["status"] == "failed"]
    if failed_results:
        lines.extend(["", "## Failures", ""])
        for result in failed_results:
            lines.append(f"- {result['id']}: {'; '.join(result['failures'])}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run offline VeriCircuit Tutor benchmark cases.")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Report format. Defaults to json.",
    )
    args = parser.parse_args(argv)

    report = _build_report()
    if args.format == "markdown":
        print(_format_markdown_report(report))
    else:
        print(json.dumps(report, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
