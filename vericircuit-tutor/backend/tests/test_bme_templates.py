import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.bme_templates import BME_TEMPLATE_FACTORIES, get_bme_demo_examples
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


client = TestClient(app)


def test_examples_endpoint_returns_bme_metadata():
    response = client.get("/examples")

    assert response.status_code == 200
    examples = response.json()
    anti_aliasing = next(example for example in examples if example["id"] == "bme_anti_aliasing_low_pass")
    assert anti_aliasing["biomedical_context"]
    assert anti_aliasing["what_students_should_learn"]
    assert anti_aliasing["typical_signal_range"]
    assert anti_aliasing["safety_note"]
    assert anti_aliasing["noise_sources"]
    assert anti_aliasing["real_world_nonidealities"]
    assert anti_aliasing["recommended_next_block"]


def test_bme_demo_templates_parse_and_solve():
    for example in get_bme_demo_examples():
        parsed = parse_problem(example["problem_text"], mode="demo")
        packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)

        assert parsed.circuit.id == example["id"]
        assert parsed.circuit.bme_metadata is not None
        assert example["biomedical_context"]
        assert example["signal_chain_role"]
        assert example["what_students_should_learn"]
        assert example["common_lab_mistakes"]
        assert packet.status == "solved"
        assert packet.verification_badge.label == "PASS"
        assert packet.bme_metadata is not None


def test_bme_templates_are_supported_circuit_ir():
    for template_id, factory in BME_TEMPLATE_FACTORIES.items():
        template = factory()
        packet = solve_circuit(template.circuit_problem)

        assert template.circuit_problem.id == template_id
        assert template.circuit_problem.bme_metadata is not None
        assert template.biomedical_context
        assert template.signal_chain_role
        assert template.assumptions
        assert template.what_students_should_learn
        assert template.common_lab_mistakes
        assert template.typical_signal_range
        assert template.safety_note
        assert template.noise_sources
        assert template.real_world_nonidealities
        assert template.recommended_next_block
        assert packet.status == "solved", template_id
        assert packet.verification_badge.label == "PASS", template_id
        assert packet.bme_metadata == template.circuit_problem.bme_metadata
        assert packet.bme_metadata.typical_signal_range
        assert packet.bme_metadata.safety_note
        if template_id in {
            "bme_ecg_front_end",
            "bme_photodiode_tia",
            "bme_instrumentation_amplifier",
        }:
            assert packet.bme_metadata.nominal_supply_rails_v == {
                "negative": 0.0,
                "positive": 3.3,
            }


def test_bme_ecg_front_end_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem)

    assert packet.requested_answers["ecg_front_end_output"].value == pytest.approx(0.01)


def test_bme_photodiode_tia_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem)

    assert packet.requested_answers["tia_output"].value == pytest.approx(10.0)
    assert packet.requested_answers["photodiode_current"].value == pytest.approx(10e-6)


def test_bme_instrumentation_amplifier_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_instrumentation_amplifier"]().circuit_problem)

    assert packet.requested_answers["instrumentation_amp_output"].value == pytest.approx(0.011)


def test_bme_emg_and_anti_aliasing_templates_return_phasors():
    emg_packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_emg_band_pass_chain"]().circuit_problem)
    anti_alias_packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem)

    assert emg_packet.ac_requested_answers["emg_band_pass_output"].magnitude == pytest.approx(
        0.8829789928743454
    )
    assert anti_alias_packet.ac_requested_answers["anti_aliasing_output"].magnitude == pytest.approx(
        0.44756213587647853
    )
    assert emg_packet.tutor_observations
    assert anti_alias_packet.tutor_observations
