from __future__ import annotations

from dataclasses import dataclass

from app.models.circuit_ir import CircuitProblem
from app.services.demo_parser import ambiguous_problem, parse_demo_problem
from app.services.gemini_parser import GeminiParserUnavailable, parse_with_gemini


@dataclass
class ParseResult:
    circuit: CircuitProblem
    parser_used: str
    warnings: list[str]


def parse_problem(problem_text: str, mode: str = "demo") -> ParseResult:
    if mode in {"gemini", "gemini_strict"}:
        try:
            return ParseResult(
                circuit=parse_with_gemini(problem_text),
                parser_used="gemini",
                warnings=[],
            )
        except GeminiParserUnavailable as exc:
            if mode == "gemini_strict":
                circuit = ambiguous_problem(problem_text)
                circuit.id = "gemini_strict_parse_failed"
                circuit.title = "Gemini Strict Parse Failed"
                circuit.ambiguities = [
                    "Gemini strict mode could not produce validated CircuitProblem JSON.",
                    str(exc),
                ]
                return ParseResult(
                    circuit=circuit,
                    parser_used="gemini_strict",
                    warnings=[str(exc), "Gemini strict mode did not use demo fallback."],
                )

            fallback = parse_demo_problem(problem_text)
            return ParseResult(
                circuit=fallback,
                parser_used="demo",
                warnings=[str(exc), "Fell back to deterministic demo parser."],
            )

    return ParseResult(
        circuit=parse_demo_problem(problem_text),
        parser_used="demo",
        warnings=[],
    )
