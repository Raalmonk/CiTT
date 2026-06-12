from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.explainer import explain_solution
from app.services.pipeline import solve_circuit


def test_explainer_teaches_bme_low_pass_from_packet_context():
    template = BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]()
    packet = solve_circuit(template.circuit_problem)

    explanation = explain_solution(packet)

    assert "low-pass filter" in explanation
    assert "ADC" in explanation
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
