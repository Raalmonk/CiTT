from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ComponentFlow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str
    component_type: str
    nodes: list[str]
    current_a: float
    abs_current_a: float
    direction_from: str
    direction_to: str
    voltage_v: float
    power_w: float
    is_zero_current: bool
    sign_convention: str


class NodeKclTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str
    other_node: str
    signed_current_leaving_a: float
    abs_current_a: float
    direction: Literal["entering", "leaving", "zero"]
    description: str


class NodeKclReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node: str
    voltage_v: float
    terms: list[NodeKclTerm]
    sum_leaving_a: float
    residual_a: float
    passed: bool


class AnalysisView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["available", "blocked"]
    badge: str
    reason: str | None = None
    component_flows: dict[str, ComponentFlow]
    node_kcl: dict[str, NodeKclReport]
