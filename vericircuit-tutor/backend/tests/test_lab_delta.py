import json
import math

from app.models.matlab_plugin import LabDeltaRequest, MatlabLabDeltaUploadRequest
from app.services.matlab_plugin_generator import (
    RC_ANTIALIAS_LAB_ID,
    compare_lab_delta,
    parse_lab_delta_upload,
)


def _cause_ids(response):
    return {cause.id for cause in response.likely_causes}


def test_lab_delta_detects_rad_s_vs_hz_confusion():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            hand_values={"fc_hz": 40.0},
            simulation_values={"fc_hz": 40.1},
            measured_values={"fc_hz": 40.0 * 2 * math.pi},
            value_units={"fc_hz": "Hz"},
        ),
    )

    assert "rad_s_vs_hz" in _cause_ids(response)
    assert any("rad/s vs Hz" in cause.title for cause in response.likely_causes)
    assert response.comparison_rows
    assert response.next_probe_suggestion
    assert response.next_check
    assert response.reflection_question


def test_lab_delta_detects_unit_prefix_mistake_near_1000x():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            hand_values={"capacitor_f": 100e-9},
            simulation_values={"capacitor_f": 100e-9},
            measured_values={"capacitor_f": 100e-6},
            value_units={"capacitor_f": "F"},
        ),
    )

    assert "unit_prefix_mistake" in _cause_ids(response)
    assert any("nF/uF" in cause.explanation for cause in response.likely_causes)


def test_lab_delta_suggests_tolerance_or_loading_for_moderate_cutoff_delta():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            hand_values={"cutoff_hz": 40.0},
            simulation_values={"cutoff_hz": 40.0},
            measured_values={"cutoff_hz": 45.0},
            value_units={"cutoff_hz": "Hz"},
        ),
    )

    assert "rc_tolerance_or_loading" in _cause_ids(response)


def test_lab_delta_suggests_sampling_issue_from_notes():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            hand_values={"output_rms_v": 0.5},
            simulation_values={"output_rms_v": 0.49},
            measured_values={"output_rms_v": 0.42},
            value_units={"output_rms_v": "V"},
            notes="The sampled waveform looks aliased near Nyquist.",
        ),
    )

    assert "nyquist_or_adc_sampling" in _cause_ids(response)
    assert "sampled_output" in response.next_probe_suggestion


def test_lab_delta_response_serializes_to_json():
    response = compare_lab_delta(
        RC_ANTIALIAS_LAB_ID,
        LabDeltaRequest(
            hand_values={"fc_hz": 40.0},
            simulation_values={"fc_hz": 40.0},
            measured_values={"fc_hz": 41.0},
            value_units={"fc_hz": "Hz"},
        ),
    )

    payload = json.loads(response.model_dump_json())
    assert payload["comparison_rows"]
    assert payload["likely_causes"]
    assert payload["next_probe_suggestion"]
    assert payload["reflection_question"]


def test_lab_delta_upload_parser_accepts_csv_rows():
    upload = parse_lab_delta_upload(
        RC_ANTIALIAS_LAB_ID,
        MatlabLabDeltaUploadRequest(
            content=(
                "source,key,value,unit,note\n"
                "hand,fc_hz,40,Hz,\n"
                "simulation,fc_hz,40.1,Hz,\n"
                "measured,fc_hz,251.327412,Hz,reported from scope cursor\n"
            )
        ),
    )

    assert upload.parsed_request.hand_values["fc_hz"] == 40.0
    assert upload.parsed_request.measured_values["fc_hz"] == 251.327412
    assert upload.parsed_request.value_units["fc_hz"] == "Hz"
    assert "rad_s_vs_hz" in _cause_ids(upload.lab_delta_response)


def test_lab_delta_upload_parser_accepts_json_request():
    upload = parse_lab_delta_upload(
        RC_ANTIALIAS_LAB_ID,
        MatlabLabDeltaUploadRequest(
            format="json",
            content=json.dumps(
                {
                    "hand_values": {"capacitor_f": 100e-9},
                    "simulation_values": {"capacitor_f": 100e-9},
                    "measured_values": {"capacitor_f": 100e-6},
                    "value_units": {"capacitor_f": "F"},
                }
            ),
        ),
    )

    assert "unit_prefix_mistake" in _cause_ids(upload.lab_delta_response)
