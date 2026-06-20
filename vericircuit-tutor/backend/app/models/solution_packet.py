from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import BMETemplateMetadata


ProblemStatus = Literal["solved", "invalid", "unsupported", "ambiguous"]
VerificationBadgeLabel = Literal["PASS", "FAIL", "AMBIGUOUS", "UNSUPPORTED"]


class QuantityValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    unit: str
    explanation_key: str | None = None
    reference: dict[str, str] | None = None


class SymbolicQuantityValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str
    unit: str
    explanation_key: str | None = None
    reference: dict[str, str] | None = None
    numeric_coefficient: float | None = None


class ComplexQuantityValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    real: float
    imag: float
    magnitude: float
    phase_deg: float
    unit: str
    explanation_key: str | None = None
    reference: dict[str, str] | None = None


class ComponentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voltage: QuantityValue
    current: QuantityValue
    power: QuantityValue
    sign_convention: str


class ACComponentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voltage: ComplexQuantityValue
    current: ComplexQuantityValue
    complex_power: ComplexQuantityValue | None = None
    power_note: str = (
        "Signed AC complex power uses V * conjugate(I). Negative real power "
        "means the component supplies net active power under the stated reference."
    )


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    message: str
    value: float | str | None = None


class VerificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool = False
    max_kcl_residual_a: float = 0.0
    power_balance_error_w: float = 0.0
    checks: list[CheckResult] = Field(default_factory=list)


class VerificationBadge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: VerificationBadgeLabel = "FAIL"
    message: str = "Solution has not passed verification."


class CalculationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parser_used: str | None = None
    llm_used_for_numerical_answer: bool = False
    solver_name: str = "internal_mna_v1"
    solver_method: str = "Modified Nodal Analysis"
    solver_backend: str = "numpy.linalg.solve"
    answer_source: str = "mna_solver"
    verification_source: str = "verifier.py"
    unknown_order: list[str] = Field(default_factory=list)
    mna_matrix: list[list[float]] = Field(default_factory=list)
    rhs_vector: list[float] = Field(default_factory=list)
    solution_vector: list[float] = Field(default_factory=list)


class ACFrequencyPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frequency_hz: float
    node_voltages: dict[str, ComplexQuantityValue] = Field(default_factory=dict)
    component_results: dict[str, ACComponentResult] = Field(default_factory=dict)
    requested_answers: dict[str, ComplexQuantityValue] = Field(default_factory=dict)
    verification: VerificationReport = Field(default_factory=VerificationReport)


class ACSweepPlotPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frequency_hz: float
    real: float
    imag: float
    magnitude: float
    magnitude_db: float
    phase_deg: float


class ACSweepPlotSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    source: Literal[
        "requested_answer",
        "node_voltage",
        "component_voltage",
        "component_current",
    ]
    unit: str
    points: list[ACSweepPlotPoint] = Field(default_factory=list)


class TransientPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_s: float
    voltage_v: float


class RCTransientResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capacitor_id: str
    positive_node: str
    negative_node: str
    initial_voltage_v: float
    final_voltage_v: float
    resistance_ohm: float
    capacitance_f: float
    time_constant_s: float
    formula: str
    sample_points: list[TransientPoint] = Field(default_factory=list)
    analysis_method: str = "first_order_rc_template"
    is_first_order: bool = True


class TeachingPlotPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    x_label: str | None = None
    y_label: str | None = None
    note: str | None = None


class TeachingPlotSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    unit: str | None = None
    points: list[TeachingPlotPoint] = Field(default_factory=list)


class TeachingPlotMarker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    axis: Literal["x", "y"]
    value: float
    label: str


class TeachingPlot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    subtitle: str | None = None
    plot_type: Literal["line", "bar"] = "line"
    source: Literal[
        "dc_operating_point",
        "ac_single_frequency",
        "ac_sweep",
        "rc_transient",
        "biomedical_context",
        "verification",
    ]
    x_label: str
    y_label: str
    x_scale: Literal["linear", "log"] = "linear"
    y_scale: Literal["linear", "log"] = "linear"
    series: list[TeachingPlotSeries] = Field(default_factory=list)
    markers: list[TeachingPlotMarker] = Field(default_factory=list)
    insight: str | None = None


class TutorObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    value: float | None = None
    unit: str | None = None
    note: str = ""


class TutorFocus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    components: list[str] = Field(default_factory=list)
    nodes: list[str] = Field(default_factory=list)
    current_paths: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


class TutorStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    body: str
    look_at: str | None = None
    why_it_matters: str | None = None
    common_mistake: str | None = None
    focus: TutorFocus = Field(default_factory=TutorFocus)
    verified_values: list[TutorObservation] = Field(default_factory=list)
    caution: str | None = None
    next_action: str | None = None


class LessonValueRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    formatted_value: str | None = None
    source: Literal[
        "solution_packet",
        "tutor_observation",
        "analysis_view",
        "deterministic_metadata",
    ] = "solution_packet"
    note: str | None = None


class LessonEquationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    equation: str
    explanation: str
    focus: TutorFocus = Field(default_factory=TutorFocus)
    value_refs: list[str] = Field(default_factory=list)


class LessonCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    passed: bool
    explanation: str
    value_ref: str | None = None


class SocraticModeProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal[
        "first_exposure",
        "worked_example",
        "end_of_chapter_practice",
        "review_debug",
    ]
    tutor_posture: str
    reveal_rule: str
    pace_notes: list[str] = Field(default_factory=list)


class SocraticLecturePrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    phase: Literal[
        "orient",
        "represent",
        "model",
        "predict",
        "commit",
        "compare",
        "check",
        "transfer",
    ]
    tutor_move: str
    student_task: str
    expected_student_evidence: str
    if_correct: str
    if_stuck: str
    reveal_policy: Literal[
        "no_numeric_reveal",
        "value_refs_only",
        "allow_verified_reveal",
    ] = "no_numeric_reveal"
    unlocks: list[str] = Field(default_factory=list)
    plot_ids: list[str] = Field(default_factory=list)
    value_refs: list[str] = Field(default_factory=list)
    focus: TutorFocus = Field(default_factory=TutorFocus)


class SocraticLectureStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    goal: str
    pace: Literal[
        "observe",
        "predict",
        "commit",
        "calculate",
        "interpret",
        "transfer",
    ]
    prompts: list[SocraticLecturePrompt] = Field(default_factory=list)
    advance_when: str
    common_failure: str | None = None
    instructor_note: str | None = None


class SocraticLecturePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal[
        "first_exposure",
        "worked_example",
        "end_of_chapter_practice",
        "review_debug",
    ] = "worked_example"
    source_pattern: str
    opening_contract: str
    textbook_pacing_summary: list[str] = Field(default_factory=list)
    mode_profiles: list[SocraticModeProfile] = Field(default_factory=list)
    stages: list[SocraticLectureStage] = Field(default_factory=list)
    gemini_prompt: str
    safety_notes: list[str] = Field(default_factory=list)


class LessonPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    learning_objectives: list[str] = Field(default_factory=list)
    conceptual_overview: list[str] = Field(default_factory=list)
    step_by_step_derivation: list[TutorStep] = Field(default_factory=list)
    equation_steps: list[LessonEquationStep] = Field(default_factory=list)
    visual_cues: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    checks: list[LessonCheck] = Field(default_factory=list)
    practice_prompts: list[str] = Field(default_factory=list)
    verified_value_refs: list[LessonValueRef] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SolutionPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_id: str
    status: ProblemStatus
    node_voltages: dict[str, float] = Field(default_factory=dict)
    component_results: dict[str, ComponentResult] = Field(default_factory=dict)
    requested_answers: dict[str, QuantityValue] = Field(default_factory=dict)
    symbolic_requested_answers: dict[str, SymbolicQuantityValue] = Field(default_factory=dict)
    ac_node_voltages: dict[str, ComplexQuantityValue] = Field(default_factory=dict)
    ac_component_results: dict[str, ACComponentResult] = Field(default_factory=dict)
    ac_requested_answers: dict[str, ComplexQuantityValue] = Field(default_factory=dict)
    frequency_hz: float | None = None
    ac_sweep: list[ACFrequencyPoint] = Field(default_factory=list)
    ac_sweep_plots: list[ACSweepPlotSeries] = Field(default_factory=list)
    transient_response: RCTransientResponse | None = None
    verification: VerificationReport = Field(default_factory=VerificationReport)
    verification_badge: VerificationBadge = Field(default_factory=VerificationBadge)
    calculation_trace: CalculationTrace = Field(default_factory=CalculationTrace)
    generated_netlist: str = ""
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)
    bme_metadata: BMETemplateMetadata | None = None
    tutor_observations: list[TutorObservation] = Field(default_factory=list)
    teaching_plots: list[TeachingPlot] = Field(default_factory=list)
    guided_steps: list[TutorStep] = Field(default_factory=list)
    lesson_packet: LessonPacket | None = None
    socratic_lecture: SocraticLecturePacket | None = None
