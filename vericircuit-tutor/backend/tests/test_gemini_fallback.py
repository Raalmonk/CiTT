from app.services.demo_parser import VOLTAGE_DIVIDER_TEXT
from app.services.parser_service import parse_problem


def test_gemini_parser_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini")

    assert result.parser_used == "demo"
    assert result.circuit.id == "voltage_divider"
    assert any("Fell back" in warning for warning in result.warnings)

