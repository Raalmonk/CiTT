import math

from app.models.matlab_playground import LabDeltaRequest
from app.services.matlab_playground import RC_ANTIALIAS_LAB_ID, compare_lab_delta


def _cause_ids(response):
    return {cause.id for cause in response.likely_causes}


def test_playground_lab_delta_detects_2pi_ratio_issue():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            lab_id=RC_ANTIALIAS_LAB_ID,
            hand_values={"fc_hz": 40.0},
            simulation_values={"fc_hz": 40.0},
            measured_values={"fc_hz": 40.0 * 2.0 * math.pi},
        ),
    )

    assert "rad_s_vs_hz" in _cause_ids(response)
    assert "missing_2pi" in _cause_ids(response)
    assert response.rows[0].absolute_error is not None


def test_playground_lab_delta_detects_1000x_prefix_issue():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            lab_id=RC_ANTIALIAS_LAB_ID,
            hand_values={"capacitor_f": 100e-9},
            simulation_values={"capacitor_f": 100e-9},
            measured_values={"capacitor_f": 100e-6},
        ),
    )

    assert "capacitor_prefix_mistake" in _cause_ids(response)
    assert response.recommended_probe == "cutoff_attenuation_check"


def test_playground_lab_delta_detects_nyquist_issue():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            lab_id=RC_ANTIALIAS_LAB_ID,
            hand_values={"fs_hz": 90.0, "signal_frequency_hz": 60.0},
            simulation_values={"fs_hz": 90.0, "signal_frequency_hz": 60.0},
            measured_values={"output_rms_v": 0.3},
            notes="The sampled waveform looks aliased.",
        ),
    )

    assert "sampling_nyquist" in _cause_ids(response)
    assert response.recommended_probe == "sampled_output_probe"
