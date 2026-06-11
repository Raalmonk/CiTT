import pytest

from app.services.bme_templates import BME_TEMPLATE_FACTORIES, get_bme_demo_examples
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


def test_bme_demo_templates_parse_and_solve():
    for example in get_bme_demo_examples():
        parsed = parse_problem(example["problem_text"], mode="demo")
        packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)

        assert parsed.circuit.id == example["id"]
        assert packet.status == "solved"
        assert packet.verification_badge.label == "PASS"


def test_bme_templates_are_supported_circuit_ir():
    for template_id, factory in BME_TEMPLATE_FACTORIES.items():
        packet = solve_circuit(factory())

        assert packet.status == "solved", template_id
        assert packet.verification_badge.label == "PASS", template_id


def test_bme_ecg_front_end_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]())

    assert packet.requested_answers["ecg_front_end_output"].value == pytest.approx(0.01)


def test_bme_photodiode_tia_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]())

    assert packet.requested_answers["tia_output"].value == pytest.approx(10.0)
    assert packet.requested_answers["photodiode_current"].value == pytest.approx(10e-6)


def test_bme_instrumentation_amplifier_gain_is_stable():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_instrumentation_amplifier"]())

    assert packet.requested_answers["instrumentation_amp_output"].value == pytest.approx(0.011)


def test_bme_emg_and_anti_aliasing_templates_return_phasors():
    emg_packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_emg_band_pass_chain"]())
    anti_alias_packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]())

    assert emg_packet.ac_requested_answers["emg_band_pass_output"].magnitude == pytest.approx(
        0.8829789928743454
    )
    assert anti_alias_packet.ac_requested_answers["anti_aliasing_output"].magnitude == pytest.approx(
        0.44756213587647853
    )
