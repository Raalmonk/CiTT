from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import CircuitProblem
from app.services.gemini_client import (
    GeminiClientUnavailable,
    GeminiStructuredClient,
    gemini_api_key,
    gemini_is_configured,
)


class GeminiParserUnavailable(RuntimeError):
    """Raised when Gemini parsing is unavailable and the caller should fall back."""


class GeminiGoalReference(BaseModel):
    positive_node: str | None = None
    negative_node: str | None = None
    from_node: str | None = None
    to_node: str | None = None
    component: str | None = None


class GeminiAPIACSweep(BaseModel):
    start_hz: float
    stop_hz: float
    points_per_decade: int = 20
    scale: Literal["log", "linear"] = "log"


class GeminiAPIRCTransient(BaseModel):
    capacitor_id: str | None = None
    initial_voltage_v: float = 0.0
    time_points_s: list[float] = Field(default_factory=list)


class GeminiAPIComponent(BaseModel):
    id: str = Field(min_length=1)
    type: Literal[
        "resistor",
        "voltage_source",
        "current_source",
        "capacitor",
        "inductor",
        "op_amp_ideal",
        "ideal_op_amp",
    ]
    nodes: list[str] = Field(min_length=2, max_length=4)
    value: float
    unit: Literal["ohm", "V", "A", "F", "H", "ideal"]
    label: str | None = None
    ac_magnitude: float | None = None
    ac_phase_deg: float | None = None


class GeminiAPIGoal(BaseModel):
    id: str = Field(min_length=1)
    quantity: Literal[
        "node_voltage",
        "component_voltage",
        "component_current",
        "component_power",
        "source_power",
    ]
    target: str = Field(min_length=1)
    reference: GeminiGoalReference | None = None


class GeminiAPICircuitProblem(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    analysis_type: Literal[
        "dc_operating_point",
        "ac_steady_state",
        "ac_single_frequency",
        "ac_sweep",
        "rc_transient",
    ]
    frequency_hz: float | None = None
    sweep: GeminiAPIACSweep | None = None
    transient: GeminiAPIRCTransient | None = None
    topology_id: Literal[
        "voltage_divider",
        "current_divider",
        "bridge_network",
        "rc_low_pass",
        "rc_transient_charging",
        "op_amp_non_inverting",
    ] | None = None
    ground_node: str = "0"
    nodes: list[str] = Field(default_factory=list)
    components: list[GeminiAPIComponent] = Field(default_factory=list)
    goals: list[GeminiAPIGoal] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    unsupported_features: list[str] = Field(default_factory=list)


class GeminiACSweep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_hz: float
    stop_hz: float
    points_per_decade: int = 20
    scale: Literal["log", "linear"] = "log"


class GeminiRCTransient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capacitor_id: str | None = None
    initial_voltage_v: float = 0.0
    time_points_s: list[float] = Field(default_factory=list)


class GeminiComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: Literal[
        "resistor",
        "voltage_source",
        "current_source",
        "capacitor",
        "inductor",
        "op_amp_ideal",
        "ideal_op_amp",
    ]
    nodes: list[str] = Field(min_length=2, max_length=4)
    value: float
    unit: Literal["ohm", "V", "A", "F", "H", "ideal"]
    label: str | None = None
    ac_magnitude: float | None = None
    ac_phase_deg: float | None = None


class GeminiGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    quantity: Literal[
        "node_voltage",
        "component_voltage",
        "component_current",
        "component_power",
        "source_power",
    ]
    target: str = Field(min_length=1)
    reference: GeminiGoalReference | None = None


class GeminiCircuitProblem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    analysis_type: Literal[
        "dc_operating_point",
        "ac_steady_state",
        "ac_single_frequency",
        "ac_sweep",
        "rc_transient",
    ]
    frequency_hz: float | None = None
    sweep: GeminiACSweep | None = None
    transient: GeminiRCTransient | None = None
    topology_id: Literal[
        "voltage_divider",
        "current_divider",
        "bridge_network",
        "rc_low_pass",
        "rc_transient_charging",
        "op_amp_non_inverting",
    ] | None = None
    ground_node: str = "0"
    nodes: list[str] = Field(default_factory=list)
    components: list[GeminiComponent] = Field(default_factory=list)
    goals: list[GeminiGoal] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    unsupported_features: list[str] = Field(default_factory=list)


def _schema_prompt(problem_text: str) -> str:
    return f"""
Parse this undergraduate linear circuit problem into VeriCircuit Tutor Circuit IR.

Rules:
- Return only JSON matching the provided schema.
- Do not solve the circuit.
- Do not compute final voltages, currents, powers, requested answers, or explanations.
- The user may ask to create, generate, model, draw, or describe a circuit rather than ask a textbook calculation question. Still produce Circuit IR from the stated topology and component values.
- If no requested measurement or calculation target is explicit, leave goals empty rather than inventing a goal.
- Normalize kOhm and kilohm values to ohms, mA values to A, microfarads to F, and all voltages to V.
- Allowed component types are resistor, voltage_source, current_source, capacitor, inductor, op_amp_ideal, and ideal_op_amp.
- Use "0" as the ground node.
- For voltage sources, nodes[0] is the positive terminal and nodes[1] is the negative terminal.
- For current sources, positive current direction is from nodes[0] to nodes[1].
- For ideal op-amps, nodes must be [non_inverting, inverting, output, reference] and unit must be "ideal".
- Source ac_magnitude and ac_phase_deg define AC phasor amplitude and phase; leave them null for non-source components.
- If the problem asks for capacitor DC steady state, use analysis_type "dc_operating_point" with a capacitor component.
- If the problem asks for a first-order RC charging or discharging transient with one capacitor, use analysis_type "rc_transient", include one capacitor component, and set transient.initial_voltage_v. Use transient.time_points_s for requested evaluation times.
- If the problem asks for sinusoidal steady-state, phasor, impedance, filters at one frequency, or a single AC frequency, use "ac_steady_state" and set frequency_hz.
- If the problem asks for frequency response, Bode data, or an AC sweep, use "ac_sweep" and set sweep.
- For AC steady-state, capacitors use impedance 1/(j omega C), inductors use impedance j omega L, and source ac_magnitude/ac_phase_deg define phasors.
- If the problem asks for general transient/time-domain response beyond a first-order RC template, list "transient analysis" in unsupported_features.
- If an op-amp is ideal and closed-loop assumptions are clear, use ideal_op_amp.
- If op-amp rails, saturation, slew rate, bias current, finite bandwidth, or nonideal frequency response is requested, list it in unsupported_features.
- Biomedical words such as ECG, EMG, pressure, strain, thermistor, photodiode, or anti-aliasing do not by themselves justify guessing circuit topology, physiology, safety claims, or BME template metadata.
- If biomedical component values and connectivity are explicit, parse them as ordinary Circuit IR and put only stated assumptions in assumptions.
- If a biomedical prompt appears to request a known BME template but leaves topology, values, sensor model, or signal-chain role ambiguous, fill ambiguities instead of inventing a template.
- Do not return bme_metadata from Gemini; deterministic server templates attach that context after strict template matching.
- If unsupported components appear, list them in unsupported_features and do not pretend to solve them.
- If topology or connectivity is ambiguous, fill ambiguities instead of guessing.
- Final numerical answers are produced only by the internal MNA solver and verifier.

Problem:
{problem_text}
""".strip()


def _api_key_is_present() -> bool:
    return gemini_is_configured()


def parse_with_gemini(problem_text: str) -> CircuitProblem:
    if not gemini_api_key():
        raise GeminiParserUnavailable("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

    try:
        response_text = GeminiStructuredClient().generate_json_text(
            prompt=_schema_prompt(problem_text),
            schema_model=GeminiAPICircuitProblem,
        )
    except GeminiClientUnavailable as exc:
        raise GeminiParserUnavailable(str(exc)) from exc

    try:
        api_parsed = GeminiAPICircuitProblem.model_validate_json(response_text)
        strict_parsed = GeminiCircuitProblem.model_validate(api_parsed.model_dump())
        return CircuitProblem.model_validate(strict_parsed.model_dump())
    except ValueError as exc:
        raise GeminiParserUnavailable(f"Gemini did not return valid CircuitProblem JSON: {exc}") from exc
