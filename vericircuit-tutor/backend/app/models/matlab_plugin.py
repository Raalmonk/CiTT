from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MatlabPluginTab = Literal["overview", "teach", "probe", "lab_delta"]

MatlabArtifactKind = Literal[
    "matlab_script",
    "simulink_build_script",
    "live_script_plan",
    "app_designer_plan",
    "toolbox_manifest",
    "focus_map_json",
    "probe_plan_json",
]

HighlightTargetType = Literal[
    "block",
    "line",
    "port",
    "annotation",
    "svg_component",
    "svg_node",
    "conceptual_path",
]

HighlightSurface = Literal[
    "web_svg",
    "matlab_script",
    "simulink",
    "simscape",
    "conceptual",
]

LabDeltaValueSource = Literal["hand", "simulation", "measured"]
MatlabLabDeltaUploadFormat = Literal["auto", "csv", "tsv", "json"]
MatlabDeploymentMode = Literal["offline_toolbox", "optional_api", "web_preview"]
MatlabAgentActionKind = Literal[
    "fetch_manifest",
    "render_tab",
    "open_artifact",
    "highlight_target",
    "insert_probe",
    "run_simulation",
    "compare_lab_delta",
    "refuse_unsupported",
]


class HighlightTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    target_type: HighlightTargetType
    target_path: str | None = None
    simulink_path: str | None = None
    svg_id: str | None = None
    port: str | None = None
    description: str = ""


class FocusMapEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tab: MatlabPluginTab = "teach"
    title: str
    teaching_step_id: str | None = None
    target: HighlightTarget
    reason: str
    surfaces: list[HighlightSurface] = Field(default_factory=list)
    current_svg_components: list[str] = Field(default_factory=list)
    current_svg_nodes: list[str] = Field(default_factory=list)
    current_svg_goals: list[str] = Field(default_factory=list)
    future_simulink_actions: list[str] = Field(default_factory=list)
    student_prompt: str | None = None


class ProbePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    student_goal: str
    target: HighlightTarget
    quantity: str
    unit: str
    expected_behavior: str
    student_question: str
    measurement_explanation: str
    suggested_logging: list[str] = Field(default_factory=list)
    suggested_sensor_insertion: list[str] = Field(default_factory=list)
    future_matlab_steps: list[str] = Field(default_factory=list)
    matlab_comment_lines: list[str] = Field(default_factory=list)


class MatlabTeachStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    tab: MatlabPluginTab = "teach"
    prompt_before_reveal: str
    focus_entry_ids: list[str] = Field(default_factory=list)
    verified_value_refs: list[str] = Field(default_factory=list)
    explanation: str
    common_mistakes: list[str] = Field(default_factory=list)
    reveal_policy: Literal[
        "prompt_first",
        "show_hand_check",
        "show_simulation_evidence",
    ] = "prompt_first"


class LabDeltaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hand_values: dict[str, float] = Field(default_factory=dict)
    simulation_values: dict[str, float] = Field(default_factory=dict)
    measured_values: dict[str, float] = Field(default_factory=dict)
    value_units: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None


class LabDeltaComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    unit: str | None = None
    hand_value: float | None = None
    simulation_value: float | None = None
    measured_value: float | None = None
    reference_source: LabDeltaValueSource
    compared_source: LabDeltaValueSource
    absolute_difference: float
    percent_difference: float | None = None
    note: str = ""


class LabDeltaCause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    explanation: str
    confidence: Literal["low", "medium", "high"] = "medium"
    related_keys: list[str] = Field(default_factory=list)
    next_check: str


class LabDeltaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab_id: str
    comparison_rows: list[LabDeltaComparisonRow] = Field(default_factory=list)
    likely_causes: list[LabDeltaCause] = Field(default_factory=list)
    next_probe_suggestion: str
    next_check: str
    reflection_question: str
    notes: list[str] = Field(default_factory=list)


class MatlabLabDeltaUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    format: MatlabLabDeltaUploadFormat = "auto"
    notes: str | None = None


class MatlabLabDeltaUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab_id: str
    parsed_request: LabDeltaRequest
    lab_delta_response: LabDeltaResponse
    warnings: list[str] = Field(default_factory=list)


class MatlabAgentActionStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tab: MatlabPluginTab | None = None
    label: str
    action_kind: MatlabAgentActionKind
    inputs: list[str] = Field(default_factory=list)
    expected_output: str
    requires_matlab_runtime: bool = False
    dry_run_note: str


class MatlabAdapterPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab_id: str
    adapter_id: str = "matlab_app_designer_adapter_v1"
    launch_command: str = "citt"
    mode: Literal["dry_run_contract", "future_matlab_runtime"] = "dry_run_contract"
    required_matlab_products: list[str] = Field(default_factory=list)
    supported_now: list[str] = Field(default_factory=list)
    future_runtime_hooks: list[str] = Field(default_factory=list)
    agent_actions: list[MatlabAgentActionStep] = Field(default_factory=list)
    refusal_rules: list[str] = Field(default_factory=list)
    ci_validation: list[str] = Field(default_factory=list)


class MatlabPluginArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    lab_id: str
    kind: MatlabArtifactKind
    filename: str
    title: str
    description: str
    content: str
    mime_type: str = "text/plain"
    generated_by: str = "citt_matlab_plugin_generator_v1"
    requires_matlab_runtime: bool = False


class MatlabOfflineBundleFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    content: str
    mime_type: str = "text/plain"
    description: str


class MatlabLabSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    objective: str
    tabs: list[MatlabPluginTab] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    key_parameters: dict[str, str] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    idealizations: list[str] = Field(default_factory=list)
    bme_safety_boundary: str
    generated_artifact_kinds: list[MatlabArtifactKind] = Field(default_factory=list)
    evidence_to_collect: list[str] = Field(default_factory=list)
    status: Literal["implemented", "stub"] = "implemented"


class MatlabPluginManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plugin_id: str = "citt_matlab_popup_tutor"
    title: str = "CiTT MATLAB Popup Tutor"
    version: str = "0.1.0"
    description: str
    tabs: list[MatlabPluginTab]
    labs: list[MatlabLabSummary]
    api_prefix: str = "/matlab_plugin"
    matlab_entrypoint: str = "citt"
    default_deployment_mode: MatlabDeploymentMode = "offline_toolbox"
    deployment_modes: list[MatlabDeploymentMode] = Field(
        default_factory=lambda: ["offline_toolbox", "optional_api", "web_preview"]
    )
    local_server_required: bool = False
    ci_boundary: str = (
        "Generated artifacts, plans, and JSON manifests are testable without MATLAB installed."
    )
    source_of_truth_rule: str = (
        "LLM prose is not the numerical authority; tutoring is grounded in explicit "
        "models, hand checks, generated artifacts, simulation evidence, and student-visible reasoning steps."
    )


class MatlabLabPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab: MatlabLabSummary
    overview: dict[str, object] = Field(default_factory=dict)
    teach_steps: list[MatlabTeachStep] = Field(default_factory=list)
    focus_map: list[FocusMapEntry] = Field(default_factory=list)
    probe_plan: list[ProbePlan] = Field(default_factory=list)
    lab_delta_seed_request: LabDeltaRequest
    expected_artifact_kinds: list[MatlabArtifactKind] = Field(default_factory=list)
    adapter_plan: MatlabAdapterPlan


class MatlabOfflineBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    lab_id: str
    manifest: MatlabPluginManifest
    lab_plan: MatlabLabPlan
    artifacts: list[MatlabPluginArtifact] = Field(default_factory=list)
    files: list[MatlabOfflineBundleFile] = Field(default_factory=list)
    lab_delta_example: LabDeltaResponse
    file_tree: list[str] = Field(default_factory=list)
    integrity_checks: list[str] = Field(default_factory=list)
    requires_matlab_runtime: bool = False


class MatlabArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kinds: list[MatlabArtifactKind] | None = None
    include_focus_map: bool = True
    include_probe_plan: bool = True
    include_app_designer_plan: bool = True
