from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


AnalysisType = Literal["dc_operating_point"]
ComponentType = str
GoalQuantity = Literal[
    "node_voltage",
    "component_voltage",
    "component_current",
    "component_power",
    "source_power",
]


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: ComponentType = Field(
        min_length=1,
        json_schema_extra={"enum": ["resistor", "voltage_source", "current_source"]},
    )
    nodes: list[str] = Field(min_length=2, max_length=2)
    value: float
    unit: str
    label: str | None = None
    current_reference: dict[str, Any] | None = None
    voltage_reference: dict[str, Any] | None = None

    @field_validator("nodes")
    @classmethod
    def nodes_must_be_two_non_empty_names(cls, nodes: list[str]) -> list[str]:
        if len(nodes) != 2:
            raise ValueError("components must connect exactly two nodes")
        if any(not node or not node.strip() for node in nodes):
            raise ValueError("component node names must be non-empty")
        return nodes

    @field_validator("type")
    @classmethod
    def type_must_be_non_empty(cls, component_type: str) -> str:
        if not component_type or not component_type.strip():
            raise ValueError("component type must be non-empty")
        return component_type

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("component value must be finite")
        return value


class Goal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    quantity: GoalQuantity
    target: str = Field(min_length=1)
    reference: dict[str, Any] | None = None


class CircuitProblem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    analysis_type: AnalysisType = "dc_operating_point"
    ground_node: str = "0"
    nodes: list[str] = Field(default_factory=lambda: ["0"])
    components: list[Component] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    unsupported_features: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_nodes(self) -> "CircuitProblem":
        if not self.ground_node:
            self.ground_node = "0"

        ordered_nodes: list[str] = []
        for node in [*self.nodes, self.ground_node]:
            if node and node not in ordered_nodes:
                ordered_nodes.append(node)
        for component in self.components:
            for node in component.nodes:
                if node not in ordered_nodes:
                    ordered_nodes.append(node)
        self.nodes = ordered_nodes
        return self
