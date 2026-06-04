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


class ComponentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voltage: QuantityValue
    current: QuantityValue
    power: QuantityValue
    sign_convention: str


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


class SolutionPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_id: str
    status: ProblemStatus
    node_voltages: dict[str, float] = Field(default_factory=dict)
    component_results: dict[str, ComponentResult] = Field(default_factory=dict)
    requested_answers: dict[str, QuantityValue] = Field(default_factory=dict)
    verification: VerificationReport = Field(default_factory=VerificationReport)
    verification_badge: VerificationBadge = Field(default_factory=VerificationBadge)
    generated_netlist: str = ""
    warnings: list[str] = Field(default_factory=list)
    assumptions_used: list[str] = Field(default_factory=list)
