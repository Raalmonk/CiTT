from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.models.analysis_view import AnalysisView
from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket
from app.services.demo_parser import get_demo_examples
from app.services.analysis_view import build_analysis_view
from app.services.explainer import explain_solution
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit
from app.services.schematic_generator import render_schematic_svg
from app.services.variant_generator import (
    generate_goal_variant,
    generate_value_variants,
    generate_variants,
)


class ParseRequest(BaseModel):
    problem_text: str = Field(min_length=1)
    mode: Literal["demo", "gemini", "gemini_strict"] = "demo"


class ParseResponse(BaseModel):
    circuit_ir: CircuitProblem
    parser_used: str
    warnings: list[str]


class SolveRequest(BaseModel):
    circuit_ir: CircuitProblem
    parser_used: str | None = None


class ExplainRequest(BaseModel):
    solution_packet: SolutionPacket


class VariantRequest(BaseModel):
    circuit_ir: CircuitProblem
    kind: Literal["value", "goal", "both"] = "both"


class AnalysisViewRequest(BaseModel):
    circuit_ir: CircuitProblem
    solution_packet: SolutionPacket


class FullPipelineRequest(BaseModel):
    problem_text: str = Field(min_length=1)
    mode: Literal["demo", "gemini", "gemini_strict"] = "demo"


class FullPipelineResponse(BaseModel):
    circuit_ir: CircuitProblem
    solution_packet: SolutionPacket
    explanation: str
    variants: list[dict[str, object]]
    parser_used: str
    warnings: list[str]


app = FastAPI(
    title="VeriCircuit Tutor",
    description="Simulation-grounded AI tutor MVP for controlled linear circuit analysis.",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vericircuit-tutor"}


@app.get("/examples")
def examples() -> list[dict[str, object]]:
    return get_demo_examples()


@app.post("/parse", response_model=ParseResponse)
def parse_endpoint(request: ParseRequest) -> ParseResponse:
    result = parse_problem(request.problem_text, request.mode)
    return ParseResponse(
        circuit_ir=result.circuit,
        parser_used=result.parser_used,
        warnings=result.warnings,
    )


@app.post("/solve", response_model=SolutionPacket)
def solve_endpoint(request: SolveRequest) -> SolutionPacket:
    return solve_circuit(request.circuit_ir, parser_used=request.parser_used)


@app.post("/schematic", response_class=Response)
def schematic_endpoint(request: SolveRequest) -> Response:
    return Response(
        content=render_schematic_svg(request.circuit_ir),
        media_type="image/svg+xml",
    )


@app.post("/explain")
def explain_endpoint(request: ExplainRequest) -> dict[str, str]:
    return {"explanation": explain_solution(request.solution_packet)}


@app.post("/variant")
def variant_endpoint(request: VariantRequest) -> dict[str, object]:
    if request.kind == "value":
        variants = generate_value_variants(request.circuit_ir)
    elif request.kind == "goal":
        variants = [
            {
                "kind": "same_circuit_different_goal",
                "prompt": "What if the requested target changes?",
                "description": "Same circuit with a different requested target quantity.",
                "circuit_ir": generate_goal_variant(request.circuit_ir).model_dump(),
            }
        ]
    else:
        variants = generate_variants(request.circuit_ir)
    return {"variants": variants}


@app.post("/analysis_view", response_model=AnalysisView)
def analysis_view_endpoint(request: AnalysisViewRequest) -> AnalysisView:
    return build_analysis_view(request.circuit_ir, request.solution_packet)


@app.post("/full_pipeline", response_model=FullPipelineResponse)
def full_pipeline(request: FullPipelineRequest) -> FullPipelineResponse:
    parsed = parse_problem(request.problem_text, request.mode)
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)
    warnings = [*parsed.warnings, *packet.warnings]
    variants = (
        generate_variants(parsed.circuit)
        if packet.verification_badge.label == "PASS"
        else []
    )
    return FullPipelineResponse(
        circuit_ir=parsed.circuit,
        solution_packet=packet,
        explanation=explain_solution(packet),
        variants=variants,
        parser_used=parsed.parser_used,
        warnings=warnings,
    )
