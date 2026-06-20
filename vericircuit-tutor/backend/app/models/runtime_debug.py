from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RuntimeDebugEvent(BaseModel):
    stage: str = Field(min_length=1)
    label: str = Field(min_length=1)
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: float | None = None


class RuntimeDebugTrace(BaseModel):
    enabled: bool = True
    events: list[RuntimeDebugEvent] = Field(default_factory=list)
    redaction_notes: list[str] = Field(
        default_factory=lambda: [
            "Gemini API keys are never included in debug output.",
            "Uploaded image bytes and base64 payloads are summarized by MIME type and byte count only.",
        ]
    )


def add_debug_event(
    trace: RuntimeDebugTrace | None,
    *,
    stage: str,
    label: str,
    message: str = "",
    data: dict[str, Any] | None = None,
    elapsed_ms: float | None = None,
) -> None:
    if trace is None or not trace.enabled:
        return
    trace.events.append(
        RuntimeDebugEvent(
            stage=stage,
            label=label,
            message=message,
            data=data or {},
            elapsed_ms=elapsed_ms,
        )
    )
