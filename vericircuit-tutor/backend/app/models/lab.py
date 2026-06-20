from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket


class LabScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_value_error_percent: dict[str, float] = Field(default_factory=dict)
    resistor_tolerance_percent: float | None = Field(default=None, gt=-100.0)
    capacitor_tolerance_percent: float | None = Field(default=None, gt=-100.0)
    inductor_tolerance_percent: float | None = Field(default=None, gt=-100.0)
    source_amplitude_error_percent: float | None = Field(default=None, gt=-100.0)
    source_dc_offset_v: float | None = None
    op_amp_input_bias_current_a: float | None = None
    op_amp_input_offset_voltage_v: float | None = None
    op_amp_open_loop_gain: float | None = Field(default=None, gt=0.0)
    supply_positive_v: float | None = None
    supply_negative_v: float | None = None
    output_swing_margin_v: float | None = Field(default=None, ge=0.0)
    slew_rate_v_per_s: float | None = Field(default=None, gt=0.0)
    enable_bias_compensation: bool = False
    breadboard_leakage_ohm: float | None = Field(default=None, gt=0.0)
    breadboard_shunt_capacitance_f: float | None = Field(default=None, gt=0.0)
    readout_gain_error_percent: float | None = Field(default=None, gt=-100.0)
    readout_offset_v: float | None = None


class LabSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_ir: CircuitProblem
    baseline_packet: SolutionPacket | None = None
    scenario: LabScenario = Field(default_factory=LabScenario)
    parser_used: str | None = None


class LabAppliedModification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal[
        "component_value",
        "source_generation",
        "op_amp_nonideality",
        "bias_compensation",
        "breadboard_parasitic",
        "measurement_readout",
    ]
    target: str
    before_value: float | None = None
    after_value: float | None = None
    unit: str | None = None
    note: str


class LabComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    source: Literal[
        "requested_answer",
        "node_voltage",
        "ac_requested_answer",
        "ac_node_voltage",
        "transient",
    ]
    unit: str
    baseline_value: float
    lab_value: float
    measured_value: float
    delta: float
    relative_error_percent: float | None = None
    note: str = ""


class LabObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    severity: Literal["notice", "watch", "failure", "success"]
    title: str
    body: str
    value: float | None = None
    unit: str | None = None
    focus_component_ids: list[str] = Field(default_factory=list)
    focus_node_ids: list[str] = Field(default_factory=list)


class LabSensitivityPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_value: float
    lab_value: float
    measured_value: float
    delta: float
    relative_error_percent: float | None = None


class LabSensitivitySweep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    x_label: str
    x_unit: str
    y_label: str
    y_unit: str
    comparison_id: str
    points: list[LabSensitivityPoint] = Field(default_factory=list)
    insight: str | None = None


class LabCounterfactual(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    summary: str
    comparisons: list[LabComparison] = Field(default_factory=list)
    applied_modifications: list[LabAppliedModification] = Field(default_factory=list)


class LabSimulationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_packet: SolutionPacket
    lab_packet: SolutionPacket
    lab_circuit: CircuitProblem
    applied_modifications: list[LabAppliedModification] = Field(default_factory=list)
    comparisons: list[LabComparison] = Field(default_factory=list)
    observations: list[LabObservation] = Field(default_factory=list)
    sensitivity_sweeps: list[LabSensitivitySweep] = Field(default_factory=list)
    counterfactuals: list[LabCounterfactual] = Field(default_factory=list)
    teaching_script: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
