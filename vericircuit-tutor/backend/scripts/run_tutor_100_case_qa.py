from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.circuit_ir import ACSweep, CircuitProblem, Component, Goal, RCTransient
from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.lesson_builder import lesson_has_unverified_numeric_claims
from app.services.pipeline import solve_circuit
from app.services.optcpv_bridge import render_optcpv_schematic_svg
from app.services.variant_generator import generate_goal_variant, generate_value_variant


TOTAL_CASES = 100


@dataclass(frozen=True)
class TutorQACase:
    family: str
    circuit: CircuitProblem
    expected_lens: str


def _goal_node(goal_id: str, node: str, ground: str) -> Goal:
    return Goal(
        id=goal_id,
        quantity="node_voltage",
        target=node,
        reference={"positive_node": node, "negative_node": ground},
    )


def _goal_component_current(goal_id: str, component: Component) -> Goal:
    return Goal(
        id=goal_id,
        quantity="component_current",
        target=component.id,
        reference={"from_node": component.nodes[0], "to_node": component.nodes[1]},
    )


def _goal_component_voltage(goal_id: str, component: Component) -> Goal:
    return Goal(
        id=goal_id,
        quantity="component_voltage",
        target=component.id,
        reference={"positive_node": component.nodes[0], "negative_node": component.nodes[1]},
    )


def _goal_component_power(goal_id: str, component: Component) -> Goal:
    return Goal(
        id=goal_id,
        quantity="component_power",
        target=component.id,
        reference={"component": component.id},
    )


def _voltage_divider_case(index: int) -> TutorQACase:
    ground = "0" if index % 3 else "gnd"
    top = f"vin_{index}"
    out = f"sense_{index}"
    source = Component(
        id=f"V{index}",
        type="voltage_source",
        nodes=[top, ground],
        value=5.0 + (index % 5) * 1.5,
        unit="V",
    )
    upper = Component(
        id=f"Rtop{index}",
        type="resistor",
        nodes=[top, out],
        value=1000.0 + 250.0 * (index % 7),
        unit="ohm",
    )
    lower = Component(
        id=f"Rbot{index}",
        type="resistor",
        nodes=[out, ground],
        value=1500.0 + 400.0 * (index % 6),
        unit="ohm",
    )
    goal_options = [
        [_goal_node(f"{out}_voltage", out, ground)],
        [_goal_component_voltage(f"{lower.id}_voltage", lower)],
        [_goal_component_current(f"{upper.id}_current", upper)],
        [_goal_component_power(f"{lower.id}_power", lower)],
    ]
    circuit = CircuitProblem(
        id=f"qa_voltage_divider_{index:02d}",
        title=f"QA Voltage Divider {index}",
        analysis_type="dc_operating_point",
        topology_id=None if index % 2 else "voltage_divider",
        ground_node=ground,
        nodes=[ground, top, out],
        components=[source, upper, lower],
        goals=goal_options[index % len(goal_options)],
        assumptions=["QA generated simple divider; midpoint has no extra branch."],
    )
    return TutorQACase("voltage_divider", circuit, "divider")


def _current_divider_case(index: int) -> TutorQACase:
    ground = "0"
    top = f"bus_{index}"
    branch_count = 2 + (index % 3)
    source = Component(
        id=f"I{index}",
        type="current_source",
        nodes=[ground, top],
        value=(1.5 + 0.2 * index) * 1e-3,
        unit="A",
    )
    resistors = [
        Component(
            id=f"Rb{index}_{branch}",
            type="resistor",
            nodes=[top, ground],
            value=1000.0 + 550.0 * branch + 80.0 * index,
            unit="ohm",
        )
        for branch in range(1, branch_count + 1)
    ]
    goals = [_goal_node(f"{top}_voltage", top, ground)]
    goals.extend(_goal_component_current(f"{resistor.id}_current", resistor) for resistor in resistors[:2])
    circuit = CircuitProblem(
        id=f"qa_current_divider_{index:02d}",
        title=f"QA Current Divider {index}",
        analysis_type="dc_operating_point",
        topology_id=None if index % 2 else "current_divider",
        ground_node=ground,
        nodes=[ground, top],
        components=[source, *resistors],
        goals=goals,
        assumptions=["QA generated parallel branch current divider."],
    )
    return TutorQACase("current_divider", circuit, "current_divider")


def _bridge_case(index: int) -> TutorQACase:
    ground = "0"
    source_node = f"src_{index}"
    left = f"left_{index}"
    right = f"right_{index}"
    source = Component(
        id=f"Vb{index}",
        type="voltage_source",
        nodes=[source_node, ground],
        value=6.0 + index % 7,
        unit="V",
    )
    r1 = Component(id=f"R1b{index}", type="resistor", nodes=[source_node, left], value=900.0 + 30 * index, unit="ohm")
    r2 = Component(id=f"R2b{index}", type="resistor", nodes=[left, ground], value=1400.0 + 40 * index, unit="ohm")
    r3 = Component(id=f"R3b{index}", type="resistor", nodes=[source_node, right], value=1200.0 + 50 * index, unit="ohm")
    r4 = Component(id=f"R4b{index}", type="resistor", nodes=[right, ground], value=1600.0 + 60 * index, unit="ohm")
    r5 = Component(id=f"R5b{index}", type="resistor", nodes=[left, right], value=2000.0 + 70 * index, unit="ohm")
    circuit = CircuitProblem(
        id=f"qa_bridge_{index:02d}",
        title=f"QA Bridge Network {index}",
        analysis_type="dc_operating_point",
        topology_id="bridge_network" if index % 2 == 0 else None,
        ground_node=ground,
        nodes=[ground, source_node, left, right],
        components=[source, r1, r2, r3, r4, r5],
        goals=[
            _goal_node(f"{left}_voltage", left, ground),
            _goal_node(f"{right}_voltage", right, ground),
            _goal_component_current(f"{r5.id}_current", r5),
        ],
        assumptions=["QA generated bridge network with a midpoint coupling branch."],
    )
    return TutorQACase("bridge", circuit, "coupled_nodes")


def _generic_dc_case(index: int) -> TutorQACase:
    ground = "0"
    source_node = f"rail_{index}"
    node_a = f"a_{index}"
    node_b = f"b_{index}"
    source = Component(
        id=f"Vg{index}",
        type="voltage_source",
        nodes=[source_node, ground],
        value=4.5 + 0.5 * (index % 6),
        unit="V",
    )
    r1 = Component(id=f"Ra_top{index}", type="resistor", nodes=[source_node, node_a], value=1200.0 + 50 * index, unit="ohm")
    r2 = Component(id=f"Ra_bot{index}", type="resistor", nodes=[node_a, ground], value=1800.0 + 70 * index, unit="ohm")
    load = Component(id=f"Iload{index}", type="current_source", nodes=[node_b, ground], value=(0.2 + 0.03 * index) * 1e-3, unit="A")
    r3 = Component(id=f"Rb_top{index}", type="resistor", nodes=[source_node, node_b], value=1500.0 + 40 * index, unit="ohm")
    r4 = Component(id=f"Rb_bot{index}", type="resistor", nodes=[node_b, ground], value=2200.0 + 80 * index, unit="ohm")
    circuit = CircuitProblem(
        id=f"qa_generic_dc_{index:02d}",
        title=f"QA Generic DC Network {index}",
        analysis_type="dc_operating_point",
        topology_id=None,
        ground_node=ground,
        nodes=[ground, source_node, node_a, node_b],
        components=[source, r1, r2, r3, r4, load],
        goals=[
            _goal_node(f"{node_b}_voltage", node_b, ground),
            _goal_component_current(f"{load.id}_current", load),
        ],
        assumptions=["QA generated non-motif DC network with one loaded divider branch."],
    )
    return TutorQACase("generic_dc", circuit, "node_relationships")


def _rc_low_pass_case(index: int) -> TutorQACase:
    ground = "0"
    input_node = f"ac_in_{index}"
    output_node = f"ac_out_{index}"
    source = Component(
        id=f"Vac{index}",
        type="voltage_source",
        nodes=[input_node, ground],
        value=0.0,
        unit="V",
        ac_magnitude=0.5 + 0.1 * (index % 5),
        ac_phase_deg=0.0,
    )
    resistor = Component(id=f"Rac{index}", type="resistor", nodes=[input_node, output_node], value=1000.0 + 150 * index, unit="ohm")
    capacitor = Component(id=f"Cac{index}", type="capacitor", nodes=[output_node, ground], value=(47.0 + index) * 1e-9, unit="F")
    circuit = CircuitProblem(
        id=f"qa_rc_low_pass_{index:02d}",
        title=f"QA RC Low-Pass {index}",
        analysis_type="ac_steady_state" if index % 4 else "ac_sweep",
        topology_id=None if index % 2 else "rc_low_pass",
        frequency_hz=100.0 + 90.0 * index,
        sweep=ACSweep(start_hz=10.0, stop_hz=10000.0, points_per_decade=3) if index % 4 == 0 else None,
        ground_node=ground,
        nodes=[ground, input_node, output_node],
        components=[source, resistor, capacitor],
        goals=[_goal_node(f"{output_node}_phasor", output_node, ground)],
        assumptions=["QA generated first-order RC low-pass AC case."],
    )
    return TutorQACase("rc_low_pass_ac", circuit, "ac_low_pass")


def _rc_transient_case(index: int) -> TutorQACase:
    ground = "0"
    source_node = f"step_{index}"
    cap_node = f"vc_{index}"
    source = Component(
        id=f"Vstep{index}",
        type="voltage_source",
        nodes=[source_node, ground],
        value=3.0 + 0.25 * index,
        unit="V",
    )
    resistor = Component(id=f"Rt{index}", type="resistor", nodes=[source_node, cap_node], value=1000.0 + 100 * index, unit="ohm")
    capacitor = Component(id=f"Ct{index}", type="capacitor", nodes=[cap_node, ground], value=(0.47 + 0.05 * index) * 1e-6, unit="F")
    circuit = CircuitProblem(
        id=f"qa_rc_transient_{index:02d}",
        title=f"QA RC Transient {index}",
        analysis_type="rc_transient",
        topology_id=None,
        ground_node=ground,
        nodes=[ground, source_node, cap_node],
        components=[source, resistor, capacitor],
        goals=[_goal_component_voltage(f"{capacitor.id}_voltage", capacitor)],
        transient=RCTransient(
            capacitor_id=capacitor.id,
            initial_voltage_v=0.1 * (index % 3),
            time_points_s=[0.0, 0.001, 0.005],
        ),
        assumptions=["QA generated first-order RC charging transient."],
    )
    return TutorQACase("rc_transient", circuit, "rc_transient")


def _bme_cases() -> list[TutorQACase]:
    cases: list[TutorQACase] = []
    for template_id in sorted(BME_TEMPLATE_FACTORIES):
        base = BME_TEMPLATE_FACTORIES[template_id]().circuit_problem
        lens = "bme"
        if "bridge" in template_id or "wheatstone" in template_id:
            lens = "coupled_nodes"
        elif "low_pass" in template_id or "band_pass" in template_id:
            lens = "ac_low_pass"
        elif "tia" in template_id:
            lens = "transimpedance"
        elif "ecg" in template_id:
            lens = "differential_amp"
        cases.append(TutorQACase(f"bme:{template_id}", base, lens))
        cases.append(TutorQACase(f"bme:{template_id}:value_variant", generate_value_variant(base), lens))
        if len(cases) >= 20:
            break
    return cases[:20]


def build_cases() -> list[TutorQACase]:
    cases: list[TutorQACase] = []
    cases.extend(_voltage_divider_case(index) for index in range(1, 21))
    cases.extend(_current_divider_case(index) for index in range(1, 16))
    cases.extend(_bridge_case(index) for index in range(1, 21))
    cases.extend(_generic_dc_case(index) for index in range(1, 11))
    cases.extend(_rc_low_pass_case(index) for index in range(1, 16))
    cases.extend(_rc_transient_case(index) for index in range(1, 11))
    cases.extend(_bme_cases())
    return cases[:TOTAL_CASES]


def _svg_elements(svg: str):
    root = ET.fromstring(svg)
    return list(root.iter())


def _focus_ids_query_svg(circuit: CircuitProblem, packet) -> list[str]:
    try:
        elements = _svg_elements(render_optcpv_schematic_svg(circuit))
    except Exception as exc:  # noqa: BLE001 - QA report should capture renderer failures.
        return [f"schematic render failed: {exc}"]

    failures: list[str] = []
    for step in packet.guided_steps:
        for component_id in step.focus.components:
            if not any(element.attrib.get("data-component-id") == component_id for element in elements):
                failures.append(f"{step.id}: missing component focus in SVG: {component_id}")
        for node_id in step.focus.nodes:
            if not any(element.attrib.get("data-node-id") == node_id for element in elements):
                failures.append(f"{step.id}: missing node focus in SVG: {node_id}")
        for component_id in step.focus.current_paths:
            if not any(
                element.attrib.get("data-component-id") == component_id
                and "current-path" in element.attrib.get("class", "").split()
                for element in elements
            ):
                failures.append(f"{step.id}: missing current-path focus in SVG: {component_id}")
    return failures


def _step_has_focus(step) -> bool:
    return bool(step.focus.components or step.focus.nodes or step.focus.goals or step.focus.current_paths)


def _requested_value_ids(packet) -> set[str]:
    ids = set(packet.requested_answers)
    for answer_id in packet.ac_requested_answers:
        ids.add(f"{answer_id}_magnitude")
        ids.add(f"{answer_id}_phase")
    if packet.transient_response is not None:
        ids.update({"initial_capacitor_voltage", "final_capacitor_voltage", "time_constant"})
    return ids


def _readout_index(packet) -> int | None:
    readout_words = ("output", "answer", "requested", "phasor", "exponential")
    for index, step in enumerate(packet.guided_steps):
        if any(word in step.id for word in readout_words):
            return index
    return None


def _early_answer_leaks(packet) -> list[str]:
    readout_index = _readout_index(packet)
    if readout_index is None:
        return []
    requested = _requested_value_ids(packet)
    leaks = []
    for step in packet.guided_steps[:readout_index]:
        leaked_ids = requested & {value.id for value in step.verified_values}
        if leaked_ids:
            leaks.append(f"{step.id}: {', '.join(sorted(leaked_ids))}")
    return leaks


def _lens_failures(expected_lens: str, step_ids: list[str]) -> list[str]:
    joined = " ".join(step_ids)
    if expected_lens == "divider" and "divider_series_path" not in step_ids:
        return ["expected divider series-path explanation"]
    if expected_lens == "current_divider" and "current_divider_parallel_branches" not in step_ids:
        return ["expected current-divider branch explanation"]
    if expected_lens == "coupled_nodes" and not (
        "dc_coupled_node_map" in step_ids or "differential_sources" in step_ids
    ):
        return ["expected coupled-node or differential explanation"]
    if expected_lens == "node_relationships" and "dc_node_relationships" not in step_ids:
        return ["expected generic node-relationship explanation"]
    if expected_lens == "ac_low_pass" and "ac_low_pass_pole" not in step_ids:
        if "band" not in joined and "ac_requested_output" not in step_ids:
            return ["expected AC filter explanation"]
    if expected_lens == "rc_transient" and "rc_time_constant" not in step_ids:
        return ["expected RC time-constant explanation"]
    if expected_lens == "transimpedance" and "tia_summing_node" not in step_ids:
        return ["expected TIA summing-node explanation"]
    if expected_lens == "differential_amp" and "differential_sources" not in step_ids:
        return ["expected differential-source explanation"]
    return []


def _quality_score(
    packet,
    focus_failures: list[str],
    lens_failures: list[str],
    early_leaks: list[str],
    numeric_failure: bool,
) -> tuple[int, list[str]]:
    issues: list[str] = []
    score = 10
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return 0, [f"not solved PASS: status={packet.status}, badge={packet.verification_badge.label}"]
    if packet.lesson_packet is None:
        return 0, ["missing lesson_packet"]
    if numeric_failure:
        score -= 3
        issues.append("unverified numeric claim detected")
    if focus_failures:
        score -= 2
        issues.append(f"{len(focus_failures)} focus IDs do not map to SVG")
    empty_focus = [step.id for step in packet.guided_steps if not _step_has_focus(step)]
    if empty_focus:
        score -= 1
        issues.append(f"steps without focus: {', '.join(empty_focus[:3])}")
    if lens_failures:
        score -= 3
        issues.extend(lens_failures)
    if early_leaks:
        score -= 2
        issues.append(f"early answer reveal: {'; '.join(early_leaks[:2])}")
    if not all(step.look_at and step.why_it_matters and step.common_mistake for step in packet.guided_steps[:-1]):
        score -= 1
        issues.append("some teaching fields are missing before verification")
    return max(score, 0), issues


def evaluate_case(case: TutorQACase, index: int) -> dict[str, object]:
    packet = solve_circuit(case.circuit, parser_used="qa_generated")
    step_ids = [step.id for step in packet.guided_steps]
    focus_failures = _focus_ids_query_svg(case.circuit, packet) if packet.guided_steps else []
    lens_failures = _lens_failures(case.expected_lens, step_ids)
    early_leaks = _early_answer_leaks(packet)
    numeric_failure = bool(packet.lesson_packet and lesson_has_unverified_numeric_claims(packet.lesson_packet))
    score, issues = _quality_score(packet, focus_failures, lens_failures, early_leaks, numeric_failure)
    return {
        "index": index,
        "id": case.circuit.id,
        "title": case.circuit.title,
        "family": case.family,
        "expected_lens": case.expected_lens,
        "status": packet.status,
        "badge": packet.verification_badge.label,
        "score": score,
        "step_ids": step_ids,
        "step_count": len(step_ids),
        "focus_failure_count": len(focus_failures),
        "focus_failures": focus_failures[:5],
        "early_answer_leaks": early_leaks,
        "issues": issues,
    }


def _counter(results: Iterable[dict[str, object]], key: str) -> Counter:
    return Counter(str(result[key]) for result in results)


def _summary(results: list[dict[str, object]]) -> dict[str, object]:
    scores = [int(result["score"]) for result in results]
    by_family: dict[str, list[int]] = defaultdict(list)
    for result in results:
        by_family[str(result["family"])].append(int(result["score"]))
    issue_counter: Counter[str] = Counter()
    for result in results:
        for issue in result["issues"]:
            issue_counter[str(issue)] += 1
    return {
        "case_count": len(results),
        "solved_pass": sum(result["status"] == "solved" and result["badge"] == "PASS" for result in results),
        "average_score": round(mean(scores), 2) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "family_counts": dict(_counter(results, "family")),
        "family_average_scores": {
            family: round(mean(values), 2)
            for family, values in sorted(by_family.items())
        },
        "issue_counts": dict(issue_counter.most_common()),
    }


def _improvement_backlog(results: list[dict[str, object]]) -> list[str]:
    backlog = [
        "Add explicit student_prompt and hint_ladder fields to TutorStep so Socratic behavior is first-class instead of implied by prose.",
        "Add reveal_policy per step; the current schema can show verified values, but it cannot encode when the UI should reveal them.",
        "Use OptCPV artifact bboxes to split overly broad focus regions before playback on dense circuits.",
        "Promote AnalysisView KCL terms into lesson steps for generic DC and bridge cases, so node equations can be rendered branch-by-branch.",
    ]
    if any("expected generic node-relationship explanation" in result["issues"] for result in results):
        backlog.append("Prevent unrelated motif matches from stealing a generic target; motif selection should require goal overlap.")
    if any(result["focus_failure_count"] for result in results):
        backlog.append("Close SVG metadata gaps for every generated focus ID before relying on zoom/highlight in the UI.")
    if any(result["early_answer_leaks"] for result in results):
        backlog.append("Gate requested values until after the target reference and sign convention have been discussed.")
    return backlog


def _markdown_report(results: list[dict[str, object]]) -> str:
    summary = _summary(results)
    weak = sorted(results, key=lambda result: (int(result["score"]), str(result["id"])))[:12]
    examples = [results[index] for index in [0, 20, 35, 55, 65, 80, 90] if index < len(results)]
    lines = [
        "# Tutor 100-Case QA",
        "",
        "Generated locally from supported `CircuitProblem` families. This exercises the lesson planner as if Gemini were producing step-by-step tutor moves, then scores the returned lesson for visual grounding, graph lens, reveal timing, and source-of-truth safety.",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Solved PASS: {summary['solved_pass']}",
        f"- Average tutor score: {summary['average_score']}/10",
        f"- Minimum tutor score: {summary['min_score']}/10",
        "",
        "## Family Scores",
        "",
    ]
    for family, score in summary["family_average_scores"].items():
        count = summary["family_counts"][family]
        lines.append(f"- {family}: {score}/10 across {count} cases")

    lines.extend(["", "## Gemini-Role Sample Decompositions", ""])
    for result in examples:
        lines.append(f"### {result['index']:03d}. {result['id']} ({result['family']})")
        lines.append("")
        lines.append(f"- Expected lens: {result['expected_lens']}")
        lines.append(f"- Score: {result['score']}/10")
        lines.append(f"- Steps: {', '.join(result['step_ids'])}")
        issues = result["issues"] or ["no blocking QA issues"]
        lines.append(f"- Self-eval: {'; '.join(issues)}")
        lines.append("")

    lines.extend(["## Weakest Cases", ""])
    for result in weak:
        lines.append(
            f"- {result['index']:03d} `{result['id']}` [{result['family']}], score {result['score']}: "
            f"{'; '.join(result['issues']) if result['issues'] else 'no issues'}"
        )

    lines.extend(["", "## Improvement Backlog", ""])
    for item in _improvement_backlog(results):
        lines.append(f"- {item}")

    lines.extend(["", "## Full Case Index", ""])
    for result in results:
        issue_text = "; ".join(result["issues"]) if result["issues"] else "ok"
        lines.append(
            f"- {result['index']:03d} `{result['id']}` [{result['family']}] "
            f"score={result['score']} steps={result['step_count']} lens={result['expected_lens']} issues={issue_text}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    parser.add_argument("--markdown", type=Path, help="Optional Markdown output path.")
    args = parser.parse_args()

    cases = build_cases()
    if len(cases) != TOTAL_CASES:
        raise RuntimeError(f"Expected {TOTAL_CASES} cases, got {len(cases)}")

    results = [evaluate_case(case, index) for index, case in enumerate(cases, start=1)]
    report = {"summary": _summary(results), "results": results}
    print(json.dumps(report["summary"], indent=2, sort_keys=True))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(_markdown_report(results), encoding="utf-8")

    hard_failures = [
        result
        for result in results
        if result["status"] != "solved" or result["badge"] != "PASS" or int(result["score"]) < 5
    ]
    return 1 if hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
