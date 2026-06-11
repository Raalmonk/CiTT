from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProblemStatus = Literal["solved", "invalid", "unsupported", "ambiguous"]
VerificationBadgeLabel = Literal["PASS", "FAIL", "AMBIGUOUS", "UNSUPPORTED"]


class QuantityValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    unit: str
    explanation_key: str | None = None
    reference: dict[str, str] | None = None


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
    power_note: str = "AC complex power is not verified in this MVP."


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


class SolutionPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_id: str
    status: ProblemStatus
    node_voltages: dict[str, float] = Field(default_factory=dict)
    component_results: dict[str, ComponentResult] = Field(default_factory=dict)
    requested_answers: dict[str, QuantityValue] = Field(default_factory=dict)
    ac_node_voltages: dict[str, ComplexQuantityValue] = Field(default_factory=dict)
    ac_component_results: dict[str, ACComponentResult] = Field(default_factory=dict)
    ac_requested_answers: dict[str, ComplexQuantityValue] = Field(default_factory=dict)
    frequency_hz: float | None = None
    ac_sweep: list[ACFrequencyPoint] = Field(default_factory=list)
    transient_response: RCTransientResponse | None = None
    verification: VerificationReport = Field(default_factory=VerificationReport)
    verification_badge: VerificationBadge = Field(default_factory=VerificationBadge)
    calculation_trace: CalculationTrace = Field(default_factory=CalculationTrace)
    generated_netlist: str = ""
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)
