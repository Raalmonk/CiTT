import base64
import os

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services.gemini_client import load_backend_dotenv
from app.services.parser_service import ParseResult
from app.services.demo_parser import voltage_divider_problem


def test_load_backend_dotenv_sets_missing_values_without_overwriting(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "GEMINI_API_KEY=dotenv-key",
                "GEMINI_MODEL=dotenv-model",
                "EXISTING_VALUE=dotenv-should-not-win",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("EXISTING_VALUE", "already-set")

    load_backend_dotenv(env_path)

    assert os.environ["GEMINI_API_KEY"] == "dotenv-key"
    assert os.environ["GEMINI_MODEL"] == "dotenv-model"
    assert os.environ["EXISTING_VALUE"] == "already-set"


def test_parser_config_reports_gemini_key_status_without_exposing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "secret-google-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    response = TestClient(app).get("/parser_config")

    assert response.status_code == 200
    assert response.json() == {
        "gemini_configured": True,
        "gemini_model": "gemini-test-model",
    }
    assert "secret-google-key" not in response.text


def test_parser_config_reports_missing_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    response = TestClient(app).get("/parser_config")

    assert response.status_code == 200
    assert response.json()["gemini_configured"] is False


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


def test_full_pipeline_image_endpoint_decodes_solves_and_returns_packet(monkeypatch):
    captured: dict[str, object] = {}

    def fake_parse_image_problem(*, problem_text: str, image_bytes: bytes, mime_type: str):
        captured["problem_text"] = problem_text
        captured["image_bytes"] = image_bytes
        captured["mime_type"] = mime_type
        return ParseResult(
            circuit=voltage_divider_problem(),
            parser_used="gemini_image",
            warnings=["image parser warning"],
        )

    monkeypatch.setattr(main_module, "parse_image_problem", fake_parse_image_problem)

    response = TestClient(app).post(
        "/full_pipeline_image",
        json={
            "problem_text": "Solve the uploaded divider.",
            "mime_type": "image/jpeg",
            "image_base64": base64.b64encode(b"fake-jpeg").decode("ascii"),
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["parser_used"] == "gemini_image"
    assert payload["circuit_ir"]["id"] == "voltage_divider"
    assert payload["solution_packet"]["verification_badge"]["label"] == "PASS"
    assert payload["solution_packet"]["calculation_trace"]["parser_used"] == "gemini_image"
    assert "image parser warning" in payload["warnings"]
    assert captured == {
        "problem_text": "Solve the uploaded divider.",
        "image_bytes": b"fake-jpeg",
        "mime_type": "image/jpeg",
    }
