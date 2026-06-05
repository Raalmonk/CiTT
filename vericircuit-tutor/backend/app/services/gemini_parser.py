from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import CircuitProblem


class GeminiParserUnavailable(RuntimeError):
    """Raised when Gemini parsing is unavailable and the caller should fall back."""


class GeminiComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: Literal["resistor", "voltage_source", "current_source"]
    nodes: list[str] = Field(min_length=2, max_length=2)
    value: float
    unit: Literal["ohm", "V", "A"]
    label: str | None = None


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
    reference: dict[str, str] | None = None


class GeminiCircuitProblem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    analysis_type: Literal["dc_operating_point"]
    topology_id: Literal["voltage_divider", "current_divider", "bridge_network"] | None = None
    ground_node: str = "0"
    nodes: list[str] = Field(default_factory=list)
    components: list[GeminiComponent] = Field(default_factory=list)
    goals: list[GeminiGoal] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    unsupported_features: list[str] = Field(default_factory=list)


def _schema_prompt(problem_text: str) -> str:
    return f"""
Parse this undergraduate linear DC circuit problem into VeriCircuit Tutor Circuit IR.

Rules:
- Return only JSON matching the provided schema.
- Do not solve the circuit.
- Do not compute final voltages, currents, powers, requested answers, or explanations.
- Normalize kOhm and kilohm values to ohms, mA values to A, and all voltages to V.
- Use only resistor, voltage_source, and current_source components.
- Use "0" as the ground node.
- For voltage sources, nodes[0] is the positive terminal and nodes[1] is the negative terminal.
- For current sources, positive current direction is from nodes[0] to nodes[1].
- If unsupported components appear, list them in unsupported_features and do not pretend to solve them.
- If topology or connectivity is ambiguous, fill ambiguities instead of guessing.
- Final numerical answers are produced only by the internal MNA solver and verifier.

Problem:
{problem_text}
""".strip()


def _api_key_is_present() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def parse_with_gemini(problem_text: str) -> CircuitProblem:
    if not _api_key_is_present():
        raise GeminiParserUnavailable("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

    try:
        from google import genai
    except ImportError as exc:
        raise GeminiParserUnavailable(
            "google-genai is not installed. Install project dependencies before using Gemini mode."
        ) from exc

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    schema = GeminiCircuitProblem.model_json_schema()

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=model,
            contents=_schema_prompt(problem_text),
            config={
                "temperature": 0,
                "response_format": {
                    "text": {
                        "mime_type": "application/json",
                        "schema": schema,
                    }
                },
            },
        )
    except Exception as exc:
        raise GeminiParserUnavailable(f"Gemini structured parse failed: {exc}") from exc

    try:
        parsed = GeminiCircuitProblem.model_validate_json(response.text)
        return CircuitProblem.model_validate(parsed.model_dump())
    except ValueError as exc:
        raise GeminiParserUnavailable(f"Gemini did not return valid CircuitProblem JSON: {exc}") from exc
