import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.bme_templates import BME_TEMPLATE_FACTORIES, BME_TEMPLATE_TEXTS
from app.services.demo_parser import (
    BRIDGE_NETWORK_TEXT,
    VOLTAGE_DIVIDER_TEXT,
    bridge_network_problem,
    voltage_divider_problem,
)
from app.services.parser_service import ParseResult
from app.services.pipeline import solve_circuit


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_gemini_parse_for_coach_tests(monkeypatch):
    import app.services.reasoning_coach as reasoning_coach

    circuits_by_prompt = {
        VOLTAGE_DIVIDER_TEXT: voltage_divider_problem(),
        BRIDGE_NETWORK_TEXT: bridge_network_problem(),
        BME_TEMPLATE_TEXTS["bme_ecg_front_end"]: BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem,
        BME_TEMPLATE_TEXTS["bme_anti_aliasing_low_pass"]: BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem,
    }

    def parse_problem(problem_text: str, mode: str = "gemini") -> ParseResult:
        return ParseResult(
            circuit=circuits_by_prompt[problem_text],
            parser_used="gemini",
            warnings=[],
        )

    monkeypatch.setattr(reasoning_coach, "parse_problem", parse_problem)


def test_reasoning_coach_requires_student_commit_before_reveal():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": VOLTAGE_DIVIDER_TEXT,
            "reveal_solution": True,
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["verification_badge"]["label"] == "PASS"
    assert payload["local_check"]["status"] == "needs_commit"
    assert payload["nudge"]["hint_level"] == 0
    assert payload["nudge"]["answer_revealed"] is False
    assert payload["solution_packet"] is None
    assert payload["explanation"] is None


def test_reasoning_coach_gives_common_mode_nudge_without_answer_reveal():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": BME_TEMPLATE_TEXTS["bme_ecg_front_end"],
            "requested_hint_level": 1,
            "student_commitment": {
                "attempt_text": "I think I should multiply the common-mode voltage by the gain.",
                "confidence_percent": 82,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["circuit_id"] == "bme_ecg_front_end"
    assert payload["solution_packet"] is None
    assert payload["nudge"]["answer_revealed"] is False
    assert payload["local_check"]["focus_issue"] == "common_mode_as_differential"
    assert payload["student_frame"]["likely_misconceptions"] == [
        "common_mode_as_differential"
    ]
    assert payload["nudge"]["representation_mode"] == "biomedical_context"
    assert "shared body" in payload["nudge"]["representation_prompt"]
    assert "Which one does the ideal instrumentation amplifier amplify?" in payload["nudge"]["question"]
    assert payload["metrics"]["confidence_calibration"].startswith("High confidence")
    assert payload["profile_update"]["recurring_misconceptions"][
        "common_mode_as_differential"
    ] == 1
    assert payload["adaptive_practice"]
    assert payload["adaptive_practice"][0]["target_misconception"] == "common_mode_as_differential"


def test_reasoning_coach_flags_divider_shortcut_on_bridge_network():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": BRIDGE_NETWORK_TEXT,
            "requested_hint_level": 2,
            "student_commitment": {
                "plan": "This is just a voltage divider, so I will use the divider formula.",
                "unknown": "n2 voltage",
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["local_check"]["focus_issue"] == "inappropriate_divider_shortcut"
    assert payload["local_check"]["blocks_next_step"] is True
    assert payload["solution_packet"] is None
    assert "coupling" in payload["nudge"]["message"].lower()
    assert "Identify the coupling branch" in payload["nudge"]["choices"]


def test_reasoning_coach_can_use_gemini_for_student_frame(monkeypatch):
    import app.services.reasoning_coach as reasoning_coach

    class FakeStudentFrameClient:
        def generate_json_text(self, *, prompt, schema_model):
            assert "Do not solve the circuit." in prompt
            return json.dumps(
                {
                    "suspected_method": "voltage_divider",
                    "confusion": "op amp role",
                    "likely_misconceptions": ["ideal_op_amp_input_current"],
                    "confidence": "low",
                    "evidence": ["freeform_student_language"],
                }
            )

    monkeypatch.setattr(
        reasoning_coach,
        "GeminiStructuredClient",
        lambda: FakeStudentFrameClient(),
    )

    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": VOLTAGE_DIVIDER_TEXT,
            "mode": "gemini",
            "student_commitment": {
                "attempt_text": "I think the op amp changes the divider because it draws input current.",
                "confidence_percent": 30,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["student_frame"]["source"] == "gemini"
    assert "ideal_op_amp_input_current" in payload["student_frame"]["likely_misconceptions"]
    assert payload["solution_packet"] is None
    assert payload["nudge"]["answer_revealed"] is False


def test_reasoning_coach_can_use_current_packet_without_reparsing():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit, parser_used="gemini_image")

    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": "Uploaded schematic image.",
            "parser_used": "gemini_image",
            "student_frame_mode": "heuristic",
            "circuit_ir": json.loads(circuit.model_dump_json()),
            "solution_packet": json.loads(packet.model_dump_json()),
            "student_commitment": {
                "attempt_text": "I think this is a divider, but I am not sure where to start.",
                "confidence_percent": 40,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["parser_used"] == "gemini_image"
    assert payload["circuit_id"] == circuit.id
    assert payload["verification_badge"]["label"] == "PASS"
    assert payload["solution_packet"] is None
    assert payload["nudge"]["answer_revealed"] is False
    assert payload["nudge"]["question"]


def test_reasoning_coach_uses_recurring_profile_for_personalized_feedback():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": VOLTAGE_DIVIDER_TEXT,
            "requested_hint_level": 1,
            "student_profile": {
                "strengths": ["recognizes voltage divider structure"],
                "recurring_misconceptions": {"sign_convention": 2},
                "hint_preference": "conceptual_nudges",
                "independence_level": "medium",
                "hint_budget_used": 2,
                "completed_attempts": 0,
            },
            "student_commitment": {
                "attempt_text": "I know it is a divider, but I am confused about the current direction sign.",
                "confidence_percent": 45,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["local_check"]["focus_issue"] == "sign_convention"
    assert payload["profile_update"]["recurring_misconceptions"]["sign_convention"] == 3
    assert payload["metrics"]["hint_budget_used"] == 3
    assert payload["metrics"]["independence_score"] == "medium"


def test_reasoning_coach_caps_hint_when_student_is_over_reliant():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": VOLTAGE_DIVIDER_TEXT,
            "requested_hint_level": 4,
            "student_profile": {
                "strengths": [],
                "recurring_misconceptions": {"sign_convention": 4},
                "hint_preference": "diagram",
                "independence_level": "low",
                "hint_budget_used": 9,
                "completed_attempts": 0,
            },
            "student_commitment": {
                "attempt_text": "I am stuck on current direction again.",
                "confidence_percent": 20,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["nudge"]["hint_level"] == 1
    assert payload["nudge"]["representation_mode"] == "diagram"
    assert "arrow" in payload["nudge"]["representation_prompt"].lower()
    assert payload["metrics"]["independence_score"] == "low"


def test_reasoning_coach_units_representation_and_nyquist_practice():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": BME_TEMPLATE_TEXTS["bme_anti_aliasing_low_pass"],
            "requested_hint_level": 2,
            "representation_mode": "units_magnitude",
            "student_commitment": {
                "attempt_text": "I think the cutoff should be above Nyquist so aliasing is avoided.",
                "confidence_percent": 78,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["local_check"]["focus_issue"] == "aliasing_nyquist_misread"
    assert payload["nudge"]["representation_mode"] == "units_magnitude"
    assert "frequency axis" in payload["nudge"]["representation_prompt"]
    assert [item["target_misconception"] for item in payload["adaptive_practice"]] == [
        "aliasing_nyquist_misread",
        "aliasing_nyquist_misread",
    ]


def test_reasoning_coach_builds_dynamic_diagnostic_graph_for_new_issue():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": VOLTAGE_DIVIDER_TEXT,
            "requested_hint_level": 2,
            "student_commitment": {
                "attempt_text": "The node voltage is absolute, so the ground reference does not matter.",
                "confidence_percent": 80,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["local_check"]["focus_issue"] == "reference_node_dependency"
    assert payload["student_frame"]["diagnostic_graph"]
    assert any(
        node["kind"] == "root_cause"
        for node in payload["student_frame"]["diagnostic_graph"]
    )
    assert payload["adaptive_practice"][0]["target_misconception"] == "reference_node_dependency"
    assert payload["profile_update"]["knowledge_state"]["reference_node_dependency"]["opportunities"] == 1
    assert payload["profile_update"]["knowledge_state"]["reference_node_dependency"]["mastery"] < 0.5


def test_reasoning_coach_reveals_solution_only_at_level_five_after_commit():
    response = client.post(
        "/reasoning_coach",
        json={
            "problem_text": VOLTAGE_DIVIDER_TEXT,
            "requested_hint_level": 5,
            "student_commitment": {
                "plan": "I will use a divider after anchoring source and ground.",
                "unknown": "voltage across R2",
                "first_equation": "Vout = Vin * R2 / (R1 + R2)",
                "confidence_percent": 70,
            },
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["nudge"]["answer_revealed"] is True
    assert payload["local_check"]["status"] == "ready_for_reveal"
    assert payload["solution_packet"] is not None
    assert payload["explanation"]
    assert payload["solution_packet"]["requested_answers"]["voltage_across_R2"][
        "value"
    ] == pytest.approx(6.0)
    assert payload["solution_packet"]["calculation_trace"]["answer_source"] == "mna_solver"
    assert payload["reflection"]["today_i_learned"]


def test_instructor_dashboard_summarizes_misconception_map():
    response = client.post(
        "/instructor_dashboard",
        json={
            "student_profiles": [
                {
                    "strengths": [],
                    "recurring_misconceptions": {
                        "sign_convention": 3,
                        "unit_prefix": 1,
                    },
                    "hint_preference": "diagram",
                    "independence_level": "medium",
                    "hint_budget_used": 3,
                    "completed_attempts": 1,
                },
                {
                    "strengths": [],
                    "recurring_misconceptions": {"sign_convention": 2},
                    "hint_preference": "conceptual_nudges",
                    "independence_level": "low",
                    "hint_budget_used": 8,
                    "completed_attempts": 0,
                },
            ]
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["student_count"] == 2
    assert payload["cohort_independence"] == {"high": 0, "medium": 1, "low": 1}
    assert payload["misconception_summary"][0]["misconception"] == "sign_convention"
    assert payload["misconception_summary"][0]["affected_students"] == 2
    assert payload["misconception_summary"][0]["affected_percent"] == pytest.approx(100.0)
    assert "current arrows" in payload["misconception_summary"][0]["suggested_intervention"]
