from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VisualPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float


class VisualNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    position: VisualPoint
    role: Literal["ground", "input", "output", "internal"] = "internal"


class VisualComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    label: str
    nodes: list[str]
    role: Literal["source", "load", "filter", "feedback", "op_amp", "bridge", "generic"] = "generic"
    orientation: Literal["horizontal", "vertical", "triangle", "auto"] = "auto"


class VisualWire(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    from_node: str
    to_node: str
    component_id: str | None = None
    points: list[VisualPoint] = Field(default_factory=list)


class VisualAnnotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["ground", "polarity", "current_arrow", "phasor", "kcl", "note"]
    label: str
    target_type: Literal["node", "component", "goal", "circuit"]
    target_id: str


class VisualFocusRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    components: list[str] = Field(default_factory=list)
    nodes: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


class VisualOverlay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["goal_reference", "kcl_node", "current_path", "phasor_hint", "lesson_focus"]
    label: str
    focus_region_id: str | None = None
    enabled_by_default: bool = False


class VisualCircuit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_id: str
    renderer: str
    layout_strategy: str
    nodes: list[VisualNode] = Field(default_factory=list)
    components: list[VisualComponent] = Field(default_factory=list)
    wires: list[VisualWire] = Field(default_factory=list)
    annotations: list[VisualAnnotation] = Field(default_factory=list)
    overlays: list[VisualOverlay] = Field(default_factory=list)
    focus_regions: list[VisualFocusRegion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
