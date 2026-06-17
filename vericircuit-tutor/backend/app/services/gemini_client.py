from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel


DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
T = TypeVar("T", bound=BaseModel)


class GeminiClientUnavailable(RuntimeError):
    """Raised when Gemini cannot be called and the app should use fallback behavior."""


def gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def gemini_is_configured() -> bool:
    return bool(gemini_api_key())


class GeminiStructuredClient:
    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or gemini_api_key()
        self.model = model or gemini_model()
        if not self.api_key:
            raise GeminiClientUnavailable("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise GeminiClientUnavailable(
                "google-genai is not installed. Install project dependencies before using Gemini mode."
            ) from exc

        self._types = types
        self._client = genai.Client(api_key=self.api_key)

    def generate_json_text(self, *, prompt: str, schema_model: type[T]) -> str:
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=schema_model.model_json_schema(),
                ),
            )
        except Exception as exc:
            raise GeminiClientUnavailable(f"Gemini structured request failed: {exc}") from exc

        response_text = getattr(response, "text", None)
        if not response_text:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, BaseModel):
                    return parsed.model_dump_json()
                return schema_model.model_validate(parsed).model_dump_json()
            raise GeminiClientUnavailable("Gemini returned an empty structured response.")
        return str(response_text)

    def generate_json_text_from_image(
        self,
        *,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        schema_model: type[T],
    ) -> str:
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[
                    self._types.Part.from_text(text=prompt),
                    self._types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=self._types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=schema_model.model_json_schema(),
                ),
            )
        except Exception as exc:
            raise GeminiClientUnavailable(
                f"Gemini image structured request failed: {exc}"
            ) from exc

        response_text = getattr(response, "text", None)
        if not response_text:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, BaseModel):
                    return parsed.model_dump_json()
                return schema_model.model_validate(parsed).model_dump_json()
            raise GeminiClientUnavailable("Gemini returned an empty structured image response.")
        return str(response_text)
