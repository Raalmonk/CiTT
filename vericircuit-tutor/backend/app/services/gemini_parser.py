from __future__ import annotations

import os

from app.models.circuit_ir import CircuitProblem


class GeminiParserUnavailable(RuntimeError):
    """Raised when Gemini parsing is unavailable and the caller should fall back."""


def _schema_prompt(problem_text: str) -> str:
    return f"""
Parse this undergraduate linear DC circuit problem into VeriCircuit Tutor Circuit IR.

Rules:
- Return only CircuitProblem JSON matching the provided schema.
- Normalize resistor values to ohms, voltages to volts, and currents to amperes.
- Use only resistor, voltage_source, and current_source components.
- If unsupported components appear, list them in unsupported_features and do not pretend to solve them.
- If topology is ambiguous, list ambiguities.
- Do not compute final numerical answers. Final answers are produced only by the internal MNA solver and verifier.

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
    schema = CircuitProblem.model_json_schema()

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=model,
            contents=_schema_prompt(problem_text),
            config={
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )
    except Exception as exc:
        raise GeminiParserUnavailable(f"Gemini structured parse failed: {exc}") from exc

    try:
        return CircuitProblem.model_validate_json(response.text)
    except ValueError as exc:
        raise GeminiParserUnavailable(f"Gemini did not return valid CircuitProblem JSON: {exc}") from exc

