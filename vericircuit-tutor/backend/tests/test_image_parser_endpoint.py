import base64

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services.parser_service import ParseResult
from app.services.demo_parser import voltage_divider_problem


def test_parse_image_endpoint_decodes_base64_and_returns_circuit(monkeypatch):
    captured: dict[str, object] = {}

    def fake_parse_image_problem(*, problem_text: str, image_bytes: bytes, mime_type: str):
        captured["problem_text"] = problem_text
        captured["image_bytes"] = image_bytes
        captured["mime_type"] = mime_type
        return ParseResult(
            circuit=voltage_divider_problem(),
            parser_used="gemini_image",
            warnings=[],
        )

    monkeypatch.setattr(main_module, "parse_image_problem", fake_parse_image_problem)
    payload = {
        "problem_text": "Find Vout from this schematic.",
        "mime_type": "image/png",
        "image_base64": base64.b64encode(b"fake-image").decode("ascii"),
    }

    response = TestClient(app).post("/parse_image", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["parser_used"] == "gemini_image"
    assert body["circuit_ir"]["id"] == "voltage_divider"
    assert captured == {
        "problem_text": "Find Vout from this schematic.",
        "image_bytes": b"fake-image",
        "mime_type": "image/png",
    }


def test_parse_image_endpoint_rejects_invalid_base64():
    response = TestClient(app).post(
        "/parse_image",
        json={
            "problem_text": "Find Vout.",
            "mime_type": "image/png",
            "image_base64": "not base64",
        },
    )

    assert response.status_code == 400
