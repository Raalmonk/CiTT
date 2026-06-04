from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from app.models.circuit_ir import CircuitProblem


class GeminiParserUnavailable(RuntimeError):
    """Raised when Gemini parsing is unavailable and the caller should fall back."""


def _schema_prompt(problem_text: str) -> str:
    return f"""
You are parsing an undergraduate linear DC circuit problem into VeriCircuit Tutor Circuit IR.
Return only JSON matching this shape:
{{
  "id": "string",
  "title": "string",
  "analysis_type": "dc_operating_point",
  "ground_node": "0",
  "nodes": ["0"],
  "components": [
    {{
      "id": "R1",
      "type": "resistor | voltage_source | current_source",
      "nodes": ["n1", "0"],
      "value": 1000.0,
      "unit": "ohm | V | A",
      "label": "optional",
      "current_reference": {{"from_node": "n1", "to_node": "0"}},
      "voltage_reference": {{"positive_node": "n1", "negative_node": "0"}}
    }}
  ],
  "goals": [
    {{
      "id": "string",
      "quantity": "node_voltage | component_voltage | component_current | component_power | source_power",
      "target": "node_or_component_id",
      "reference": {{}}
    }}
  ],
  "assumptions": [],
  "ambiguities": [],
  "unsupported_features": []
}}

Rules:
- Normalize resistor values to ohms, voltages to volts, and currents to amperes.
- Use only resistor, voltage_source, and current_source components.
- If unsupported components appear, list them in unsupported_features and do not pretend to solve them.
- If topology is ambiguous, list ambiguities.

Problem:
{problem_text}
""".strip()


def parse_with_gemini(problem_text: str) -> CircuitProblem:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiParserUnavailable("GEMINI_API_KEY is not set.")

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:"
        f"generateContent?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _schema_prompt(problem_text)}],
            }
        ],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GeminiParserUnavailable(f"Gemini request failed: {exc}") from exc

    try:
        response_json = json.loads(raw)
        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        return CircuitProblem.model_validate_json(text)
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        raise GeminiParserUnavailable(f"Gemini did not return valid Circuit IR: {exc}") from exc

