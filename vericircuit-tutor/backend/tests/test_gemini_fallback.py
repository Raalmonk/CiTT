import json
from pathlib import Path

from app.models.circuit_ir import CircuitProblem
from app.services.gemini_client import DEFAULT_GEMINI_MODEL
from app.services.demo_parser import VOLTAGE_DIVIDER_TEXT
from app.services.gemini_parser import (
    GeminiAPICircuitProblem,
    GeminiAPIComponent,
    GeminiAPIGoal,
    GeminiCircuitProblem,
    GeminiComponent,
    GeminiGoal,
    GeminiParserUnavailable,
    _schema_prompt,
    parse_with_gemini,
)
from app.services.parser_service import parse_problem


def gemini_api_voltage_divider() -> GeminiAPICircuitProblem:
    return GeminiAPICircuitProblem(
        id="gemini_voltage_divider",
        title="Gemini Voltage Divider Parse",
        analysis_type="dc_operating_point",
        topology_id="voltage_divider",
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            GeminiAPIComponent(
                id="V1",
                type="voltage_source",
                nodes=["n1", "0"],
                value=5.0,
                unit="V",
            ),
            GeminiAPIComponent(
                id="R1",
                type="resistor",
                nodes=["n1", "n2"],
                value=1000.0,
                unit="ohm",
            ),
            GeminiAPIComponent(
                id="R2",
                type="resistor",
                nodes=["n2", "0"],
                value=4000.0,
                unit="ohm",
            ),
        ],
        goals=[
            GeminiAPIGoal(
                id="voltage_across_R2",
                quantity="component_voltage",
                target="R2",
                reference={"positive_node": "n2", "negative_node": "0"},
            )
        ],
        assumptions=["Voltage source positive terminal is node n1."],
        ambiguities=[],
        unsupported_features=[],
    )


def gemini_voltage_divider() -> GeminiCircuitProblem:
    return GeminiCircuitProblem(
        id="gemini_voltage_divider",
        title="Gemini Voltage Divider Parse",
        analysis_type="dc_operating_point",
        topology_id="voltage_divider",
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            GeminiComponent(
                id="V1",
                type="voltage_source",
                nodes=["n1", "0"],
                value=5.0,
                unit="V",
            ),
            GeminiComponent(
                id="R1",
                type="resistor",
                nodes=["n1", "n2"],
                value=1000.0,
                unit="ohm",
            ),
            GeminiComponent(
                id="R2",
                type="resistor",
                nodes=["n2", "0"],
                value=4000.0,
                unit="ohm",
            ),
        ],
        goals=[
            GeminiGoal(
                id="voltage_across_R2",
                quantity="component_voltage",
                target="R2",
                reference={"positive_node": "n2", "negative_node": "0"},
            )
        ],
        assumptions=["Voltage source positive terminal is node n1."],
        ambiguities=[],
        unsupported_features=[],
    )


class GeminiResponse:
    def __init__(self, *, parsed=None, text: str = ""):
        self.parsed = parsed
        self.text = text


class FakeModels:
    def __init__(self, response: GeminiResponse):
        self.response = response
        self.config = None
        self.model = None

    def generate_content(self, *, model, contents, config):
        self.model = model
        self.config = config
        return self.response


class FakeClient:
    def __init__(self, response: GeminiResponse, api_key: str):
        self.api_key = api_key
        self.models = FakeModels(response)


def install_fake_gemini_client(monkeypatch, response: GeminiResponse) -> FakeClient:
    from google import genai

    fake_client = FakeClient(response, api_key="")

    def client_factory(*, api_key: str) -> FakeClient:
        fake_client.api_key = api_key
        return fake_client

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(genai, "Client", client_factory)
    return fake_client


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


def test_parse_with_gemini_uses_parsed_model(monkeypatch):
    parsed = gemini_api_voltage_divider()
    fake_client = install_fake_gemini_client(monkeypatch, GeminiResponse(parsed=parsed))

    circuit = parse_with_gemini("mock parse request")

    assert isinstance(circuit, CircuitProblem)
    assert circuit.id == "gemini_voltage_divider"
    assert circuit.components[0].id == "V1"
    assert fake_client.api_key == "test-key"
    assert fake_client.models.model == DEFAULT_GEMINI_MODEL
    assert fake_client.models.config.response_mime_type == "application/json"
    assert fake_client.models.config.response_json_schema == GeminiAPICircuitProblem.model_json_schema()


def test_parse_with_gemini_falls_back_to_response_text_json(monkeypatch):
    parsed = gemini_api_voltage_divider()
    install_fake_gemini_client(
        monkeypatch,
        GeminiResponse(parsed=None, text=json.dumps(parsed.model_dump())),
    )

    circuit = parse_with_gemini("mock parse request")

    assert isinstance(circuit, CircuitProblem)
    assert circuit.id == "gemini_voltage_divider"
    assert circuit.goals[0].id == "voltage_across_R2"


def test_parse_with_gemini_accepts_google_api_key(monkeypatch):
    parsed = gemini_api_voltage_divider()
    fake_client = install_fake_gemini_client(
        monkeypatch,
        GeminiResponse(parsed=None, text=json.dumps(parsed.model_dump())),
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-test-key")

    circuit = parse_with_gemini("mock parse request")

    assert circuit.id == "gemini_voltage_divider"
    assert fake_client.api_key == "google-test-key"


def test_gemini_api_schema_omits_additional_properties():
    schema = GeminiAPICircuitProblem.model_json_schema()
    serialized = json.dumps(schema)

    assert "additionalProperties" not in serialized


def test_gemini_prompt_supports_circuit_generation_not_only_questions():
    prompt = _schema_prompt(
        "Generate a Circuit IR for a 5 V source feeding two resistors in series."
    )

    assert "create, generate, model, draw, or describe a circuit" in prompt
    assert "leave goals empty rather than inventing a goal" in prompt


def test_gemini_strict_succeeds_when_gemini_parse_succeeds(monkeypatch):
    import app.services.parser_service as parser_service

    circuit = CircuitProblem.model_validate(gemini_voltage_divider().model_dump())
    monkeypatch.setattr(parser_service, "parse_with_gemini", lambda _problem_text: circuit)

    result = parse_problem("mock parse request", mode="gemini_strict")

    assert result.parser_used == "gemini"
    assert result.circuit.id == "gemini_voltage_divider"
    assert result.warnings == []


def test_api_keys_do_not_appear_in_static_frontend():
    static_dir = Path(__file__).resolve().parents[1] / "app" / "static"
    static_text = "\n".join(path.read_text(encoding="utf-8") for path in static_dir.rglob("*") if path.is_file())

    assert "GEMINI_API_KEY" not in static_text
    assert "GOOGLE_API_KEY" not in static_text
    assert "x-goog-api-key" not in static_text.lower()
    assert "AIza" not in static_text
