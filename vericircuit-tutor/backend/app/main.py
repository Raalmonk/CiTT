from __future__ import annotations

import base64
import binascii
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.models.coaching import (
    InstructorDashboardRequest,
    InstructorDashboardResponse,
    ReasoningCoachRequest,
    ReasoningCoachResponse,
)
from app.models.analysis_view import AnalysisView
from app.models.circuit_ir import CircuitProblem
from app.models.lab import LabSimulationRequest, LabSimulationResponse
from app.models.matlab_plugin import (
    FocusMapEntry,
    LabDeltaRequest,
    LabDeltaResponse,
    MatlabAdapterPlan,
    MatlabArtifactRequest,
    MatlabLabPlan,
    MatlabLabSummary,
    MatlabLabDeltaUploadRequest,
    MatlabLabDeltaUploadResponse,
    MatlabOfflineBundle,
    MatlabPluginArtifact,
    MatlabPluginManifest,
    ProbePlan,
)
from app.models.matlab_playground import (
    FocusMapEntry as PlaygroundFocusMapEntry,
    LabDeltaRequest as PlaygroundLabDeltaRequest,
    LabDeltaResponse as PlaygroundLabDeltaResponse,
    MatlabArtifact as PlaygroundMatlabArtifact,
    MatlabArtifactRequest as PlaygroundMatlabArtifactRequest,
    MatlabPlaygroundManifest,
    PlaygroundLab,
    ProbePlan as PlaygroundProbePlan,
)
from app.models.runtime_debug import RuntimeDebugTrace, add_debug_event
from app.models.scope_boundary import ScopeBoundary
from app.models.solution_packet import SolutionPacket
from app.models.visual_layout import VisualCircuit
from app.services.demo_parser import get_demo_examples
from app.services.analysis_view import build_analysis_view
from app.services.explainer import explain_solution
from app.services.gemini_client import gemini_is_configured, gemini_model, load_backend_dotenv
from app.services.incremental_solver import solve_resistor_update_incremental
from app.services.lab_simulator import simulate_lab
from app.services.matlab_plugin_generator import (
    available_labs,
    build_offline_bundle,
    build_matlab_plugin_manifest,
    compare_lab_delta,
    generate_artifacts,
    get_adapter_plan,
    get_focus_map,
    get_lab_plan,
    get_probe_plan,
    parse_lab_delta_upload,
)
from app.services.matlab_playground import (
    available_labs as playground_available_labs,
    build_playground_manifest,
    compare_lab_delta as playground_compare_lab_delta,
    generate_artifacts as playground_generate_artifacts,
    get_focus_map as playground_get_focus_map,
    get_lab as playground_get_lab,
    get_probe_plans as playground_get_probe_plans,
)
from app.services.parser_service import parse_image_problem, parse_problem
from app.services.pipeline import solve_circuit
from app.services.reasoning_coach import build_instructor_dashboard, coach_student_attempt
from app.services.scope_boundary import get_scope_boundary
from app.services.optcpv_bridge import (
    OptCPVUnavailable,
    SchematicRenderer,
    render_optcpv_schematic_svg,
)
from app.services.visual_layout import build_visual_circuit
from app.services.variant_generator import (
    generate_goal_variant,
    generate_value_variants,
    generate_variants,
)

logger = logging.getLogger(__name__)
load_backend_dotenv()


class ParseRequest(BaseModel):
    problem_text: str = Field(min_length=1)
    mode: Literal["gemini", "gemini_strict"] = "gemini"


class ParseImageRequest(BaseModel):
    image_base64: str = Field(min_length=1)
    mime_type: Literal["image/png", "image/jpeg", "image/webp"] = "image/png"
    problem_text: str = "Parse this schematic into Circuit IR."


class ParseResponse(BaseModel):
    circuit_ir: CircuitProblem
    parser_used: str
    warnings: list[str]
    debug_trace: RuntimeDebugTrace


class SolveRequest(BaseModel):
    circuit_ir: CircuitProblem
    parser_used: str | None = None


class SchematicRequest(SolveRequest):
    renderer: SchematicRenderer = "optcpv"


class ExplainRequest(BaseModel):
    solution_packet: SolutionPacket


class VariantRequest(BaseModel):
    circuit_ir: CircuitProblem
    kind: Literal["value", "goal", "both"] = "both"


class AnalysisViewRequest(BaseModel):
    circuit_ir: CircuitProblem
    solution_packet: SolutionPacket


class IncrementalResistorUpdateRequest(BaseModel):
    circuit_ir: CircuitProblem
    component_id: str = Field(min_length=1)
    new_value: float = Field(gt=0.0)


class IncrementalResistorUpdateResponse(BaseModel):
    incremental_used: bool
    message: str
    solution_packet: SolutionPacket | None = None


class FullPipelineRequest(BaseModel):
    problem_text: str = Field(min_length=1)
    mode: Literal["gemini", "gemini_strict"] = "gemini"


class FullPipelineResponse(BaseModel):
    circuit_ir: CircuitProblem
    solution_packet: SolutionPacket
    explanation: str
    variants: list[dict[str, object]]
    parser_used: str
    warnings: list[str]
    debug_trace: RuntimeDebugTrace


class ParserConfigResponse(BaseModel):
    gemini_configured: bool
    gemini_model: str


app = FastAPI(
    title="CiTT",
    description=(
        "Graphical tutor layer for BME circuits and signal-conditioning labs, "
        "with a MATLAB/Simscape playground direction and solver-grounded hand checks."
    ),
    version="1.0.0",
)

@app.middleware("http")
async def log_unhandled_citt_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled CiTT API error during %s %s",
            request.method,
            request.url.path,
        )
        raise


@app.get("/")
def index() -> dict[str, str]:
    return {
        "service": "vericircuit-tutor",
        "status": "ok",
        "frontend": "Use the React/Vite app in vericircuit-tutor/frontend.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vericircuit-tutor"}


@app.get("/scope", response_model=ScopeBoundary)
def scope() -> ScopeBoundary:
    return get_scope_boundary()


@app.get("/parser_config", response_model=ParserConfigResponse)
def parser_config() -> ParserConfigResponse:
    return ParserConfigResponse(
        gemini_configured=gemini_is_configured(),
        gemini_model=gemini_model(),
    )


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
        debug_trace=result.debug_trace,
    )


@app.post("/parse_image", response_model=ParseResponse)
def parse_image_endpoint(request: ParseImageRequest) -> ParseResponse:
    image_bytes = _decode_image_base64(request.image_base64)
    result = parse_image_problem(
        problem_text=request.problem_text,
        image_bytes=image_bytes,
        mime_type=request.mime_type,
    )
    return ParseResponse(
        circuit_ir=result.circuit,
        parser_used=result.parser_used,
        warnings=result.warnings,
        debug_trace=result.debug_trace,
    )


@app.post("/solve", response_model=SolutionPacket)
def solve_endpoint(request: SolveRequest) -> SolutionPacket:
    return solve_circuit(request.circuit_ir, parser_used=request.parser_used)


@app.post("/schematic", response_class=Response)
def schematic_endpoint(request: SchematicRequest) -> Response:
    try:
        svg = render_optcpv_schematic_svg(request.circuit_ir)
    except OptCPVUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("OptCPV schematic rendering failed.")
        raise HTTPException(
            status_code=502,
            detail=f"OptCPV schematic rendering failed: {type(exc).__name__}: {exc}",
        ) from exc
    return Response(content=svg, media_type="image/svg+xml")


@app.post("/visual_layout", response_model=VisualCircuit)
def visual_layout_endpoint(request: SolveRequest) -> VisualCircuit:
    return build_visual_circuit(request.circuit_ir)


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


@app.post("/incremental_resistor_update", response_model=IncrementalResistorUpdateResponse)
def incremental_resistor_update(
    request: IncrementalResistorUpdateRequest,
) -> IncrementalResistorUpdateResponse:
    result = solve_resistor_update_incremental(
        request.circuit_ir,
        component_id=request.component_id,
        new_value=request.new_value,
    )
    return IncrementalResistorUpdateResponse(
        incremental_used=result.incremental_used,
        message=result.message,
        solution_packet=result.packet,
    )


@app.post("/lab/simulate", response_model=LabSimulationResponse)
def lab_simulate_endpoint(request: LabSimulationRequest) -> LabSimulationResponse:
    try:
        return simulate_lab(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/matlab_playground/manifest", response_model=MatlabPlaygroundManifest)
def matlab_playground_manifest_endpoint() -> MatlabPlaygroundManifest:
    return build_playground_manifest()


@app.get("/matlab_playground/labs", response_model=list[PlaygroundLab])
def matlab_playground_labs_endpoint() -> list[PlaygroundLab]:
    return playground_available_labs()


@app.get("/matlab_playground/labs/{lab_id}", response_model=PlaygroundLab)
def matlab_playground_lab_endpoint(lab_id: str) -> PlaygroundLab:
    try:
        return playground_get_lab(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(
    "/matlab_playground/labs/{lab_id}/artifacts",
    response_model=list[PlaygroundMatlabArtifact],
)
def matlab_playground_artifacts_endpoint(
    lab_id: str,
    request: PlaygroundMatlabArtifactRequest | None = None,
) -> list[PlaygroundMatlabArtifact]:
    try:
        return playground_generate_artifacts(lab_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/matlab_playground/labs/{lab_id}/focus_map",
    response_model=list[PlaygroundFocusMapEntry],
)
def matlab_playground_focus_map_endpoint(lab_id: str) -> list[PlaygroundFocusMapEntry]:
    try:
        return playground_get_focus_map(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/matlab_playground/labs/{lab_id}/probe_plans",
    response_model=list[PlaygroundProbePlan],
)
def matlab_playground_probe_plans_endpoint(lab_id: str) -> list[PlaygroundProbePlan]:
    try:
        return playground_get_probe_plans(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(
    "/matlab_playground/labs/{lab_id}/lab_delta",
    response_model=PlaygroundLabDeltaResponse,
)
def matlab_playground_lab_delta_endpoint(
    lab_id: str,
    request: PlaygroundLabDeltaRequest,
) -> PlaygroundLabDeltaResponse:
    try:
        return playground_compare_lab_delta(lab_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/matlab_plugin/manifest", response_model=MatlabPluginManifest)
def matlab_plugin_manifest_endpoint() -> MatlabPluginManifest:
    return build_matlab_plugin_manifest()


@app.get("/matlab_plugin/labs", response_model=list[MatlabLabSummary])
def matlab_plugin_labs_endpoint() -> list[MatlabLabSummary]:
    return available_labs()


@app.post(
    "/matlab_plugin/labs/{lab_id}/artifact",
    response_model=list[MatlabPluginArtifact],
)
def matlab_plugin_artifact_endpoint(
    lab_id: str,
    request: MatlabArtifactRequest | None = None,
) -> list[MatlabPluginArtifact]:
    try:
        return generate_artifacts(lab_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/matlab_plugin/labs/{lab_id}/plan",
    response_model=MatlabLabPlan,
)
def matlab_plugin_lab_plan_endpoint(lab_id: str) -> MatlabLabPlan:
    try:
        return get_lab_plan(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/matlab_plugin/labs/{lab_id}/adapter_plan",
    response_model=MatlabAdapterPlan,
)
def matlab_plugin_adapter_plan_endpoint(lab_id: str) -> MatlabAdapterPlan:
    try:
        return get_adapter_plan(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(
    "/matlab_plugin/labs/{lab_id}/offline_bundle",
    response_model=MatlabOfflineBundle,
)
def matlab_plugin_offline_bundle_endpoint(
    lab_id: str,
    request: MatlabArtifactRequest | None = None,
) -> MatlabOfflineBundle:
    try:
        return build_offline_bundle(lab_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/matlab_plugin/labs/{lab_id}/focus_map",
    response_model=list[FocusMapEntry],
)
def matlab_plugin_focus_map_endpoint(lab_id: str) -> list[FocusMapEntry]:
    try:
        return get_focus_map(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/matlab_plugin/labs/{lab_id}/probe_plan",
    response_model=list[ProbePlan],
)
def matlab_plugin_probe_plan_endpoint(lab_id: str) -> list[ProbePlan]:
    try:
        return get_probe_plan(lab_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(
    "/matlab_plugin/labs/{lab_id}/lab_delta",
    response_model=LabDeltaResponse,
)
def matlab_plugin_lab_delta_endpoint(
    lab_id: str,
    request: LabDeltaRequest,
) -> LabDeltaResponse:
    try:
        return compare_lab_delta(lab_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(
    "/matlab_plugin/labs/{lab_id}/lab_delta/parse_upload",
    response_model=MatlabLabDeltaUploadResponse,
)
def matlab_plugin_lab_delta_upload_endpoint(
    lab_id: str,
    request: MatlabLabDeltaUploadRequest,
) -> MatlabLabDeltaUploadResponse:
    try:
        return parse_lab_delta_upload(lab_id, request)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail.startswith("Unknown MATLAB plugin lab") else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@app.post("/full_pipeline", response_model=FullPipelineResponse)
def full_pipeline(request: FullPipelineRequest) -> FullPipelineResponse:
    parsed = parse_problem(request.problem_text, request.mode)
    return _full_pipeline_response(parsed)


@app.post("/full_pipeline_image", response_model=FullPipelineResponse)
def full_pipeline_image(request: ParseImageRequest) -> FullPipelineResponse:
    image_bytes = _decode_image_base64(request.image_base64)
    parsed = parse_image_problem(
        problem_text=request.problem_text,
        image_bytes=image_bytes,
        mime_type=request.mime_type,
    )
    return _full_pipeline_response(parsed)


def _full_pipeline_response(parsed) -> FullPipelineResponse:
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)
    add_debug_event(
        parsed.debug_trace,
        stage="solver",
        label="solve_circuit_complete",
        message="Deterministic solve pipeline completed.",
        data={
            "circuit_id": parsed.circuit.id,
            "parser_used": parsed.parser_used,
            "status": packet.status,
            "verification_badge": packet.verification_badge.model_dump(),
            "solver_name": packet.calculation_trace.solver_name,
            "answer_source": packet.calculation_trace.answer_source,
            "requested_answer_count": len(packet.requested_answers),
            "symbolic_requested_answer_count": len(packet.symbolic_requested_answers),
            "ac_requested_answer_count": len(packet.ac_requested_answers),
            "warning_count": len(packet.warnings),
        },
    )
    warnings = [*parsed.warnings, *packet.warnings]
    variants = (
        generate_variants(parsed.circuit)
        if packet.verification_badge.label == "PASS"
        else []
    )
    explanation = explain_solution(packet)
    add_debug_event(
        parsed.debug_trace,
        stage="pipeline",
        label="full_pipeline_complete",
        message="Full parse/solve/explain/variant pipeline response assembled.",
        data={
            "warning_count": len(warnings),
            "variant_count": len(variants),
            "explanation_chars": len(explanation),
        },
    )
    return FullPipelineResponse(
        circuit_ir=parsed.circuit,
        solution_packet=packet,
        explanation=explanation,
        variants=variants,
        parser_used=parsed.parser_used,
        warnings=warnings,
        debug_trace=parsed.debug_trace,
    )


def _decode_image_base64(image_base64: str) -> bytes:
    try:
        return base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="image_base64 must be valid base64.") from exc


@app.post("/reasoning_coach", response_model=ReasoningCoachResponse)
def reasoning_coach(request: ReasoningCoachRequest) -> ReasoningCoachResponse:
    return coach_student_attempt(request)


@app.post("/instructor_dashboard", response_model=InstructorDashboardResponse)
def instructor_dashboard(
    request: InstructorDashboardRequest,
) -> InstructorDashboardResponse:
    return build_instructor_dashboard(request)
