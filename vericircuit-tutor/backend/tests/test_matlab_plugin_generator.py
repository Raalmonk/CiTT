import json

from app.models.matlab_plugin import FocusMapEntry, HighlightTarget, MatlabArtifactRequest
from app.services.matlab_plugin_generator import (
    INSTRUMENTATION_AMP_LAB_ID,
    RC_ANTIALIAS_LAB_ID,
    build_offline_bundle,
    build_matlab_plugin_manifest,
    generate_artifacts,
    get_adapter_plan,
    get_focus_map,
    get_lab_plan,
    get_probe_plan,
    guided_steps_to_focus_map,
)
from app.services.demo_parser import voltage_divider_problem
from app.services.pipeline import solve_circuit


def test_manifest_includes_four_tabs_and_rc_lab():
    manifest = build_matlab_plugin_manifest()

    assert manifest.tabs == ["overview", "teach", "probe", "lab_delta"]
    assert any(lab.id == RC_ANTIALIAS_LAB_ID for lab in manifest.labs)
    assert "MATLAB" in manifest.title
    assert "without MATLAB installed" in manifest.ci_boundary
    assert "LLM prose is not the numerical authority" in manifest.source_of_truth_rule
    assert manifest.default_deployment_mode == "offline_toolbox"
    assert manifest.local_server_required is False


def test_rc_artifacts_include_matlab_script_and_required_text():
    artifacts = generate_artifacts(RC_ANTIALIAS_LAB_ID)
    script = next(artifact for artifact in artifacts if artifact.kind == "matlab_script")

    assert script.filename.endswith(".m")
    assert script.requires_matlab_runtime is False
    for expected in [
        "fs",
        "target_fc",
        "R",
        "C",
        "1/(2*pi*R*C)",
        "nyquist",
        "hand_fc_hz",
        "simulated_summary",
        "citt_results",
        "% CiTT Overview tab",
        "% CiTT Teach tab",
        "% CiTT Probe tab",
        "% CiTT Lab Delta tab",
        "% Future Simulink highlight: input_path",
        "% Future Simulink highlight: rc_filter",
        "% Future Simulink highlight: sampling_stage",
        "% Future Simulink highlight: output_signal",
    ]:
        assert expected in script.content


def test_focus_map_includes_rc_targets_and_serializes_to_json():
    focus_map = get_focus_map(RC_ANTIALIAS_LAB_ID)
    focus_ids = {entry.id for entry in focus_map}

    assert {
        "input_path",
        "rc_filter",
        "sampling_stage",
        "output_signal",
        "lab_delta_measurement_point",
    } <= focus_ids
    assert all(entry.reason for entry in focus_map)
    assert all(entry.target.id for entry in focus_map)

    encoded = json.loads(focus_map[0].model_dump_json())
    assert encoded["target"]["id"] == focus_map[0].target.id


def test_focus_map_schema_represents_feedback_loop():
    entry = FocusMapEntry(
        id="feedback_loop",
        tab="teach",
        title="Feedback loop",
        teaching_step_id="feedback_loop",
        target=HighlightTarget(
            id="feedback_loop",
            label="Feedback loop",
            target_type="conceptual_path",
            target_path="op_amp_output->feedback_resistor->inverting_input",
            simulink_path="instrumentation_amp/Feedback Loop",
        ),
        reason="Highlight the feedback loop in a drawn circuit or future Simulink model.",
        surfaces=["web_svg", "simulink"],
        current_svg_components=["feedback_resistor"],
        future_simulink_actions=["Call hilite_system on the mapped feedback path."],
    )

    payload = json.loads(entry.model_dump_json())
    assert payload["id"] == "feedback_loop"
    assert "simulink" in payload["surfaces"]


def test_instrumentation_amp_stub_includes_feedback_loop_targets():
    focus_map = get_focus_map(INSTRUMENTATION_AMP_LAB_ID)
    focus_ids = {entry.id for entry in focus_map}

    assert {
        "feedback_loop",
        "inverting_input",
        "noninverting_input",
        "op_amp_output",
        "feedback_resistor",
    } <= focus_ids


def test_probe_plan_includes_filter_output_measurement_point():
    probes = get_probe_plan(RC_ANTIALIAS_LAB_ID)
    combined = " ".join(
        " ".join(
            [
                probe.title,
                probe.student_goal,
                probe.target.label,
                probe.measurement_explanation,
            ]
        )
        for probe in probes
    ).lower()

    assert "filter output" in combined or "rc output" in combined
    assert any(probe.quantity == "voltage" and probe.unit == "V" for probe in probes)


def test_generated_json_artifacts_are_parseable():
    artifacts = generate_artifacts(RC_ANTIALIAS_LAB_ID)
    json_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.kind in {"focus_map_json", "probe_plan_json", "app_designer_plan", "toolbox_manifest"}
    ]

    assert json_artifacts
    for artifact in json_artifacts:
        parsed = json.loads(artifact.content)
        assert parsed


def test_artifact_request_flags_can_hide_optional_plans():
    artifacts = generate_artifacts(
        RC_ANTIALIAS_LAB_ID,
        MatlabArtifactRequest(
            include_focus_map=False,
            include_probe_plan=False,
            include_app_designer_plan=False,
        ),
    )
    kinds = {artifact.kind for artifact in artifacts}

    assert "matlab_script" in kinds
    assert "simulink_build_script" in kinds
    assert "focus_map_json" not in kinds
    assert "probe_plan_json" not in kinds
    assert "app_designer_plan" not in kinds


def test_existing_guided_steps_bridge_to_matlab_focus_map():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit)

    focus_map = guided_steps_to_focus_map(packet.guided_steps, lab_id="voltage_divider")

    assert len(focus_map) == len(packet.guided_steps)
    assert all("web_svg" in entry.surfaces for entry in focus_map)
    assert all("simulink" in entry.surfaces for entry in focus_map)
    assert any(entry.current_svg_components for entry in focus_map)
    assert all(entry.future_simulink_actions for entry in focus_map)


def test_lab_plan_packages_four_tab_contract_without_matlab_runtime():
    plan = get_lab_plan(RC_ANTIALIAS_LAB_ID)

    assert plan.lab.tabs == ["overview", "teach", "probe", "lab_delta"]
    assert plan.overview["title"] == "RC anti-aliasing before ADC"
    assert plan.teach_steps
    assert plan.focus_map
    assert plan.probe_plan
    assert plan.lab_delta_seed_request.hand_values
    assert plan.adapter_plan.mode == "dry_run_contract"
    assert plan.adapter_plan.launch_command == "citt"


def test_adapter_plan_marks_future_runtime_actions_and_refusal_rules():
    plan = get_adapter_plan(RC_ANTIALIAS_LAB_ID)
    action_by_id = {action.id: action for action in plan.agent_actions}

    assert action_by_id["highlight_focus"].requires_matlab_runtime is True
    assert action_by_id["insert_probe"].requires_matlab_runtime is True
    assert action_by_id["run_simulation"].requires_matlab_runtime is True
    assert action_by_id["compare_lab_delta"].requires_matlab_runtime is False
    assert any("Do not claim" in rule for rule in plan.refusal_rules)
    assert any("JSON serialization" in check for check in plan.ci_validation)


def test_offline_bundle_contains_agent_contract_and_parseable_json():
    bundle = build_offline_bundle(RC_ANTIALIAS_LAB_ID)
    payload = json.loads(bundle.model_dump_json())
    file_by_path = {file.path: file for file in bundle.files}

    assert payload["requires_matlab_runtime"] is False
    assert payload["manifest"]["local_server_required"] is False
    assert payload["manifest"]["default_deployment_mode"] == "offline_toolbox"
    assert payload["manifest"]["plugin_id"] == "citt_matlab_popup_tutor"
    assert payload["lab_plan"]["adapter_plan"]["mode"] == "dry_run_contract"
    assert payload["artifacts"]
    assert "citt.m" in payload["file_tree"]
    assert "+citt/citt.m" in payload["file_tree"]
    assert "+citt/loadOfflineBundle.m" in payload["file_tree"]
    assert "+citt/openPopup.m" in payload["file_tree"]
    assert "function varargout = citt" in file_by_path["citt.m"].content
    assert "citt.openPopup" in file_by_path["citt.m"].content
    assert "function varargout = citt" in file_by_path["+citt/citt.m"].content
    assert "jsondecode" in file_by_path["+citt/loadOfflineBundle.m"].content
    assert "uifigure" in file_by_path["+citt/openPopup.m"].content
    assert "uitabgroup" in file_by_path["+citt/openPopup.m"].content
    assert "Lab Delta" in file_by_path["+citt/openPopup.m"].content
    assert "local FastAPI server is optional" in file_by_path["docs/offline_first.md"].content
    assert payload["lab_delta_example"]["likely_causes"]
