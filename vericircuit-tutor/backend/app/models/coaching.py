from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, VerificationBadge


HintLevel = Literal[0, 1, 2, 3, 4, 5]
IndependenceScore = Literal["high", "medium", "low"]
RepresentationMode = Literal[
    "diagram",
    "kcl_equation",
    "physical_intuition",
    "units_magnitude",
    "biomedical_context",
]
CoachCheckStatus = Literal[
    "needs_commit",
    "productive",
    "blocked",
    "ready_for_next",
    "ready_for_reveal",
]


class StudentCommitment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_text: str = ""
    plan: str | None = None
    knowns: list[str] = Field(default_factory=list)
    unknown: str | None = None
    first_equation: str | None = None
    expected_answer: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    confidence_percent: float | None = Field(default=None, ge=0.0, le=100.0)


class StudentFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suspected_method: str | None = None
    confusion: str | None = None
    likely_misconceptions: list[str] = Field(default_factory=list)
    diagnostic_graph: list["DiagnosticNode"] = Field(default_factory=list)
    confidence: Literal["unknown", "low", "medium", "high"] = "unknown"
    evidence: list[str] = Field(default_factory=list)
    source: Literal["heuristic", "gemini", "gemini_fallback"] = "heuristic"


class DiagnosticEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(min_length=1)
    relation: Literal["causes", "depends_on", "evidence_for", "next_check"] = "causes"


class DiagnosticNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    kind: Literal["observed_error", "missing_concept", "root_cause", "next_step"] = "observed_error"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    edges: list[DiagnosticEdge] = Field(default_factory=list)


class KnowledgeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mastery: float = Field(default=0.5, ge=0.0, le=1.0)
    opportunities: int = Field(default=0, ge=0)
    last_evidence: str | None = None


class StudentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strengths: list[str] = Field(default_factory=list)
    recurring_misconceptions: dict[str, int] = Field(default_factory=dict)
    knowledge_state: dict[str, KnowledgeState] = Field(default_factory=dict)
    hint_preference: str = "conceptual_nudges"
    independence_level: IndependenceScore = "medium"
    hint_budget_used: int = Field(default=0, ge=0)
    completed_attempts: int = Field(default=0, ge=0)


class CoachLocalCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CoachCheckStatus
    focus_issue: str
    verified_context: str
    blocks_next_step: bool = False


class CoachNudge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hint_level: HintLevel
    representation_mode: RepresentationMode = "physical_intuition"
    message: str
    question: str
    representation_prompt: str
    choices: list[str] = Field(default_factory=list)
    answer_revealed: bool = False


class CoachMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hint_budget_used: int = Field(ge=0)
    independence_score: IndependenceScore
    confidence_calibration: str | None = None


class ReflectionJournalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    today_i_learned: list[str] = Field(default_factory=list)
    corrected_misconceptions: list[str] = Field(default_factory=list)
    next_practice_focus: list[str] = Field(default_factory=list)


class AdaptivePracticePrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    target_misconception: str
    prompt: str
    goal: str
    representation_mode: RepresentationMode = "physical_intuition"
    source: Literal["deterministic_template"] = "deterministic_template"


class ReasoningCoachRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_text: str = Field(min_length=1)
    mode: Literal["gemini", "gemini_strict"] = "gemini"
    circuit_ir: CircuitProblem | None = None
    solution_packet: SolutionPacket | None = None
    parser_used: str | None = None
    student_frame_mode: Literal["heuristic", "gemini"] = "gemini"
    student_commitment: StudentCommitment = Field(default_factory=StudentCommitment)
    student_profile: StudentProfile | None = None
    requested_hint_level: int = Field(default=1, ge=0, le=5)
    representation_mode: RepresentationMode = "physical_intuition"
    reveal_solution: bool = False


class ReasoningCoachResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_id: str
    parser_used: str
    warnings: list[str] = Field(default_factory=list)
    verification_badge: VerificationBadge
    student_frame: StudentFrame
    local_check: CoachLocalCheck
    nudge: CoachNudge
    profile_update: StudentProfile
    metrics: CoachMetrics
    reflection: ReflectionJournalEntry
    adaptive_practice: list[AdaptivePracticePrompt] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    solution_packet: SolutionPacket | None = None
    explanation: str | None = None


class InstructorDashboardRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_profiles: list[StudentProfile] = Field(default_factory=list)


class MisconceptionCohortSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    misconception: str
    label: str
    affected_students: int = Field(ge=0)
    total_occurrences: int = Field(ge=0)
    affected_percent: float = Field(ge=0.0, le=100.0)
    suggested_intervention: str


class InstructorDashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_count: int = Field(ge=0)
    cohort_independence: dict[IndependenceScore, int] = Field(default_factory=dict)
    misconception_summary: list[MisconceptionCohortSummary] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
