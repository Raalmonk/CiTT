from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


AnalysisType = Literal["dc_operating_point", "ac_single_frequency", "ac_sweep"]
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
        json_schema_extra={
            "enum": [
                "resistor",
                "voltage_source",
                "current_source",
                "capacitor",
                "op_amp_ideal",
            ]
        },
    )
    nodes: list[str] = Field(min_length=2, max_length=4)
    value: float
    unit: str
    label: str | None = None
    current_reference: dict[str, Any] | None = None
    voltage_reference: dict[str, Any] | None = None
    ac_magnitude: float | None = None
    ac_phase_deg: float | None = None

    @field_validator("nodes")
    @classmethod
    def nodes_must_be_non_empty_names(cls, nodes: list[str]) -> list[str]:
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

    @field_validator("ac_magnitude", "ac_phase_deg")
    @classmethod
    def ac_values_must_be_finite(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("AC phasor values must be finite")
        return value

    @model_validator(mode="after")
    def node_count_matches_component_type(self) -> "Component":
        if self.type == "op_amp_ideal":
            if len(self.nodes) != 4:
                raise ValueError(
                    "op_amp_ideal must use four nodes: [non_inverting, inverting, output, reference]"
                )
        elif len(self.nodes) != 2:
            raise ValueError("two-terminal components must connect exactly two nodes")
        return self


class ACSweep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_hz: float
    stop_hz: float
    points_per_decade: int = 20
    scale: Literal["log", "linear"] = "log"

    @model_validator(mode="after")
    def validate_sweep(self) -> "ACSweep":
        if not math.isfinite(self.start_hz) or self.start_hz <= 0:
            raise ValueError("sweep start_hz must be positive")
        if not math.isfinite(self.stop_hz) or self.stop_hz <= 0:
            raise ValueError("sweep stop_hz must be positive")
        if self.stop_hz <= self.start_hz:
            raise ValueError("sweep stop_hz must be greater than start_hz")
        if self.points_per_decade <= 0:
            raise ValueError("sweep points_per_decade must be positive")
        return self


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
    frequency_hz: float | None = None
    sweep: ACSweep | None = None
    topology_id: str | None = None
    layout_hint: dict[str, Any] | None = None
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

    @field_validator("frequency_hz")
    @classmethod
    def frequency_must_be_positive(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or value <= 0):
            raise ValueError("frequency_hz must be positive")
        return value
