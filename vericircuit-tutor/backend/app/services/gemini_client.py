from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.models.runtime_debug import RuntimeDebugTrace, add_debug_event


DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
GEMINI_MAX_ATTEMPTS = 3
T = TypeVar("T", bound=BaseModel)


class GeminiClientUnavailable(RuntimeError):
    """Raised when Gemini cannot be called and the app should use fallback behavior."""


def _is_retryable_gemini_error(exc: Exception) -> bool:
    error_name = type(exc).__name__.lower()
    message = str(exc).lower()
    retry_markers = [
        "remoteprotocolerror",
        "server disconnected without sending a response",
        "connection reset",
        "connection aborted",
        "temporarily unavailable",
        "timeout",
        "timed out",
        "502",
        "503",
        "504",
    ]
    return any(marker in error_name or marker in message for marker in retry_markers)


def load_backend_dotenv(path: Path | None = None) -> None:
    env_path = path or Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


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

    def generate_json_text(
        self,
        *,
        prompt: str,
        schema_model: type[T],
        debug_trace: RuntimeDebugTrace | None = None,
    ) -> str:
        schema = schema_model.model_json_schema()
        add_debug_event(
            debug_trace,
            stage="gemini",
            label="request",
            message="Gemini structured text request.",
            data={
                "model": self.model,
                "prompt": prompt,
                "prompt_chars": len(prompt),
                "response_mime_type": "application/json",
                "response_json_schema": schema,
                "schema_model": schema_model.__name__,
            },
        )
        started = time.perf_counter()
        for attempt in range(1, GEMINI_MAX_ATTEMPTS + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=schema,
                    ),
                )
                break
            except Exception as exc:
                retryable = _is_retryable_gemini_error(exc)
                if retryable and attempt < GEMINI_MAX_ATTEMPTS:
                    delay_s = 0.25 * attempt
                    add_debug_event(
                        debug_trace,
                        stage="gemini",
                        label="retry",
                        message="Gemini structured text request hit a transient transport error; retrying.",
                        data={
                            "attempt": attempt,
                            "next_attempt": attempt + 1,
                            "max_attempts": GEMINI_MAX_ATTEMPTS,
                            "delay_s": delay_s,
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                        },
                        elapsed_ms=(time.perf_counter() - started) * 1000.0,
                    )
                    time.sleep(delay_s)
                    continue
                add_debug_event(
                    debug_trace,
                    stage="gemini",
                    label="error",
                    message="Gemini structured text request failed.",
                    data={
                        "attempt": attempt,
                        "max_attempts": GEMINI_MAX_ATTEMPTS,
                        "retryable": retryable,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                )
                raise GeminiClientUnavailable(f"Gemini structured request failed: {exc}") from exc

        response_text = getattr(response, "text", None)
        response_source = "text"
        if not response_text:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, BaseModel):
                    response_text = parsed.model_dump_json()
                else:
                    response_text = schema_model.model_validate(parsed).model_dump_json()
                response_source = "parsed"
            else:
                add_debug_event(
                    debug_trace,
                    stage="gemini",
                    label="empty_response",
                    message="Gemini returned an empty structured response.",
                    data={},
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                )
                raise GeminiClientUnavailable("Gemini returned an empty structured response.")
        response_text = str(response_text)
        add_debug_event(
            debug_trace,
            stage="gemini",
            label="response",
            message="Gemini structured text response.",
            data={
                "response_source": response_source,
                "response_text": response_text,
                "response_chars": len(response_text),
            },
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
        return response_text

    def generate_json_text_from_image(
        self,
        *,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        schema_model: type[T],
        debug_trace: RuntimeDebugTrace | None = None,
    ) -> str:
        schema = schema_model.model_json_schema()
        add_debug_event(
            debug_trace,
            stage="gemini",
            label="image_request",
            message="Gemini structured image request.",
            data={
                "model": self.model,
                "prompt": prompt,
                "prompt_chars": len(prompt),
                "image": {"mime_type": mime_type, "byte_count": len(image_bytes)},
                "response_mime_type": "application/json",
                "response_json_schema": schema,
                "schema_model": schema_model.__name__,
            },
        )
        started = time.perf_counter()
        for attempt in range(1, GEMINI_MAX_ATTEMPTS + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=[
                        self._types.Part.from_text(text=prompt),
                        self._types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    ],
                    config=self._types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=schema,
                    ),
                )
                break
            except Exception as exc:
                retryable = _is_retryable_gemini_error(exc)
                if retryable and attempt < GEMINI_MAX_ATTEMPTS:
                    delay_s = 0.25 * attempt
                    add_debug_event(
                        debug_trace,
                        stage="gemini",
                        label="image_retry",
                        message="Gemini structured image request hit a transient transport error; retrying.",
                        data={
                            "attempt": attempt,
                            "next_attempt": attempt + 1,
                            "max_attempts": GEMINI_MAX_ATTEMPTS,
                            "delay_s": delay_s,
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                        },
                        elapsed_ms=(time.perf_counter() - started) * 1000.0,
                    )
                    time.sleep(delay_s)
                    continue
                add_debug_event(
                    debug_trace,
                    stage="gemini",
                    label="image_error",
                    message="Gemini structured image request failed.",
                    data={
                        "attempt": attempt,
                        "max_attempts": GEMINI_MAX_ATTEMPTS,
                        "retryable": retryable,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                )
                raise GeminiClientUnavailable(
                    f"Gemini image structured request failed: {exc}"
                ) from exc

        response_text = getattr(response, "text", None)
        response_source = "text"
        if not response_text:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, BaseModel):
                    response_text = parsed.model_dump_json()
                else:
                    response_text = schema_model.model_validate(parsed).model_dump_json()
                response_source = "parsed"
            else:
                add_debug_event(
                    debug_trace,
                    stage="gemini",
                    label="empty_image_response",
                    message="Gemini returned an empty structured image response.",
                    data={},
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                )
                raise GeminiClientUnavailable("Gemini returned an empty structured image response.")
        response_text = str(response_text)
        add_debug_event(
            debug_trace,
            stage="gemini",
            label="image_response",
            message="Gemini structured image response.",
            data={
                "response_source": response_source,
                "response_text": response_text,
                "response_chars": len(response_text),
            },
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
        return response_text
