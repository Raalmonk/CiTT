from app.services.demo_parser import VOLTAGE_DIVIDER_TEXT
from app.services.gemini_parser import GeminiParserUnavailable
from app.services.parser_service import parse_problem


def test_gemini_parser_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini")

    assert result.parser_used == "demo"
    assert result.circuit.id == "voltage_divider"
    assert any("Fell back" in warning for warning in result.warnings)


def test_gemini_strict_without_api_key_returns_controlled_ambiguity(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini_strict")

    assert result.parser_used == "gemini_strict"
    assert result.circuit.id == "gemini_strict_parse_failed"
    assert result.circuit.ambiguities
    assert any("did not use demo fallback" in warning for warning in result.warnings)


def test_gemini_fallback_when_parser_raises(monkeypatch):
    import app.services.parser_service as parser_service

    def unavailable(_problem_text: str):
        raise GeminiParserUnavailable("mock Gemini outage")

    monkeypatch.setattr(parser_service, "parse_with_gemini", unavailable)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini")

    assert result.parser_used == "demo"
    assert result.circuit.id == "voltage_divider"
    assert any("mock Gemini outage" in warning for warning in result.warnings)
