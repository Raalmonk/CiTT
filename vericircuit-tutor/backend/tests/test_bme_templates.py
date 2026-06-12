import math

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
    assert anti_aliasing["adc_sampling_frequency_hz"] == 4000.0
    assert anti_aliasing["adc_target_cutoff_hz"] == 500.0
    assert anti_aliasing["adc_resolution_bits"] == 12
    assert anti_aliasing["adc_full_scale_voltage_v"] == 3.3
    assert anti_aliasing["adc_input_impedance_ohm"] == 1_000_000.0
    assert anti_aliasing["noise_bandwidth_hz"] == 500.0


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
            assert packet.bme_metadata.supply_negative_v == 0.0
            assert packet.bme_metadata.supply_positive_v == 3.3
            assert packet.bme_metadata.output_swing_margin_v == 0.1


def test_bme_ecg_front_end_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem)

    assert packet.requested_answers["ecg_front_end_output"].value == pytest.approx(0.01)


def test_bme_photodiode_tia_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem)

    assert packet.requested_answers["tia_output"].value == pytest.approx(10.0)
    assert packet.requested_answers["photodiode_current"].value == pytest.approx(10e-6)


def test_bme_photodiode_tia_reports_noise_budget_starter():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem)
    observations = {observation.id: observation for observation in packet.tutor_observations}

    bandwidth_hz = 1000.0
    assert observations["noise_budget_bandwidth"].value == pytest.approx(bandwidth_hz)
    assert observations["thermal_noise_RF"].value == pytest.approx(
        math.sqrt(4.0 * 1.380649e-23 * 300.0 * 1_000_000.0 * bandwidth_hz)
    )
    assert observations["photodiode_shot_noise_IPD"].value == pytest.approx(
        math.sqrt(2.0 * 1.602176634e-19 * 10e-6 * bandwidth_hz)
    )
    assert observations["op_amp_input_referred_noise"].value == pytest.approx(
        15e-9 * math.sqrt(bandwidth_hz)
    )
    assert "starter estimates" in observations["noise_budget_boundary"].note


def test_bme_instrumentation_amplifier_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_instrumentation_amplifier"]().circuit_problem)

    assert packet.requested_answers["instrumentation_amp_output"].value == pytest.approx(0.011)


def test_bme_ecg_front_end_reports_cmrr_mismatch_what_if():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem)
    observations = {observation.id: observation for observation in packet.tutor_observations}

    assert observations["cmrr_mismatch_percent"].value == pytest.approx(1.0)
    assert observations["cmrr_common_mode_leakage_output"].value == pytest.approx(-0.009095454545455775)
    assert observations["cmrr_common_mode_leakage_gain"].value == pytest.approx(0.00909090909091032)
    assert observations["cmrr_mismatch_estimate_db"].value == pytest.approx(60.82785370316429)


def test_bme_instrumentation_amplifier_reports_cmrr_mismatch_what_if():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_instrumentation_amplifier"]().circuit_problem)
    observations = {observation.id: observation for observation in packet.tutor_observations}

    assert observations["cmrr_mismatch_percent"].value == pytest.approx(1.0)
    assert observations["cmrr_common_mode_leakage_output"].unit == "V"
    assert abs(observations["cmrr_common_mode_leakage_output"].value) > 0
    assert observations["cmrr_mismatch_estimate_db"].unit == "dB"


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
    anti_alias_observations = {
        observation.id: observation
        for observation in anti_alias_packet.tutor_observations
    }
    assert anti_alias_observations["adc_sampling_frequency"].value == pytest.approx(4000.0)
    assert anti_alias_observations["adc_nyquist_frequency"].value == pytest.approx(2000.0)
    assert anti_alias_observations["adc_attenuation_at_nyquist"].value == pytest.approx(
        -12.296527179496552
    )
    assert anti_alias_observations["adc_quantization_step"].value == pytest.approx(3.3 / 4096)
    assert anti_alias_observations["adc_quantization_noise_rms"].value == pytest.approx(
        (3.3 / 4096) / math.sqrt(12.0)
    )
    assert anti_alias_observations["adc_input_loading_ratio"].value == pytest.approx(0.318)
    assert "single-pole RC anti-aliasing" in anti_alias_observations["aliasing_warning"].note
    assert "switched-capacitor ADC input model" in anti_alias_observations["adc_input_loading_ratio"].note
    assert anti_alias_observations["thermal_noise_R1"].value == pytest.approx(
        math.sqrt(4.0 * 1.380649e-23 * 300.0 * 3180.0 * 500.0)
    )
