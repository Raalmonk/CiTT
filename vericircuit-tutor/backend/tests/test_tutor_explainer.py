from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.explainer import explain_solution
from app.services.pipeline import solve_circuit


def test_explainer_teaches_bme_low_pass_from_packet_context():
    template = BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]()
    packet = solve_circuit(template.circuit_problem)

    explanation = explain_solution(packet)

    assert "low-pass filter" in explanation
    assert "ADC" in explanation
    assert "Nyquist" in explanation
    assert "attenuation at Nyquist" in explanation
    assert "447.562 mV" in explanation
    assert "corner frequency" in explanation
    assert "verified Solution Packet" in explanation


def test_explainer_teaches_bme_emg_band_pass_context():
    template = BME_TEMPLATE_FACTORIES["bme_emg_band_pass_chain"]()
    packet = solve_circuit(template.circuit_problem)

    explanation = explain_solution(packet)

    assert "Surface EMG" in explanation
    assert "band-pass chain" in explanation
    assert "high-pass corner" in explanation
    assert "low-pass corner" in explanation


def test_explainer_warns_when_ideal_tia_exceeds_real_3v3_op_amp_swing():
    template = BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]()
    packet = solve_circuit(template.circuit_problem)

    explanation = explain_solution(packet)

    assert "ideal result for tia_output is 10 V" in explanation
    assert "template's nominal 0 V to 3.3 V op-amp rails" in explanation
    assert "usable output window is 0.1 V to 3.2 V" in explanation
    assert "would saturate" in explanation


def test_explainer_teaches_differential_vs_common_mode_for_ecg():
    template = BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]()
    packet = solve_circuit(template.circuit_problem)

    explanation = explain_solution(packet)

    assert "Differential-vs-common-mode" in explanation
    assert "desired input difference" in explanation
    assert "common-mode level" in explanation
    assert "real CMRR depends" in explanation
    assert "1% resistor-ratio mismatch" in explanation
    assert "common-mode-only input" in explanation
    assert "teaching estimate" in explanation
