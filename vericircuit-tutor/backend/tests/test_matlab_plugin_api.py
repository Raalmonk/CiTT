from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_matlab_plugin_manifest_endpoint():
    response = client.get("/matlab_plugin/manifest")
    payload = response.json()

    assert response.status_code == 200
    assert payload["tabs"] == ["overview", "teach", "probe", "lab_delta"]
    assert any(lab["id"] == "rc_antialias_adc" for lab in payload["labs"])


def test_matlab_plugin_labs_endpoint_lists_rc_lab():
    response = client.get("/matlab_plugin/labs")
    payload = response.json()

    assert response.status_code == 200
    assert any(lab["id"] == "rc_antialias_adc" for lab in payload)
    assert any(lab["id"] == "instrumentation_amplifier_intro" for lab in payload)


def test_matlab_plugin_artifact_endpoint_returns_matlab_script():
    response = client.post(
        "/matlab_plugin/labs/rc_antialias_adc/artifact",
        json={"kinds": ["matlab_script"]},
    )
    payload = response.json()

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["kind"] == "matlab_script"
    assert payload[0]["filename"].endswith(".m")
    assert "citt_results" in payload[0]["content"]
    assert "1/(2*pi*R*C)" in payload[0]["content"]


def test_matlab_plugin_lab_plan_endpoint():
    response = client.get("/matlab_plugin/labs/rc_antialias_adc/plan")
    payload = response.json()

    assert response.status_code == 200
    assert payload["lab"]["tabs"] == ["overview", "teach", "probe", "lab_delta"]
    assert payload["teach_steps"]
    assert payload["focus_map"]
    assert payload["probe_plan"]
    assert payload["adapter_plan"]["mode"] == "dry_run_contract"


def test_matlab_plugin_adapter_plan_endpoint():
    response = client.get("/matlab_plugin/labs/rc_antialias_adc/adapter_plan")
    payload = response.json()

    assert response.status_code == 200
    assert payload["launch_command"] == "citt"
    assert any(action["id"] == "refuse_unsupported" for action in payload["agent_actions"])
    assert any("Do not claim" in rule for rule in payload["refusal_rules"])


def test_matlab_plugin_offline_bundle_endpoint():
    response = client.post(
        "/matlab_plugin/labs/rc_antialias_adc/offline_bundle",
        json={"kinds": ["matlab_script", "toolbox_manifest"]},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["requires_matlab_runtime"] is False
    assert payload["bundle_id"] == "citt_rc_antialias_adc_offline_bundle_v1"
    assert payload["artifacts"]
    assert "citt.m" in payload["file_tree"]
    assert "+citt/citt.m" in payload["file_tree"]
    assert "+citt/openPopup.m" in payload["file_tree"]
    assert any(file["path"] == "citt.m" for file in payload["files"])
    assert any(file["path"] == "+citt/citt.m" for file in payload["files"])
    assert any(file["path"] == "+citt/openPopup.m" for file in payload["files"])
    assert payload["manifest"]["local_server_required"] is False


def test_matlab_plugin_focus_map_endpoint():
    response = client.get("/matlab_plugin/labs/rc_antialias_adc/focus_map")
    payload = response.json()

    assert response.status_code == 200
    focus_ids = {entry["id"] for entry in payload}
    assert {"input_path", "rc_filter", "sampling_stage", "output_signal"} <= focus_ids


def test_matlab_plugin_probe_plan_endpoint():
    response = client.get("/matlab_plugin/labs/rc_antialias_adc/probe_plan")
    payload = response.json()

    assert response.status_code == 200
    assert any("RC output" in probe["title"] for probe in payload)
    assert any(probe["quantity"] == "voltage" for probe in payload)


def test_matlab_plugin_lab_delta_endpoint():
    response = client.post(
        "/matlab_plugin/labs/rc_antialias_adc/lab_delta",
        json={
            "hand_values": {"fc_hz": 40.0},
            "simulation_values": {"fc_hz": 40.0},
            "measured_values": {"fc_hz": 251.327412},
            "value_units": {"fc_hz": "Hz"},
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["comparison_rows"]
    assert any(cause["id"] == "rad_s_vs_hz" for cause in payload["likely_causes"])
    assert payload["next_probe_suggestion"]
    assert payload["reflection_question"]


def test_matlab_plugin_lab_delta_upload_endpoint_accepts_csv():
    response = client.post(
        "/matlab_plugin/labs/rc_antialias_adc/lab_delta/parse_upload",
        json={
            "content": (
                "source,key,value,unit\n"
                "hand,fc_hz,40,Hz\n"
                "simulation,fc_hz,40.1,Hz\n"
                "measured,fc_hz,251.327412,Hz\n"
            )
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["parsed_request"]["hand_values"]["fc_hz"] == 40.0
    assert any(cause["id"] == "rad_s_vs_hz" for cause in payload["lab_delta_response"]["likely_causes"])


def test_matlab_plugin_lab_delta_upload_endpoint_rejects_bad_csv():
    response = client.post(
        "/matlab_plugin/labs/rc_antialias_adc/lab_delta/parse_upload",
        json={"content": "source,value\nhand,40\n"},
    )

    assert response.status_code == 400


def test_matlab_plugin_unknown_lab_returns_404():
    response = client.get("/matlab_plugin/labs/missing_lab/focus_map")

    assert response.status_code == 404
