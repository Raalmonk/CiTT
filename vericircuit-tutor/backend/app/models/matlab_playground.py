from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MatlabPlaygroundTab = Literal["overview", "teach", "probe", "lab_delta"]

MatlabArtifactKind = Literal[
    "matlab_script",
    "simulink_script",
    "simscape_script",
    "popup_app_script",
    "focus_map",
    "probe_plan",
    "lab_delta_report",
]

HighlightTargetType = Literal[
    "block",
    "line",
    "port",
    "annotation",
    "simscape_component",
    "simscape_connection",
    "svg_component",
    "svg_node",
    "conceptual_path",
]

LabDeltaSeverity = Literal["low", "medium", "high"]


class PlaygroundLab(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    summary: str
    bme_context: str
    required_products: list[str] = Field(default_factory=list)
    optional_products: list[str] = Field(default_factory=list)
    default_parameters: dict[str, float | str] = Field(default_factory=dict)
    learning_objectives: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class HighlightTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    target_type: HighlightTargetType
    component_id: str | None = None
    node_id: str | None = None
    model_path: str | None = None
    signal_name: str | None = None
    style: str = "default"
    reason: str


class FocusMapEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    mode: MatlabPlaygroundTab
    description: str
    targets: list[HighlightTarget] = Field(default_factory=list)
    teaching_step_id: str | None = None
    student_prompt: str | None = None


class ProbePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    target: HighlightTarget
    measurement_type: str
    expected_unit: str
    why_probe_here: str
    insertion_steps: list[str] = Field(default_factory=list)
    matlab_variable_name: str
    student_question: str


class LabDeltaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab_id: str | None = None
    hand_values: dict[str, float] = Field(default_factory=dict)
    simulation_values: dict[str, float] = Field(default_factory=dict)
    measured_values: dict[str, float] = Field(default_factory=dict)
    notes: str | None = None


class LabDeltaComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: str
    hand_value: float | None = None
    simulation_value: float | None = None
    measured_value: float | None = None
    unit: str | None = None
    absolute_error: float | None = None
    percent_error: float | None = None
    interpretation: str


class LabDeltaCause(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    explanation: str
    check_to_run: str
    severity: LabDeltaSeverity = "medium"


class LabDeltaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lab_id: str
    rows: list[LabDeltaComparisonRow] = Field(default_factory=list)
    likely_causes: list[LabDeltaCause] = Field(default_factory=list)
    recommended_probe: str
    reflection_question: str
    notes: list[str] = Field(default_factory=list)


class MatlabArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    lab_id: str
    title: str
    kind: MatlabArtifactKind
    filename: str
    content: str
    instructions: str


class MatlabArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kinds: list[MatlabArtifactKind] | None = None


class MatlabPlaygroundManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str
    version: str
    positioning: str
    tabs: list[MatlabPlaygroundTab]
    labs: list[PlaygroundLab]
    artifacts: list[MatlabArtifact]
    focus_map: list[FocusMapEntry]
    probe_plans: list[ProbePlan]
    lab_delta_causes: list[LabDeltaCause]
    notes: list[str] = Field(default_factory=list)
