import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.circuit_ir import CircuitProblem
from app.services.demo_parser import voltage_divider_problem
from app.services.gemini_parser import GeminiCircuitProblem, GeminiComponent, GeminiGoal
from app.services.pipeline import solve_circuit


def test_circuit_problem_rejects_injected_final_numerical_answers():
    payload = voltage_divider_problem().model_dump()
    payload["final_answer"] = {"voltage_across_R2": "999 V"}

    with pytest.raises(ValidationError):
        CircuitProblem.model_validate(payload)


def test_parser_ir_has_no_numerical_answer_fields_and_solver_still_owns_answer():
    circuit = voltage_divider_problem()
    assert not hasattr(circuit, "final_answer")
    assert not hasattr(circuit, "requested_answers")

    packet = solve_circuit(circuit, parser_used="fixture")

    assert packet.requested_answers["voltage_across_R2"].value == pytest.approx(6.0)
    assert packet.calculation_trace.answer_source == "mna_solver"
    assert packet.calculation_trace.llm_used_for_numerical_answer is False


def test_gemini_schema_rejects_injected_final_numerical_answers():
    payload = {
        "id": "gemini_voltage_divider",
        "title": "Gemini Voltage Divider Parse",
        "analysis_type": "dc_operating_point",
        "topology_id": "voltage_divider",
        "ground_node": "0",
        "nodes": ["0", "n1", "n2"],
        "components": [
            {
                "id": "V1",
                "type": "voltage_source",
                "nodes": ["n1", "0"],
                "value": 10.0,
                "unit": "V",
            },
            {
                "id": "R1",
                "type": "resistor",
                "nodes": ["n1", "n2"],
                "value": 2000.0,
                "unit": "ohm",
            },
            {
                "id": "R2",
                "type": "resistor",
                "nodes": ["n2", "0"],
                "value": 3000.0,
                "unit": "ohm",
            },
        ],
        "goals": [
            {
                "id": "voltage_across_R2",
                "quantity": "component_voltage",
                "target": "R2",
                "reference": {"positive_node": "n2", "negative_node": "0"},
            }
        ],
        "assumptions": [],
        "ambiguities": [],
        "unsupported_features": [],
        "final_answer": {"voltage_across_R2": "999 V"},
    }

    with pytest.raises(ValidationError):
        GeminiCircuitProblem.model_validate(payload)


def test_mocked_gemini_parse_marks_parser_used_as_gemini(monkeypatch):
    import app.services.parser_service as parser_service

    parsed = GeminiCircuitProblem(
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
            ),
            GeminiGoal(
                id="circuit_current",
                quantity="component_current",
                target="R1",
                reference={"from_node": "n1", "to_node": "n2"},
            ),
        ],
        assumptions=["Voltage source positive terminal is node n1."],
        nonblocking_ambiguities=[
            "A disconnected measurement annotation was outside the requested calculation scope."
        ],
        ambiguities=[],
        unsupported_features=[],
    )

    monkeypatch.setattr(
        parser_service,
        "parse_with_gemini",
        lambda _problem_text, **_kwargs: CircuitProblem.model_validate(parsed.model_dump()),
    )

    result = parser_service.parse_problem("mock parse request", mode="gemini")

    assert result.parser_used == "gemini"
    assert result.circuit.id == "gemini_voltage_divider"
    assert result.circuit.nonblocking_ambiguities == [
        "A disconnected measurement annotation was outside the requested calculation scope."
    ]


def test_full_pipeline_with_mocked_gemini_uses_mna_for_answers(monkeypatch):
    import app.services.parser_service as parser_service

    circuit = CircuitProblem.model_validate(
        GeminiCircuitProblem(
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
                ),
                GeminiGoal(
                    id="circuit_current",
                    quantity="component_current",
                    target="R1",
                    reference={"from_node": "n1", "to_node": "n2"},
                ),
            ],
            assumptions=[],
            ambiguities=[],
            unsupported_features=[],
        ).model_dump()
    )

    monkeypatch.setattr(parser_service, "parse_with_gemini", lambda _problem_text, **_kwargs: circuit)

    response = TestClient(app).post(
        "/full_pipeline",
        json={"problem_text": "mock Gemini problem", "mode": "gemini_strict"},
    )
    payload = response.json()
    packet = payload["solution_packet"]

    assert response.status_code == 200
    assert payload["parser_used"] == "gemini"
    assert payload["debug_trace"]["enabled"] is True
    assert any(event["label"] == "solve_circuit_complete" for event in payload["debug_trace"]["events"])
    assert packet["verification_badge"]["label"] == "PASS"
    assert packet["calculation_trace"]["parser_used"] == "gemini"
    assert packet["calculation_trace"]["answer_source"] == "mna_solver"
    assert packet["calculation_trace"]["llm_used_for_numerical_answer"] is False
    assert packet["requested_answers"]["voltage_across_R2"]["value"] == pytest.approx(4.0)
    assert packet["requested_answers"]["circuit_current"]["value"] == pytest.approx(0.001)
