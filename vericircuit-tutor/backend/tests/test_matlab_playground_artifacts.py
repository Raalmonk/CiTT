import json
from pathlib import Path

from app.services.matlab_playground import (
    INSTRUMENTATION_FEEDBACK_LAB_ID,
    RC_ANTIALIAS_LAB_ID,
    generate_artifacts,
    get_focus_map,
    get_probe_plans,
)


def _artifact(kind: str, lab_id: str = RC_ANTIALIAS_LAB_ID):
    return next(artifact for artifact in generate_artifacts(lab_id) if artifact.kind == kind)


def test_rc_matlab_artifact_contains_required_hand_check_and_signal_outputs():
    artifact = _artifact("matlab_script")

    for expected in [
        "fs = 500",
        "target_fc = 40",
        "R = 1/(2*pi*target_fc*C)",
        "C = 100e-9",
        "fc = 1/(2*pi*R*C)",
        "nyquist = fs/2",
        "citt_results",
        "citt_hand_fc_hz",
        "citt_nyquist_hz",
        "citt_input_signal",
        "citt_filtered_signal",
        "citt_sampled_signal",
    ]:
        assert expected in artifact.content


def test_rc_simscape_artifact_mentions_blocks_and_graceful_fallback():
    artifact = _artifact("simscape_script")
    lowered = artifact.content.lower()

    for expected in [
        "simscape",
        "simulink",
        "fallback",
        "resistor",
        "capacitor",
        "solver configuration",
        "electrical reference",
        "probe/logging comments",
    ]:
        assert expected in lowered
    assert "tryaddblock" in lowered


def test_focus_map_and_probe_plan_ids_match_demo_requirements():
    focus_ids = {entry.id for entry in get_focus_map(RC_ANTIALIAS_LAB_ID)}
    probe_labels = {probe.label.lower() for probe in get_probe_plans(RC_ANTIALIAS_LAB_ID)}

    assert {
        "overview_signal_flow",
        "input_path",
        "rc_filter",
        "capacitor_output_node",
        "sampling_stage",
        "output_signal",
        "lab_delta_measurement_point",
    } <= focus_ids
    assert any("input signal" in label for label in probe_labels)
    assert any("filter output" in label for label in probe_labels)
    assert any("sampled output" in label for label in probe_labels)


def test_instrumentation_focus_map_includes_feedback_loop_targets():
    focus_ids = {entry.id for entry in get_focus_map(INSTRUMENTATION_FEEDBACK_LAB_ID)}

    assert {
        "differential_input",
        "common_mode_input",
        "gain_setting_resistor",
        "feedback_loop",
        "op_amp_output",
        "output_probe",
    } <= focus_ids


def test_json_artifacts_are_parseable():
    for artifact in generate_artifacts(RC_ANTIALIAS_LAB_ID):
        if artifact.kind in {"focus_map", "probe_plan", "lab_delta_report"}:
            assert json.loads(artifact.content)


def test_matlab_highlight_helper_contains_function_and_required_ids():
    helper_path = Path(__file__).resolve().parents[2] / "matlab" / "+citt" / "highlightFocus.m"
    content = helper_path.read_text(encoding="utf-8")

    assert "function matchedEntry = highlightFocus" in content
    assert "hilite_system" in content
    assert "feedback_loop" in content
    assert "rc_filter" in content
