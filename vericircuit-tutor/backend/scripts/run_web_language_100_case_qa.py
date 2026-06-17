from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from app.models.circuit_ir import CircuitProblem, Component
from app.services.gemini_client import gemini_is_configured
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit
from run_tutor_100_case_qa import TutorQACase, build_cases, evaluate_case


@dataclass(frozen=True)
class SourceRef:
    title: str
    url: str
    note: str


@dataclass(frozen=True)
class WebLanguageCase:
    index: int
    source: SourceRef
    prompt: str
    expected: TutorQACase


SOURCE_REFS = {
    "voltage_divider": SourceRef(
        title="All About Circuits: Voltage Divider Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/",
        note="Worksheet includes voltage divider calculation/design prompts.",
    ),
    "current_divider": SourceRef(
        title="All About Circuits: Current Divider Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/current-divider-circuits/",
        note="Worksheet asks students to draw, construct, and mathematically analyze current-divider circuits.",
    ),
    "bridge": SourceRef(
        title="All About Circuits: DC Bridge Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/",
        note="Worksheet covers two-divider/bridge midpoint voltages and differential bridge readings.",
    ),
    "generic_dc": SourceRef(
        title="All About Circuits: Kirchhoff's Laws Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/",
        note="Worksheet emphasizes meter readings, signed voltages, and KCL/KVL reasoning in DC networks.",
    ),
    "rc_low_pass_ac": SourceRef(
        title="All About Circuits: Series and Parallel AC Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/",
        note="Worksheet includes AC impedance and frequency-domain circuit exercises.",
    ),
    "rc_transient": SourceRef(
        title="All About Circuits: Time Constant Calculations Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/time-constant-calculations/",
        note="Worksheet covers RC time constants and transient calculations.",
    ),
    "bme:bme_anti_aliasing_low_pass": SourceRef(
        title="All About Circuits: Series and Parallel AC Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/",
        note="Used as a public AC filter/impedance source pattern for anti-aliasing RC prompts.",
    ),
    "bme:bme_anti_aliasing_low_pass:value_variant": SourceRef(
        title="All About Circuits: Series and Parallel AC Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/",
        note="Used as a public AC filter/impedance source pattern for anti-aliasing RC prompts.",
    ),
    "bme:bme_ecg_front_end": SourceRef(
        title="All About Circuits: Inverting and Noninverting OpAmp Voltage Amplifier Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/inverting-and-noninverting-opamp-voltage-amplifier-circuits/",
        note="Worksheet asks students to draw schematics and analyze ideal op-amp voltage amplifier values.",
    ),
    "bme:bme_ecg_front_end:value_variant": SourceRef(
        title="All About Circuits: Inverting and Noninverting OpAmp Voltage Amplifier Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/inverting-and-noninverting-opamp-voltage-amplifier-circuits/",
        note="Worksheet asks students to draw schematics and analyze ideal op-amp voltage amplifier values.",
    ),
    "bme:bme_emg_band_pass_chain": SourceRef(
        title="All About Circuits: Series and Parallel AC Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/",
        note="Used as a public AC impedance/filter source pattern for cascaded RC prompts.",
    ),
    "bme:bme_emg_band_pass_chain:value_variant": SourceRef(
        title="All About Circuits: Series and Parallel AC Circuits Worksheet",
        url="https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/",
        note="Used as a public AC impedance/filter source pattern for cascaded RC prompts.",
    ),
    "bme:bme_instrumentation_amplifier": SourceRef(
        title="Electronics Tutorials: Instrumentation Amplifier",
        url="https://www.electronics-tutorials.ws/opamp/instrumentation-amplifier.html",
        note="Article explains instrumentation amplifier topology and worked examples.",
    ),
    "bme:bme_instrumentation_amplifier:value_variant": SourceRef(
        title="Electronics Tutorials: Instrumentation Amplifier",
        url="https://www.electronics-tutorials.ws/opamp/instrumentation-amplifier.html",
        note="Article explains instrumentation amplifier topology and worked examples.",
    ),
    "bme:bme_photodiode_tia": SourceRef(
        title="RP Photonics: Photodiode Amplifiers",
        url="https://www.rp-photonics.com/photodiode_amplifiers.html",
        note="Article describes photodiode transimpedance amplifiers converting photocurrent into voltage.",
    ),
    "bme:bme_photodiode_tia:value_variant": SourceRef(
        title="RP Photonics: Photodiode Amplifiers",
        url="https://www.rp-photonics.com/photodiode_amplifiers.html",
        note="Article describes photodiode transimpedance amplifiers converting photocurrent into voltage.",
    ),
}


def _component(circuit: CircuitProblem, component_id: str) -> Component:
    return next(component for component in circuit.components if component.id == component_id)


def _value(component: Component) -> str:
    if component.type == "resistor":
        if component.value >= 1000:
            return f"{component.value / 1000:.6g} kOhm"
        return f"{component.value:.6g} ohm"
    if component.type == "capacitor":
        if component.value < 1e-6:
            return f"{component.value * 1e9:.6g} nF"
        return f"{component.value * 1e6:.6g} uF"
    if component.type == "current_source":
        if abs(component.value) < 1:
            return f"{component.value * 1000:.6g} mA"
        return f"{component.value:.6g} A"
    if component.type == "voltage_source":
        return f"{component.value:.6g} V"
    return f"{component.value:.6g} {component.unit}"


def _goal_text(circuit: CircuitProblem) -> str:
    parts = []
    for goal in circuit.goals:
        if goal.quantity == "node_voltage":
            parts.append(f"node voltage at {goal.target} relative to {circuit.ground_node}")
        elif goal.quantity == "component_current":
            component = _component(circuit, goal.target)
            parts.append(f"current through {component.id} from {component.nodes[0]} to {component.nodes[1]}")
        elif goal.quantity == "component_voltage":
            component = _component(circuit, goal.target)
            parts.append(f"voltage across {component.id} from {component.nodes[0]} to {component.nodes[1]}")
        elif goal.quantity == "component_power":
            parts.append(f"signed power for {goal.target}")
        else:
            parts.append(f"{goal.quantity} for {goal.target}")
    return "; ".join(parts)


def _prompt_for_case(case: TutorQACase, index: int) -> str:
    circuit = case.circuit
    components = {component.id: component for component in circuit.components}
    if case.family == "voltage_divider":
        source = next(component for component in circuit.components if component.type == "voltage_source")
        resistors = [component for component in circuit.components if component.type == "resistor"]
        return (
            "Generate a circuit model from this description, not just a numeric answer: "
            f"a {_value(source)} DC source has its positive terminal at {source.nodes[0]} and negative terminal at ground {source.nodes[1]}. "
            f"{resistors[0].id} = {_value(resistors[0])} connects {resistors[0].nodes[0]} to {resistors[0].nodes[1]}, "
            f"and {resistors[1].id} = {_value(resistors[1])} connects {resistors[1].nodes[0]} to {resistors[1].nodes[1]}. "
            f"Create the Circuit IR/schematic focus and request {_goal_text(circuit)}."
        )
    if case.family == "current_divider":
        source = next(component for component in circuit.components if component.type == "current_source")
        resistors = [component for component in circuit.components if component.type == "resistor"]
        branches = ", ".join(
            f"{resistor.id} = {_value(resistor)} from {resistor.nodes[0]} to {resistor.nodes[1]}"
            for resistor in resistors
        )
        return (
            "Turn this human-language current-divider setup into Circuit IR: "
            f"an ideal {_value(source)} current source points from {source.nodes[0]} into {source.nodes[1]}. "
            f"The parallel branch resistors are {branches}. "
            f"Use {circuit.ground_node} as ground and request {_goal_text(circuit)}."
        )
    if case.family == "bridge":
        source = next(component for component in circuit.components if component.type == "voltage_source")
        resistors = [component for component in circuit.components if component.type == "resistor"]
        edges = "; ".join(
            f"{resistor.id} = {_value(resistor)} between {resistor.nodes[0]} and {resistor.nodes[1]}"
            for resistor in resistors
        )
        return (
            "Create a graph-style circuit representation for a bridge network: "
            f"{source.id} is a {_value(source)} DC source from {source.nodes[0]} to {source.nodes[1]}; "
            f"the resistor edges are {edges}. "
            f"The requested measurements are {_goal_text(circuit)}."
        )
    if case.family == "generic_dc":
        source = next(component for component in circuit.components if component.type == "voltage_source")
        current_source = next(component for component in circuit.components if component.type == "current_source")
        resistors = [component for component in circuit.components if component.type == "resistor"]
        edges = "; ".join(
            f"{resistor.id} {_value(resistor)} from {resistor.nodes[0]} to {resistor.nodes[1]}"
            for resistor in resistors
        )
        return (
            "Generate the circuit, nodes, and goals from this loaded DC network description: "
            f"{source.id} fixes {source.nodes[0]} at {_value(source)} relative to {source.nodes[1]}; "
            f"resistor connections are {edges}; "
            f"{current_source.id} is an ideal {_value(current_source)} source from {current_source.nodes[0]} to {current_source.nodes[1]}. "
            f"Request {_goal_text(circuit)}."
        )
    if case.family == "rc_low_pass_ac":
        source = next(component for component in circuit.components if component.type == "voltage_source")
        resistor = next(component for component in circuit.components if component.type == "resistor")
        capacitor = next(component for component in circuit.components if component.type == "capacitor")
        sweep_text = (
            f"Use an AC sweep from {circuit.sweep.start_hz:.6g} Hz to {circuit.sweep.stop_hz:.6g} Hz"
            if circuit.sweep
            else f"Analyze it at {circuit.frequency_hz:.6g} Hz"
        )
        return (
            "Build an AC phasor Circuit IR for this RC low-pass description: "
            f"the source {source.id} is {source.ac_magnitude:.6g} V angle {source.ac_phase_deg:.6g} degrees from {source.nodes[0]} to {source.nodes[1]}; "
            f"{resistor.id} = {_value(resistor)} from {resistor.nodes[0]} to {resistor.nodes[1]}; "
            f"{capacitor.id} = {_value(capacitor)} from {capacitor.nodes[0]} to {capacitor.nodes[1]}. "
            f"{sweep_text}. Request {_goal_text(circuit)}."
        )
    if case.family == "rc_transient":
        source = next(component for component in circuit.components if component.type == "voltage_source")
        resistor = next(component for component in circuit.components if component.type == "resistor")
        capacitor = next(component for component in circuit.components if component.type == "capacitor")
        return (
            "Create a first-order RC transient circuit from this statement: "
            f"{source.id} is a {_value(source)} step source from {source.nodes[0]} to {source.nodes[1]}; "
            f"{resistor.id} = {_value(resistor)} connects {resistor.nodes[0]} to {resistor.nodes[1]}; "
            f"{capacitor.id} = {_value(capacitor)} connects {capacitor.nodes[0]} to {capacitor.nodes[1]}; "
            f"the capacitor starts at {circuit.transient.initial_voltage_v:.6g} V. "
            f"Request {_goal_text(circuit)} at the listed transient sample times."
        )
    if case.family.startswith("bme:"):
        compact_components = []
        for component in circuit.components:
            if component.type in {"resistor", "capacitor", "current_source", "voltage_source"}:
                compact_components.append(
                    f"{component.id} {component.type} {_value(component)} nodes {component.nodes}"
                )
            elif component.type in {"op_amp_ideal", "ideal_op_amp"}:
                compact_components.append(f"{component.id} ideal op-amp nodes {component.nodes}")
        return (
            "Generate Circuit IR from this biomedical-flavored but fully explicit circuit description. "
            "Do not infer medical safety facts; just parse the stated ideal circuit. "
            f"Components: {'; '.join(compact_components)}. "
            f"Analysis type is {circuit.analysis_type}; request {_goal_text(circuit)}."
        )
    raise ValueError(f"Unhandled family {case.family}")


def build_web_language_cases() -> list[WebLanguageCase]:
    cases = build_cases()
    web_cases = []
    for index, case in enumerate(cases, start=1):
        source = SOURCE_REFS.get(case.family)
        if source is None:
            source = SOURCE_REFS[case.family.split(":value_variant")[0]]
        web_cases.append(
            WebLanguageCase(
                index=index,
                source=source,
                prompt=_prompt_for_case(case, index),
                expected=case,
            )
        )
    return web_cases


def _component_signature(circuit: CircuitProblem) -> dict[str, list[float]]:
    signature: dict[str, list[float]] = {}
    for component in circuit.components:
        signature.setdefault(component.type, []).append(float(component.value))
    for values in signature.values():
        values.sort()
    return signature


def _close_lists(left: list[float], right: list[float]) -> bool:
    if len(left) != len(right):
        return False
    return all(math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-12) for a, b in zip(left, right))


def _compare_parsed_to_expected(parsed: CircuitProblem, expected: CircuitProblem) -> list[str]:
    failures = []
    if parsed.analysis_type != expected.analysis_type:
        failures.append(f"analysis_type {parsed.analysis_type} != {expected.analysis_type}")
    if len(parsed.goals) != len(expected.goals):
        failures.append(f"goal count {len(parsed.goals)} != {len(expected.goals)}")
    parsed_signature = _component_signature(parsed)
    expected_signature = _component_signature(expected)
    if set(parsed_signature) != set(expected_signature):
        failures.append(f"component types {sorted(parsed_signature)} != {sorted(expected_signature)}")
    else:
        for component_type, expected_values in expected_signature.items():
            if not _close_lists(parsed_signature[component_type], expected_values):
                failures.append(f"{component_type} values do not match expected set")
    return failures


def _evaluate_expected_path(case: WebLanguageCase) -> dict[str, Any]:
    qa = evaluate_case(case.expected, case.index)
    return {
        "score": qa["score"],
        "status": qa["status"],
        "badge": qa["badge"],
        "step_ids": qa["step_ids"],
        "issues": qa["issues"],
    }


def _evaluate_parser_path(case: WebLanguageCase, mode: str) -> dict[str, Any]:
    parsed = parse_problem(case.prompt, mode=mode)
    failures = []
    if parsed.parser_used != "gemini":
        failures.append(f"parser_used={parsed.parser_used}")
    failures.extend(_compare_parsed_to_expected(parsed.circuit, case.expected.circuit))
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)
    if packet.verification_badge.label != "PASS":
        failures.append(f"parsed circuit did not solve PASS: {packet.verification_badge.label}")
    return {
        "parser_used": parsed.parser_used,
        "warnings": parsed.warnings,
        "failures": failures,
        "status": "passed" if not failures else "failed",
    }


def _summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    expected_scores = [result["expected_path"]["score"] for result in results]
    parser_results = [result.get("parser_path") for result in results if result.get("parser_path")]
    return {
        "case_count": len(results),
        "expected_path_average_score": round(mean(expected_scores), 2),
        "expected_path_min_score": min(expected_scores),
        "parser_path_ran": len(parser_results),
        "parser_path_passed": sum(item["status"] == "passed" for item in parser_results),
    }


def _markdown_report(results: list[dict[str, Any]], parser_mode: str | None) -> str:
    summary = _summary(results)
    lines = [
        "# Web-Sourced Human-Language 100-Case QA",
        "",
        "These cases are source-backed paraphrases: each prompt is written in our own words, with a public source URL recording the worksheet or article pattern it was based on. The benchmark tests natural-language circuit generation intent, not copied textbook wording.",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Expected-IR solver/lesson average score: {summary['expected_path_average_score']}/10",
        f"- Expected-IR minimum score: {summary['expected_path_min_score']}/10",
        f"- Live parser mode: {parser_mode or 'not run'}",
        f"- Live parser cases run: {summary['parser_path_ran']}",
        f"- Live parser cases passed: {summary['parser_path_passed']}",
        "",
        "To run the live human-language parser path, set `GEMINI_API_KEY` or `GOOGLE_API_KEY` and run:",
        "",
        "```bash",
        "python backend/scripts/run_web_language_100_case_qa.py --parser-mode gemini_strict --markdown docs/web_language_100_case_qa.md",
        "```",
        "",
        "## Source Families",
        "",
    ]
    seen = set()
    for result in results:
        source = result["source"]
        if source["url"] in seen:
            continue
        seen.add(source["url"])
        lines.append(f"- [{source['title']}]({source['url']}): {source['note']}")

    lines.extend(["", "## Sample Natural-Language Inputs", ""])
    for result in results[:8]:
        lines.append(f"### {result['index']:03d}. {result['id']}")
        lines.append("")
        lines.append(f"- Source: [{result['source']['title']}]({result['source']['url']})")
        lines.append(f"- Expected lens: {result['expected_lens']}")
        lines.append(f"- Prompt: {result['prompt']}")
        lines.append(f"- Expected path steps: {', '.join(result['expected_path']['step_ids'])}")
        lines.append("")

    lines.extend(["## Full 100-Case Index", ""])
    for result in results:
        parser_status = result.get("parser_path", {}).get("status", "not_run")
        lines.append(
            f"- {result['index']:03d} `{result['id']}` [{result['family']}] "
            f"source=[{result['source']['title']}]({result['source']['url']}) "
            f"expected_score={result['expected_path']['score']} parser={parser_status}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parser-mode", choices=["gemini", "gemini_strict"], help="Optionally run live parser on the 100 natural-language prompts.")
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    parser.add_argument("--markdown", type=Path, help="Optional Markdown output path.")
    args = parser.parse_args()

    run_parser = bool(args.parser_mode)
    if run_parser and not gemini_is_configured():
        print("Gemini API key is not configured; live parser path will be skipped.", file=sys.stderr)
        run_parser = False

    results = []
    for case in build_web_language_cases():
        result: dict[str, Any] = {
            "index": case.index,
            "id": case.expected.circuit.id,
            "family": case.expected.family,
            "expected_lens": case.expected.expected_lens,
            "source": {
                "title": case.source.title,
                "url": case.source.url,
                "note": case.source.note,
            },
            "prompt": case.prompt,
            "expected_circuit_ir": case.expected.circuit.model_dump(),
            "expected_path": _evaluate_expected_path(case),
        }
        if run_parser and args.parser_mode:
            result["parser_path"] = _evaluate_parser_path(case, args.parser_mode)
        results.append(result)

    report = {"summary": _summary(results), "results": results}
    print(json.dumps(report["summary"], indent=2, sort_keys=True))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(_markdown_report(results, args.parser_mode if run_parser else None), encoding="utf-8")

    if run_parser:
        failures = [
            result
            for result in results
            if result.get("parser_path", {}).get("status") != "passed"
        ]
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
