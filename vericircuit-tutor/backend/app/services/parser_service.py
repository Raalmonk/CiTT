from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.models.runtime_debug import RuntimeDebugTrace, add_debug_event
from app.services.gemini_parser import (
    GeminiParserUnavailable,
    parse_image_with_gemini,
    parse_with_gemini,
)


NUMERIC_RE = r"([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)"
RESISTANCE_UNIT_RE = r"(k(?:ilo)?\s*(?:ohm|Ω)|m(?:ega)?\s*(?:ohm|Ω)|ohm|Ω)?"


@dataclass
class ParseResult:
    circuit: CircuitProblem
    parser_used: str
    warnings: list[str]
    debug_trace: RuntimeDebugTrace = field(default_factory=RuntimeDebugTrace)


def parse_problem(problem_text: str, mode: str = "gemini") -> ParseResult:
    debug_trace = RuntimeDebugTrace()
    add_debug_event(
        debug_trace,
        stage="parser",
        label="parse_problem_start",
        message="Text parse request received.",
        data={"mode": mode, "problem_text": problem_text, "problem_text_chars": len(problem_text)},
    )
    if mode not in {"gemini", "gemini_strict"}:
        return _ambiguous_parse_result(
            problem_text,
            parser_used="unsupported_parser_mode",
            message=f"Parser mode {mode!r} is no longer available. CiTT parser entrypoints now use Gemini only.",
            warnings=[f"Parser mode {mode!r} is disabled."],
            debug_trace=debug_trace,
        )

    deterministic = _voltage_clamp_fallback(problem_text, None, debug_trace=debug_trace)
    if deterministic:
        return deterministic

    try:
        circuit = parse_with_gemini(problem_text, debug_trace=debug_trace)
        fallback = _voltage_clamp_fallback(problem_text, circuit, debug_trace=debug_trace)
        if fallback:
            return fallback
        add_debug_event(
            debug_trace,
            stage="parser",
            label="parse_problem_complete",
            message="Gemini parse completed without deterministic replacement.",
            data={
                "parser_used": "gemini",
                "circuit_id": circuit.id,
                "component_count": len(circuit.components),
                "goal_count": len(circuit.goals),
                "ambiguity_count": len(circuit.ambiguities),
            },
        )
        return ParseResult(
            circuit=circuit,
            parser_used="gemini",
            warnings=[],
            debug_trace=debug_trace,
        )
    except GeminiParserUnavailable as exc:
        add_debug_event(
            debug_trace,
            stage="parser",
            label="gemini_parse_unavailable",
            message="Gemini parse did not produce a usable CircuitProblem.",
            data={"error": str(exc), "error_type": type(exc).__name__},
        )
        fallback = _voltage_clamp_fallback(problem_text, None, debug_trace=debug_trace)
        if fallback:
            return fallback
        return _ambiguous_parse_result(
            problem_text,
            parser_used="gemini",
            message="Gemini could not produce validated CircuitProblem JSON.",
            warnings=[str(exc), "No built-in parser fallback is available."],
            cause=str(exc),
            debug_trace=debug_trace,
        )


def parse_image_problem(
    *,
    problem_text: str,
    image_bytes: bytes,
    mime_type: str,
) -> ParseResult:
    debug_trace = RuntimeDebugTrace()
    add_debug_event(
        debug_trace,
        stage="parser",
        label="parse_image_problem_start",
        message="Image parse request received.",
        data={
            "problem_text": problem_text,
            "problem_text_chars": len(problem_text),
            "image": {"mime_type": mime_type, "byte_count": len(image_bytes)},
        },
    )
    deterministic = _voltage_clamp_fallback(
        problem_text,
        None,
        parser_used="gemini_image",
        debug_trace=debug_trace,
    )
    if deterministic:
        return deterministic

    try:
        circuit = parse_image_with_gemini(
            problem_text=problem_text,
            image_bytes=image_bytes,
            mime_type=mime_type,
            debug_trace=debug_trace,
        )
        fallback = _voltage_clamp_fallback(
            problem_text,
            circuit,
            parser_used="gemini_image",
            debug_trace=debug_trace,
        )
        if fallback:
            return fallback
        add_debug_event(
            debug_trace,
            stage="parser",
            label="parse_image_problem_complete",
            message="Gemini image parse completed without deterministic replacement.",
            data={
                "parser_used": "gemini_image",
                "circuit_id": circuit.id,
                "component_count": len(circuit.components),
                "goal_count": len(circuit.goals),
                "ambiguity_count": len(circuit.ambiguities),
            },
        )
        return ParseResult(
            circuit=circuit,
            parser_used="gemini_image",
            warnings=[],
            debug_trace=debug_trace,
        )
    except GeminiParserUnavailable as exc:
        add_debug_event(
            debug_trace,
            stage="parser",
            label="gemini_image_parse_unavailable",
            message="Gemini image parse did not produce a usable CircuitProblem.",
            data={"error": str(exc), "error_type": type(exc).__name__},
        )
        fallback = _voltage_clamp_fallback(
            problem_text,
            None,
            parser_used="gemini_image",
            debug_trace=debug_trace,
        )
        if fallback:
            return fallback
        result = _ambiguous_parse_result(
            problem_text or "Parse schematic image.",
            parser_used="gemini_image",
            message="Gemini image mode could not produce validated CircuitProblem JSON.",
            warnings=[str(exc)],
            cause=str(exc),
            debug_trace=debug_trace,
        )
        result.circuit.id = "gemini_image_parse_failed"
        result.circuit.title = "Gemini Image Parse Failed"
        return result


def _ambiguous_parse_result(
    problem_text: str,
    *,
    parser_used: str,
    message: str,
    warnings: list[str],
    cause: str | None = None,
    debug_trace: RuntimeDebugTrace | None = None,
) -> ParseResult:
    debug_trace = debug_trace or RuntimeDebugTrace()
    ambiguities = [message]
    if cause:
        ambiguities.append(cause)
    add_debug_event(
        debug_trace,
        stage="parser",
        label="ambiguous_parse_result",
        message=message,
        data={
            "parser_used": parser_used,
            "warning_count": len(warnings),
            "cause": cause,
        },
    )
    return ParseResult(
        circuit=CircuitProblem(
            id="gemini_parse_failed",
            title="Gemini Parse Failed",
            topology_id=None,
            ground_node="0",
            nodes=["0"],
            components=[],
            goals=[],
            assumptions=[],
            ambiguities=ambiguities,
            unsupported_features=[],
        ),
        parser_used=parser_used,
        warnings=warnings,
        debug_trace=debug_trace,
    )


def _voltage_clamp_fallback(
    problem_text: str,
    circuit: CircuitProblem | None,
    *,
    parser_used: str = "gemini",
    debug_trace: RuntimeDebugTrace | None = None,
) -> ParseResult | None:
    if not _looks_like_two_electrode_voltage_clamp(problem_text, circuit):
        return None
    if _has_numeric_command_voltage(problem_text, circuit):
        return None

    should_replace = circuit is None or not circuit.components or bool(circuit.ambiguities)
    if not should_replace:
        return None

    gain_a = _extract_gain(problem_text, circuit)
    shared_resistance = _extract_shared_rm_ro(problem_text, circuit)
    rm = shared_resistance or _extract_resistance(problem_text, circuit, "m")
    ro = shared_resistance or _extract_resistance(problem_text, circuit, "o")
    if gain_a is None or rm is None or ro is None:
        return None

    add_debug_event(
        debug_trace,
        stage="parser",
        label="voltage_clamp_fallback_used",
        message="Deterministic two-electrode voltage-clamp parser fallback replaced the Gemini parse.",
        data={
            "parser_used": f"{parser_used}_voltage_clamp_fallback",
            "gain_a": gain_a,
            "rm_ohm": rm,
            "ro_ohm": ro,
            "had_gemini_circuit": circuit is not None,
        },
    )
    return ParseResult(
        circuit=CircuitProblem(
            id="two_electrode_voltage_clamp",
            title="2-Electrode Voltage Clamp Equilibrium",
            topology_id="two_electrode_voltage_clamp",
            ground_node="0",
            nodes=["0", "Vc", "Vm", "Vo"],
            components=[
                Component(
                    id="DiffAmp",
                    type="op_amp_nonideal",
                    nodes=["Vc", "Vm", "Vo", "0"],
                    value=gain_a,
                    unit="gain",
                    label=f"Differential amplifier, A = {gain_a:g}",
                    open_loop_gain=gain_a,
                ),
                Component(
                    id="R_m",
                    type="resistor",
                    nodes=["Vm", "0"],
                    value=rm,
                    unit="ohm",
                    label=f"R_m = {rm:g} ohm",
                ),
                Component(
                    id="R_o",
                    type="resistor",
                    nodes=["Vo", "Vm"],
                    value=ro,
                    unit="ohm",
                    label=f"R_o = {ro:g} ohm",
                ),
            ],
            goals=[
                Goal(
                    id="vm_equilibrium",
                    quantity="node_voltage",
                    target="Vm",
                    reference={"positive_node": "Vm", "negative_node": "0"},
                )
            ],
            assumptions=[
                f"A = {gain_a:g}",
                f"R_m = {rm:g} ohm",
                f"R_o = {ro:g} ohm",
                "V_c is a symbolic command-voltage input because no numeric command value is provided.",
            ],
            ambiguities=[],
            unsupported_features=[],
        ),
        parser_used=f"{parser_used}_voltage_clamp_fallback",
        warnings=["Used deterministic 2-electrode voltage-clamp parser fallback."],
        debug_trace=debug_trace or RuntimeDebugTrace(),
    )


def _looks_like_two_electrode_voltage_clamp(problem_text: str, circuit: CircuitProblem | None) -> bool:
    text = _voltage_clamp_search_text(problem_text, circuit).lower()
    compact = _compact(text)
    if ("voltage clamp" in text or "voltageclamp" in compact) and (
        "2electrode" in compact or "twoelectrode" in compact
    ):
        return True
    if not circuit:
        return False
    if _compact(circuit.topology_id) in {"voltageclamp", "twoelectrodevoltageclamp", "tevc"}:
        return True

    has_clamp_language = (
        "voltage clamp" in text
        or "voltageclamp" in compact
        or "commandvoltage" in compact
        or re.search(r"\bv\s*[_\s-]?c\b", text, flags=re.IGNORECASE) is not None
    )
    has_cell_language = (
        "membrane" in compact
        or "electrode" in compact
        or re.search(r"\bv\s*[_\s-]?m\b", text, flags=re.IGNORECASE) is not None
    )
    return has_clamp_language and has_cell_language and _has_voltage_clamp_component_shape(circuit)


def _extract_gain(problem_text: str, circuit: CircuitProblem | None) -> float | None:
    for component in circuit.components if circuit else []:
        if component.open_loop_gain and component.open_loop_gain > 0:
            return float(component.open_loop_gain)
        compact = _compact(" ".join([component.id, component.label or "", component.type]))
        if compact in {"a", "gaina", "diffamp", "differentialamplifier"} and component.value > 0:
            return float(component.value)

    return _first_number(
        problem_text,
        [
            rf"(?<![A-Za-z0-9_])A(?![A-Za-z0-9_])\s*(?:=|is|to\s+be|be)\s*{NUMERIC_RE}",
            rf"gain\s*(?:A\s*)?(?:=|is|of|to\s+be|be)\s*{NUMERIC_RE}",
        ],
    )


def _has_numeric_command_voltage(problem_text: str, circuit: CircuitProblem | None) -> bool:
    for text in _candidate_texts(problem_text, circuit):
        if re.search(rf"V\s*[_\s-]?c\s*(?:=|is|to\s+be|be)\s*{NUMERIC_RE}", text, flags=re.IGNORECASE):
            return True
    return False


def _extract_shared_rm_ro(problem_text: str, circuit: CircuitProblem | None) -> float | None:
    for text in _candidate_texts(problem_text, circuit):
        value = _first_resistance(
            text,
            [
                rf"R\s*[_\s-]?m\s*=\s*R\s*[_\s-]?o\s*=\s*{NUMERIC_RE}\s*{RESISTANCE_UNIT_RE}",
                rf"R\s*[_\s-]?o\s*=\s*R\s*[_\s-]?m\s*=\s*{NUMERIC_RE}\s*{RESISTANCE_UNIT_RE}",
            ],
        )
        if value is not None:
            return value
    if circuit and _looks_like_two_electrode_voltage_clamp(problem_text, circuit):
        return _shared_voltage_clamp_resistor_value(circuit)
    return None


def _extract_resistance(problem_text: str, circuit: CircuitProblem | None, name: str) -> float | None:
    tokens = {
        "m": {"rm", "rmembrane", "membraneresistance"},
        "o": {"ro", "rout", "outputresistance", "currentelectroderesistance"},
    }[name]

    for component in circuit.components if circuit else []:
        if component.type != "resistor" or component.value <= 0:
            continue
        compact = _compact(" ".join([component.id, component.label or ""]))
        if compact in tokens or any(token in compact for token in tokens):
            return float(component.value)

    if circuit and _looks_like_two_electrode_voltage_clamp(problem_text, circuit):
        role_value = _voltage_clamp_resistance_by_role(circuit, name)
        if role_value is not None:
            return role_value

    for text in _candidate_texts(problem_text, circuit):
        value = _first_resistance(
            text,
            [
                rf"R\s*[_\s-]?{name}\s*(?:=|is|to\s+be|be)\s*{NUMERIC_RE}\s*{RESISTANCE_UNIT_RE}",
                rf"R{name}\s*(?:=|is|to\s+be|be)\s*{NUMERIC_RE}\s*{RESISTANCE_UNIT_RE}",
            ],
        )
        if value is not None:
            return value
    return None


def _candidate_texts(problem_text: str, circuit: CircuitProblem | None) -> list[str]:
    texts = [problem_text]
    if circuit:
        texts.extend(
            [
                circuit.id,
                circuit.title,
                circuit.topology_id or "",
                *(circuit.assumptions or []),
                *(circuit.nonblocking_ambiguities or []),
                *(circuit.ambiguities or []),
            ]
        )
        for component in circuit.components:
            texts.append(
                " ".join(
                    [
                        component.id,
                        component.type,
                        component.label or "",
                        " ".join(component.nodes),
                        f"{component.value:g}",
                        component.unit,
                        "" if component.open_loop_gain is None else f"A = {component.open_loop_gain:g}",
                    ]
                )
            )
    return texts


def _voltage_clamp_search_text(problem_text: str, circuit: CircuitProblem | None) -> str:
    return " ".join(text for text in _candidate_texts(problem_text, circuit) if text)


def _has_voltage_clamp_component_shape(circuit: CircuitProblem) -> bool:
    return _voltage_clamp_core_nets(circuit) is not None and len(_positive_resistors(circuit)) >= 2


def _voltage_clamp_core_nets(circuit: CircuitProblem) -> tuple[str, str, str] | None:
    for component in circuit.components:
        if "op_amp" not in component.type and "opamp" not in component.type:
            continue
        if len(component.nodes) >= 3:
            return component.nodes[0], component.nodes[1], component.nodes[2]
    return None


def _positive_resistors(circuit: CircuitProblem) -> list[Component]:
    return [
        component
        for component in circuit.components
        if component.type == "resistor" and component.value > 0
    ]


def _shared_voltage_clamp_resistor_value(circuit: CircuitProblem) -> float | None:
    resistors = _positive_resistors(circuit)
    if len(resistors) < 2:
        return None
    first = float(resistors[0].value)
    if all(abs(float(resistor.value) - first) <= max(1e-9, abs(first) * 1e-9) for resistor in resistors[:2]):
        return first
    return None


def _voltage_clamp_resistance_by_role(circuit: CircuitProblem, name: str) -> float | None:
    core_nets = _voltage_clamp_core_nets(circuit)
    if core_nets is None:
        return None
    _, membrane_node, amplifier_output_node = core_nets
    ground_node = circuit.ground_node

    for resistor in _positive_resistors(circuit):
        nodes = set(resistor.nodes)
        if name == "m" and membrane_node in nodes and ground_node in nodes:
            return float(resistor.value)
        if name == "o" and membrane_node in nodes and amplifier_output_node in nodes:
            return float(resistor.value)

    shared = _shared_voltage_clamp_resistor_value(circuit)
    if shared is not None:
        return shared
    return None


def _first_number(text: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _first_resistance(text: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _scale_resistance(float(match.group(1)), match.group(2) or "ohm")
    return None


def _scale_resistance(value: float, unit: str) -> float:
    stripped = unit.strip()
    compact = _compact(stripped)
    if compact.startswith("k"):
        return value * 1_000.0
    if stripped.startswith("M") or compact.startswith("mega"):
        return value * 1_000_000.0
    return value


def _compact(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())
