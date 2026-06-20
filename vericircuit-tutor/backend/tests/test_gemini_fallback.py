import json
from pathlib import Path

from app.models.circuit_ir import CircuitProblem
from app.models.runtime_debug import RuntimeDebugTrace
from app.services.gemini_client import DEFAULT_GEMINI_MODEL
from app.services.gemini_parser import (
    GeminiAPICircuitProblem,
    GeminiAPIComponent,
    GeminiAPIGoal,
    GeminiCircuitProblem,
    GeminiComponent,
    GeminiGoal,
    GeminiParserUnavailable,
    _image_schema_prompt,
    _schema_prompt,
    parse_image_with_gemini,
    parse_with_gemini,
)
from app.services.parser_service import parse_problem

VOLTAGE_DIVIDER_TEXT = (
    "A 10 V voltage source is connected in series with R1 = 2 kOhm and "
    "R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit."
)


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
    def __init__(self, response: GeminiResponse | list[GeminiResponse | Exception]):
        self.responses = list(response) if isinstance(response, list) else [response]
        self.config = None
        self.model = None
        self.contents = None
        self.calls = 0

    def generate_content(self, *, model, contents, config):
        self.calls += 1
        self.model = model
        self.contents = contents
        self.config = config
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, response: GeminiResponse | list[GeminiResponse | Exception], api_key: str):
        self.api_key = api_key
        self.models = FakeModels(response)


def install_fake_gemini_client(
    monkeypatch,
    response: GeminiResponse | list[GeminiResponse | Exception],
) -> FakeClient:
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


def test_gemini_parser_returns_ambiguity_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini")

    assert result.parser_used == "gemini"
    assert result.circuit.id == "gemini_parse_failed"
    assert result.circuit.ambiguities
    assert any("No built-in parser fallback" in warning for warning in result.warnings)


def test_gemini_strict_without_api_key_returns_controlled_ambiguity(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini_strict")

    assert result.parser_used == "gemini"
    assert result.circuit.id == "gemini_parse_failed"
    assert result.circuit.ambiguities
    assert any("No built-in parser fallback" in warning for warning in result.warnings)


def test_gemini_parser_error_returns_ambiguity_without_fallback(monkeypatch):
    import app.services.parser_service as parser_service

    def unavailable(_problem_text: str, **_kwargs):
        raise GeminiParserUnavailable("mock Gemini outage")

    monkeypatch.setattr(parser_service, "parse_with_gemini", unavailable)

    result = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="gemini")

    assert result.parser_used == "gemini"
    assert result.circuit.id == "gemini_parse_failed"
    assert any("mock Gemini outage" in warning for warning in result.warnings)
    assert any("No built-in parser fallback" in warning for warning in result.warnings)


def test_parse_with_gemini_uses_parsed_model(monkeypatch):
    parsed = gemini_api_voltage_divider()
    fake_client = install_fake_gemini_client(monkeypatch, GeminiResponse(parsed=parsed))
    debug_trace = RuntimeDebugTrace()

    circuit = parse_with_gemini("mock parse request", debug_trace=debug_trace)

    assert isinstance(circuit, CircuitProblem)
    assert circuit.id == "gemini_voltage_divider"
    assert circuit.components[0].id == "V1"
    assert fake_client.api_key == "test-key"
    assert fake_client.models.model == DEFAULT_GEMINI_MODEL
    assert fake_client.models.config.response_mime_type == "application/json"
    assert fake_client.models.config.response_json_schema == GeminiAPICircuitProblem.model_json_schema()
    labels = [event.label for event in debug_trace.events]
    assert "request" in labels
    assert "response" in labels
    assert "gemini_json_validated" in labels
    request = next(event for event in debug_trace.events if event.label == "request")
    response = next(event for event in debug_trace.events if event.label == "response")
    assert request.data["model"] == DEFAULT_GEMINI_MODEL
    assert "mock parse request" in str(request.data["prompt"])
    assert "api_key" not in request.model_dump_json().lower()
    assert "response_text" in response.data


def test_parse_with_gemini_retries_transient_disconnect(monkeypatch):
    class RemoteProtocolError(Exception):
        pass

    parsed = gemini_api_voltage_divider()
    fake_client = install_fake_gemini_client(
        monkeypatch,
        [
            RemoteProtocolError("Server disconnected without sending a response."),
            GeminiResponse(parsed=parsed),
        ],
    )
    monkeypatch.setattr("app.services.gemini_client.time.sleep", lambda _delay: None)
    debug_trace = RuntimeDebugTrace()

    circuit = parse_with_gemini("mock parse request", debug_trace=debug_trace)

    assert circuit.id == "gemini_voltage_divider"
    assert fake_client.models.calls == 2
    retry = next(event for event in debug_trace.events if event.label == "retry")
    assert retry.data["error_type"] == "RemoteProtocolError"
    assert retry.data["next_attempt"] == 2
    assert any(event.label == "response" for event in debug_trace.events)


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


def test_parse_image_with_gemini_uses_image_part_and_schema(monkeypatch):
    parsed = gemini_api_voltage_divider()
    fake_client = install_fake_gemini_client(monkeypatch, GeminiResponse(parsed=parsed))
    debug_trace = RuntimeDebugTrace()

    circuit = parse_image_with_gemini(
        problem_text="Find Vout.",
        image_bytes=b"fake-png-bytes",
        mime_type="image/png",
        debug_trace=debug_trace,
    )

    assert circuit.id == "gemini_voltage_divider"
    assert fake_client.models.config.response_json_schema == GeminiAPICircuitProblem.model_json_schema()
    assert len(fake_client.models.contents) == 2
    image_request = next(event for event in debug_trace.events if event.label == "image_request")
    assert image_request.data["image"] == {"mime_type": "image/png", "byte_count": 14}
    assert "fake-png-bytes" not in image_request.model_dump_json()


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
    assert "Do not create numeric placeholder values" in prompt
    assert "nonblocking_ambiguities" in prompt


def test_gemini_image_prompt_supports_schematic_recognition():
    prompt = _image_schema_prompt("Find the output voltage.")

    assert "Parse the attached schematic/image" in prompt
    assert "visible component labels" in prompt
    assert "fill ambiguities instead of guessing" in prompt
    assert "nonblocking_ambiguities" in prompt
    assert "placeholder-valued components" in prompt


def test_gemini_strict_succeeds_when_gemini_parse_succeeds(monkeypatch):
    import app.services.parser_service as parser_service

    circuit = CircuitProblem.model_validate(gemini_voltage_divider().model_dump())
    monkeypatch.setattr(parser_service, "parse_with_gemini", lambda _problem_text, **_kwargs: circuit)

    result = parse_problem("mock parse request", mode="gemini_strict")

    assert result.parser_used == "gemini"
    assert result.circuit.id == "gemini_voltage_divider"
    assert result.warnings == []


def test_api_keys_do_not_appear_in_frontend_source():
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    frontend_files = [frontend_dir / "index.html", *frontend_dir.glob("src/**/*")]
    frontend_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in frontend_files
        if path.is_file()
    )

    assert "GEMINI_API_KEY" not in frontend_text
    assert "GOOGLE_API_KEY" not in frontend_text
    assert "x-goog-api-key" not in frontend_text.lower()
    assert "AIza" not in frontend_text
