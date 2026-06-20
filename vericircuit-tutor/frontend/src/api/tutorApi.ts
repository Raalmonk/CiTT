import type {
  AnalysisView,
  CircuitProblem,
  InstructorDashboard,
  FocusMapEntry,
  LabDeltaRequest,
  LabDeltaResponse,
  LabScenario,
  LabSimulationResponse,
  MatlabAdapterPlan,
  MatlabArtifactRequest,
  MatlabLabDeltaUploadRequest,
  MatlabLabDeltaUploadResponse,
  MatlabLabPlan,
  MatlabLabSummary,
  MatlabOfflineBundle,
  MatlabPlaygroundArtifact,
  MatlabPlaygroundArtifactRequest,
  MatlabPlaygroundFocusMapEntry,
  MatlabPlaygroundLabDeltaRequest,
  MatlabPlaygroundLabDeltaResponse,
  MatlabPlaygroundManifest,
  MatlabPlaygroundProbePlan,
  MatlabPluginArtifact,
  MatlabPluginManifest,
  PracticeVariant,
  PlaygroundLab,
  ProbePlan,
  ScopeBoundary,
  SolutionPacket,
  StudentProfile,
  RuntimeDebugTrace,
  VisualCircuit
} from "@/types/api";

export type SchematicRenderer = "optcpv";
// Keep parser choice out of the product UI; strict mode is not a frontend option.
const PIPELINE_PARSER_MODE = "gemini" as const;

export type FullPipelineResponse = {
  circuit_ir: CircuitProblem;
  solution_packet: SolutionPacket;
  explanation: string;
  variants: PracticeVariant[];
  parser_used: string;
  warnings: string[];
  debug_trace: RuntimeDebugTrace;
};

export type ParserConfig = {
  gemini_configured: boolean;
  gemini_model: string;
};

export type RepresentationMode =
  | "diagram"
  | "kcl_equation"
  | "physical_intuition"
  | "units_magnitude"
  | "biomedical_context";

export type ReasoningCoachResponse = {
  circuit_id: string;
  parser_used: string;
  warnings: string[];
  verification_badge: SolutionPacket["verification_badge"];
  student_frame: {
    suspected_method?: string | null;
    confusion?: string | null;
    likely_misconceptions: string[];
    diagnostic_graph: Array<{
      id: string;
      label: string;
      kind: "observed_error" | "missing_concept" | "root_cause" | "next_step";
      evidence: string[];
      confidence: number;
      edges: Array<{
        target_id: string;
        relation: "causes" | "depends_on" | "evidence_for" | "next_check";
      }>;
    }>;
    confidence: "unknown" | "low" | "medium" | "high";
    evidence: string[];
    source: "heuristic" | "gemini" | "gemini_fallback";
  };
  local_check: {
    status: "needs_commit" | "productive" | "blocked" | "ready_for_next" | "ready_for_reveal";
    focus_issue: string;
    verified_context: string;
    blocks_next_step: boolean;
  };
  nudge: {
    hint_level: 0 | 1 | 2 | 3 | 4 | 5;
    representation_mode: RepresentationMode;
    message: string;
    question: string;
    representation_prompt: string;
    choices: string[];
    answer_revealed: boolean;
  };
  metrics: {
    hint_budget_used: number;
    independence_score: "high" | "medium" | "low";
    confidence_calibration?: string | null;
  };
  profile_update: StudentProfile;
  reflection: {
    summary: string;
    today_i_learned: string[];
    corrected_misconceptions: string[];
    next_practice_focus: string[];
  };
  adaptive_practice: Array<{
    id: string;
    target_misconception: string;
    prompt: string;
    goal: string;
    representation_mode: RepresentationMode;
    source: "deterministic_template";
  }>;
  guardrails: string[];
  solution_packet?: SolutionPacket | null;
  explanation?: string | null;
};

export async function fetchParserConfig(): Promise<ParserConfig> {
  const response = await fetch("/api/parser_config");

  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }

  return response.json() as Promise<ParserConfig>;
}

export async function fetchScopeBoundary(): Promise<ScopeBoundary> {
  const response = await fetch("/api/scope");

  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }

  return response.json() as Promise<ScopeBoundary>;
}

export async function runTextPipeline(problemText: string): Promise<FullPipelineResponse> {
  return postJson<FullPipelineResponse>("/api/full_pipeline", {
    problem_text: problemText,
    mode: PIPELINE_PARSER_MODE
  });
}

export async function runImagePipeline(params: {
  problemText: string;
  imageBase64: string;
  mimeType: string;
}): Promise<FullPipelineResponse> {
  return postJson<FullPipelineResponse>("/api/full_pipeline_image", {
    problem_text: params.problemText || "Parse this schematic into Circuit IR.",
    image_base64: params.imageBase64,
    mime_type: params.mimeType,
    mode: PIPELINE_PARSER_MODE
  });
}

export async function runReasoningCoach(params: {
  problemText: string;
  studentText: string;
  circuit?: CircuitProblem | null;
  solutionPacket?: SolutionPacket | null;
  parserUsed?: string;
  requestedHintLevel?: number;
  representationMode?: RepresentationMode;
  confidencePercent?: number | null;
  studentProfile?: StudentProfile | null;
  revealSolution?: boolean;
  studentFrameMode?: "heuristic" | "gemini";
}): Promise<ReasoningCoachResponse> {
  return postJson<ReasoningCoachResponse>("/api/reasoning_coach", {
    problem_text: params.problemText || params.circuit?.title || "Current circuit.",
    parser_used: params.parserUsed,
    circuit_ir: params.circuit ?? undefined,
    solution_packet: params.solutionPacket ?? undefined,
    student_frame_mode: params.studentFrameMode ?? "heuristic",
    requested_hint_level: params.requestedHintLevel ?? 1,
    representation_mode: params.representationMode ?? "physical_intuition",
    reveal_solution: params.revealSolution ?? false,
    student_profile: params.studentProfile ?? undefined,
    student_commitment: {
      attempt_text: params.studentText,
      confidence_percent: params.confidencePercent ?? undefined
    }
  });
}

export async function fetchVisualLayout(
  circuit: CircuitProblem,
  parserUsed?: string
): Promise<VisualCircuit> {
  return postJson<VisualCircuit>("/api/visual_layout", {
    circuit_ir: circuit,
    parser_used: parserUsed
  });
}

export async function fetchSchematicSvg(
  circuit: CircuitProblem,
  renderer: SchematicRenderer,
  parserUsed?: string
): Promise<string> {
  const response = await fetch("/api/schematic", {
    body: JSON.stringify({
      circuit_ir: circuit,
      parser_used: parserUsed,
      renderer
    }),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });

  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }

  return response.text();
}

export async function solveCircuit(
  circuit: CircuitProblem,
  parserUsed?: string
): Promise<SolutionPacket> {
  return postJson<SolutionPacket>("/api/solve", {
    circuit_ir: circuit,
    parser_used: parserUsed
  });
}

export async function fetchAnalysisView(
  circuit: CircuitProblem,
  solutionPacket: SolutionPacket
): Promise<AnalysisView> {
  return postJson<AnalysisView>("/api/analysis_view", {
    circuit_ir: circuit,
    solution_packet: solutionPacket
  });
}

export async function fetchVariants(
  circuit: CircuitProblem,
  kind: "value" | "goal" | "both" = "both"
): Promise<PracticeVariant[]> {
  const payload = await postJson<{ variants: PracticeVariant[] }>("/api/variant", {
    circuit_ir: circuit,
    kind
  });

  return payload.variants;
}

export async function explainSolution(solutionPacket: SolutionPacket): Promise<string> {
  const payload = await postJson<{ explanation: string }>("/api/explain", {
    solution_packet: solutionPacket
  });

  return payload.explanation;
}

export async function updateResistorIncremental(params: {
  circuit: CircuitProblem;
  componentId: string;
  newValue: number;
}): Promise<{
  incremental_used: boolean;
  message: string;
  solution_packet?: SolutionPacket | null;
}> {
  return postJson("/api/incremental_resistor_update", {
    circuit_ir: params.circuit,
    component_id: params.componentId,
    new_value: params.newValue
  });
}

export async function simulateLab(params: {
  circuit: CircuitProblem;
  baselinePacket?: SolutionPacket | null;
  scenario: LabScenario;
  parserUsed?: string | null;
}): Promise<LabSimulationResponse> {
  return postJson<LabSimulationResponse>("/api/lab/simulate", {
    circuit_ir: params.circuit,
    baseline_packet: params.baselinePacket ?? undefined,
    scenario: params.scenario,
    parser_used: params.parserUsed ?? undefined
  });
}

export async function fetchInstructorDashboard(
  profiles: StudentProfile[]
): Promise<InstructorDashboard> {
  return postJson<InstructorDashboard>("/api/instructor_dashboard", {
    student_profiles: profiles
  });
}

export async function fetchMatlabPluginManifest(): Promise<MatlabPluginManifest> {
  return getJson<MatlabPluginManifest>("/api/matlab_plugin/manifest");
}

export async function fetchMatlabPluginLabs(): Promise<MatlabLabSummary[]> {
  return getJson<MatlabLabSummary[]>("/api/matlab_plugin/labs");
}

export async function fetchMatlabPluginArtifacts(
  labId: string,
  request: MatlabArtifactRequest = {}
): Promise<MatlabPluginArtifact[]> {
  return postJson<MatlabPluginArtifact[]>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/artifact`, request);
}

export async function fetchMatlabPluginLabPlan(labId: string): Promise<MatlabLabPlan> {
  return getJson<MatlabLabPlan>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/plan`);
}

export async function fetchMatlabPluginAdapterPlan(labId: string): Promise<MatlabAdapterPlan> {
  return getJson<MatlabAdapterPlan>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/adapter_plan`);
}

export async function fetchMatlabPluginOfflineBundle(
  labId: string,
  request: MatlabArtifactRequest = {}
): Promise<MatlabOfflineBundle> {
  return postJson<MatlabOfflineBundle>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/offline_bundle`, request);
}

export async function fetchMatlabPluginFocusMap(labId: string): Promise<FocusMapEntry[]> {
  return getJson<FocusMapEntry[]>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/focus_map`);
}

export async function fetchMatlabPluginProbePlan(labId: string): Promise<ProbePlan[]> {
  return getJson<ProbePlan[]>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/probe_plan`);
}

export async function compareMatlabPluginLabDelta(
  labId: string,
  request: LabDeltaRequest
): Promise<LabDeltaResponse> {
  return postJson<LabDeltaResponse>(`/api/matlab_plugin/labs/${encodeURIComponent(labId)}/lab_delta`, request);
}

export async function parseMatlabPluginLabDeltaUpload(
  labId: string,
  request: MatlabLabDeltaUploadRequest
): Promise<MatlabLabDeltaUploadResponse> {
  return postJson<MatlabLabDeltaUploadResponse>(
    `/api/matlab_plugin/labs/${encodeURIComponent(labId)}/lab_delta/parse_upload`,
    request
  );
}

export async function fetchMatlabPlaygroundManifest(): Promise<MatlabPlaygroundManifest> {
  return getJson<MatlabPlaygroundManifest>("/api/matlab_playground/manifest");
}

export async function fetchMatlabPlaygroundLabs(): Promise<PlaygroundLab[]> {
  return getJson<PlaygroundLab[]>("/api/matlab_playground/labs");
}

export async function fetchMatlabPlaygroundArtifacts(
  labId: string,
  request: MatlabPlaygroundArtifactRequest = {}
): Promise<MatlabPlaygroundArtifact[]> {
  return postJson<MatlabPlaygroundArtifact[]>(
    `/api/matlab_playground/labs/${encodeURIComponent(labId)}/artifacts`,
    request
  );
}

export async function fetchMatlabPlaygroundFocusMap(labId: string): Promise<MatlabPlaygroundFocusMapEntry[]> {
  return getJson<MatlabPlaygroundFocusMapEntry[]>(
    `/api/matlab_playground/labs/${encodeURIComponent(labId)}/focus_map`
  );
}

export async function fetchMatlabPlaygroundProbePlans(labId: string): Promise<MatlabPlaygroundProbePlan[]> {
  return getJson<MatlabPlaygroundProbePlan[]>(
    `/api/matlab_playground/labs/${encodeURIComponent(labId)}/probe_plans`
  );
}

export async function compareMatlabPlaygroundLabDelta(
  labId: string,
  request: MatlabPlaygroundLabDeltaRequest
): Promise<MatlabPlaygroundLabDeltaResponse> {
  return postJson<MatlabPlaygroundLabDeltaResponse>(
    `/api/matlab_playground/labs/${encodeURIComponent(labId)}/lab_delta`,
    request
  );
}

export async function fileToBase64(file: File): Promise<string> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read the selected image."));
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.readAsDataURL(file);
  });

  return dataUrl.includes(",") ? dataUrl.split(",")[1] : dataUrl;
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }

  return response.json() as Promise<T>;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    body: JSON.stringify(body),
    headers: {
      "Content-Type": "application/json"
    },
    method: "POST"
  });

  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }

  return response.json() as Promise<T>;
}

async function responseErrorMessage(response: Response): Promise<string> {
  const fallback = `${response.status} ${response.statusText}`.trim();

  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // The schematic endpoint returns text on success; failed responses may be plain text too.
  }

  const text = await response.text().catch(() => "");
  return text || fallback || "Request failed.";
}
