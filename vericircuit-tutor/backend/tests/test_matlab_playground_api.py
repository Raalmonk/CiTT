from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_matlab_playground_manifest_returns_four_tabs_and_included_labs():
    response = client.get("/matlab_playground/manifest")
    payload = response.json()

    assert response.status_code == 200
    assert payload["tabs"] == ["overview", "teach", "probe", "lab_delta"]
    lab_ids = {lab["id"] for lab in payload["labs"]}
    assert {"rc_antialias_adc", "instrumentation_amplifier_feedback"} <= lab_ids
    assert "graphical tutor layer" in payload["positioning"].lower()


def test_matlab_playground_lab_endpoint_serializes_supported_lab():
    response = client.get("/matlab_playground/labs/rc_antialias_adc")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == "rc_antialias_adc"
    assert payload["default_parameters"]["fs_hz"] == 500
    assert "Simscape" in payload["optional_products"]


def test_matlab_playground_artifacts_endpoint_returns_requested_kinds():
    response = client.post(
        "/matlab_playground/labs/rc_antialias_adc/artifacts",
        json={"kinds": ["matlab_script", "simscape_script", "popup_app_script"]},
    )
    payload = response.json()

    assert response.status_code == 200
    assert [artifact["kind"] for artifact in payload] == [
        "matlab_script",
        "simscape_script",
        "popup_app_script",
    ]
    assert any(artifact["filename"] == "citt.m" for artifact in payload)


def test_matlab_playground_focus_and_probe_endpoints_serialize():
    focus_response = client.get("/matlab_playground/labs/rc_antialias_adc/focus_map")
    probe_response = client.get("/matlab_playground/labs/rc_antialias_adc/probe_plans")

    assert focus_response.status_code == 200
    assert probe_response.status_code == 200
    focus_ids = {entry["id"] for entry in focus_response.json()}
    probe_ids = {probe["id"] for probe in probe_response.json()}
    assert {"rc_filter", "capacitor_output_node", "sampling_stage", "output_signal"} <= focus_ids
    assert {"input_signal_probe", "filter_output_voltage_probe", "sampled_output_probe"} <= probe_ids


def test_matlab_playground_lab_delta_endpoint_detects_ratio_issue():
    response = client.post(
        "/matlab_playground/labs/rc_antialias_adc/lab_delta",
        json={
            "lab_id": "rc_antialias_adc",
            "hand_values": {"fc_hz": 40},
            "simulation_values": {"fc_hz": 40},
            "measured_values": {"fc_hz": 251.327412},
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["rows"]
    assert any(cause["id"] == "rad_s_vs_hz" for cause in payload["likely_causes"])
    assert payload["recommended_probe"]


def test_matlab_playground_unknown_lab_returns_404():
    response = client.get("/matlab_playground/labs/not_a_lab")

    assert response.status_code == 404
