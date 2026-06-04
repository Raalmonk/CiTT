from __future__ import annotations

from dataclasses import dataclass

from app.models.circuit_ir import CircuitProblem
from app.services.demo_parser import parse_demo_problem
from app.services.gemini_parser import GeminiParserUnavailable, parse_with_gemini


@dataclass
class ParseResult:
    circuit: CircuitProblem
    parser_used: str
    warnings: list[str]


def parse_problem(problem_text: str, mode: str = "demo") -> ParseResult:
    if mode == "gemini":
        try:
            return ParseResult(
                circuit=parse_with_gemini(problem_text),
                parser_used="gemini",
                warnings=[],
            )
        except GeminiParserUnavailable as exc:
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

