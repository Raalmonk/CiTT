from __future__ import annotations

import json
import math
import csv
from collections.abc import Iterable
from io import StringIO
from typing import Any

from app.models.matlab_plugin import (
    FocusMapEntry,
    HighlightTarget,
    LabDeltaCause,
    LabDeltaComparisonRow,
    LabDeltaRequest,
    LabDeltaResponse,
    MatlabLabDeltaUploadRequest,
    MatlabLabDeltaUploadResponse,
    MatlabAdapterPlan,
    MatlabAgentActionStep,
    MatlabArtifactKind,
    MatlabArtifactRequest,
    MatlabLabPlan,
    MatlabLabSummary,
    MatlabOfflineBundle,
    MatlabOfflineBundleFile,
    MatlabPluginArtifact,
    MatlabPluginManifest,
    MatlabTeachStep,
    ProbePlan,
)
from app.models.solution_packet import TutorStep


RC_ANTIALIAS_LAB_ID = "rc_antialias_adc"
INSTRUMENTATION_AMP_LAB_ID = "instrumentation_amplifier_intro"

PLUGIN_TABS = ["overview", "teach", "probe", "lab_delta"]


def build_matlab_plugin_manifest() -> MatlabPluginManifest:
    return MatlabPluginManifest(
        description=(
            "MATLAB-native popup tutor contract for BME circuits and "
            "signal-conditioning labs. The API returns generated artifacts, "
            "focus maps, probe plans, and lab-delta comparisons without requiring "
            "MATLAB in CI."
        ),
        tabs=PLUGIN_TABS,
        labs=available_labs(),
    )


def available_labs() -> list[MatlabLabSummary]:
    return [
        MatlabLabSummary(
            id=RC_ANTIALIAS_LAB_ID,
            title="RC anti-aliasing before ADC",
            objective=(
                "Connect the hand cutoff calculation to a Simulink-style filter "
                "and sampled waveform before an ADC."
            ),
            tabs=PLUGIN_TABS,
            inputs=[
                "ECG-like low-frequency signal",
                "60 Hz interference",
                "Sampling rate",
            ],
            outputs=[
                "Filtered RC output",
                "Sampled ADC input waveform",
                "Hand/simulation/lab cutoff comparison",
            ],
            key_parameters={
                "fs": "500 Hz",
                "target_fc": "40 Hz",
                "R": "39.7887358 kOhm",
                "C": "100 nF",
            },
            assumptions=[
                "The source and ADC input are ideal unless Lab Delta suggests otherwise.",
                "The RC stage is modeled as a first-order low-pass filter.",
                "The example waveform is educational and ECG-like, not patient data.",
            ],
            idealizations=[
                "No op-amp buffer loading is included in the initial artifact.",
                "Component tolerances are represented as Lab Delta causes, not random simulation.",
                "ADC quantization is summarized instead of modeled as a device datasheet.",
            ],
            bme_safety_boundary=(
                "This is a signal-conditioning teaching model, not biomedical safety "
                "verification or patient-connected design approval."
            ),
            generated_artifact_kinds=[
                "matlab_script",
                "simulink_build_script",
                "focus_map_json",
                "probe_plan_json",
                "app_designer_plan",
                "toolbox_manifest",
            ],
            evidence_to_collect=[
                "Calculated cutoff frequency",
                "Nyquist frequency",
                "Input and filtered waveforms",
                "Sampled output waveform",
                "Lab Delta comparison rows",
            ],
        ),
        MatlabLabSummary(
            id=INSTRUMENTATION_AMP_LAB_ID,
            title="Instrumentation amplifier intro",
            objective=(
                "Preview the future popup workflow for differential/common-mode "
                "reasoning and feedback-loop highlighting."
            ),
            tabs=PLUGIN_TABS,
            inputs=[
                "Differential sensor voltage",
                "Common-mode voltage",
                "Gain-setting resistor",
            ],
            outputs=[
                "Ideal differential output",
                "Common-mode teaching note",
                "Feedback-loop focus map",
            ],
            key_parameters={
                "v_diff": "1 mV",
                "v_common": "1 V",
                "gain": "1 + 2R/Rg",
            },
            assumptions=[
                "Ideal op-amps in the stub artifact.",
                "Matched resistor ratios for common-mode rejection.",
            ],
            idealizations=[
                "No finite CMRR or input bias simulation in the stub.",
                "No live Simulink execution yet.",
            ],
            bme_safety_boundary=(
                "Human-connected instrumentation requires isolation, leakage-current "
                "limits, and approved medical-safety design practices."
            ),
            generated_artifact_kinds=[
                "matlab_script",
                "focus_map_json",
                "probe_plan_json",
                "app_designer_plan",
                "toolbox_manifest",
            ],
            evidence_to_collect=[
                "Gain formula hand check",
                "Differential/common-mode explanation",
                "Feedback-loop highlight plan",
            ],
            status="stub",
        ),
    ]


def get_lab_summary(lab_id: str) -> MatlabLabSummary:
    for lab in available_labs():
        if lab.id == lab_id:
            return lab
    raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")


def generate_artifacts(
    lab_id: str,
    request: MatlabArtifactRequest | None = None,
) -> list[MatlabPluginArtifact]:
    request = request or MatlabArtifactRequest()
    requested_kinds = set(request.kinds or _default_artifact_kinds(lab_id))
    if not request.include_focus_map:
        requested_kinds.discard("focus_map_json")
    if not request.include_probe_plan:
        requested_kinds.discard("probe_plan_json")
    if not request.include_app_designer_plan:
        requested_kinds.discard("app_designer_plan")
    artifacts: list[MatlabPluginArtifact] = []

    if lab_id == RC_ANTIALIAS_LAB_ID:
        artifact_builders = {
            "matlab_script": _rc_matlab_script_artifact,
            "simulink_build_script": _rc_simulink_plan_artifact,
            "focus_map_json": _rc_focus_map_artifact,
            "probe_plan_json": _rc_probe_plan_artifact,
            "app_designer_plan": _app_designer_plan_artifact,
            "toolbox_manifest": _toolbox_manifest_artifact,
            "live_script_plan": _rc_live_script_plan_artifact,
        }
    elif lab_id == INSTRUMENTATION_AMP_LAB_ID:
        artifact_builders = {
            "matlab_script": _instrumentation_amp_script_artifact,
            "focus_map_json": _instrumentation_amp_focus_map_artifact,
            "probe_plan_json": _instrumentation_amp_probe_plan_artifact,
            "app_designer_plan": _app_designer_plan_artifact,
            "toolbox_manifest": _toolbox_manifest_artifact,
            "live_script_plan": _instrumentation_amp_live_script_plan_artifact,
        }
    else:
        raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")

    for kind in _ordered_artifact_kinds(requested_kinds):
        builder = artifact_builders.get(kind)
        if builder is not None:
            artifacts.append(builder(lab_id))
    return artifacts


def get_focus_map(lab_id: str) -> list[FocusMapEntry]:
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return _rc_focus_map()
    if lab_id == INSTRUMENTATION_AMP_LAB_ID:
        return _instrumentation_amp_focus_map()
    raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")


def get_probe_plan(lab_id: str) -> list[ProbePlan]:
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return _rc_probe_plan()
    if lab_id == INSTRUMENTATION_AMP_LAB_ID:
        return _instrumentation_amp_probe_plan()
    raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")


def get_lab_plan(lab_id: str) -> MatlabLabPlan:
    lab = get_lab_summary(lab_id)
    return MatlabLabPlan(
        lab=lab,
        overview=_overview_payload(lab),
        teach_steps=_teach_steps(lab_id),
        focus_map=get_focus_map(lab_id),
        probe_plan=get_probe_plan(lab_id),
        lab_delta_seed_request=_lab_delta_seed_request(lab_id),
        expected_artifact_kinds=lab.generated_artifact_kinds,
        adapter_plan=get_adapter_plan(lab_id),
    )


def get_adapter_plan(lab_id: str) -> MatlabAdapterPlan:
    get_lab_summary(lab_id)
    return MatlabAdapterPlan(
        lab_id=lab_id,
        required_matlab_products=[
            "MATLAB",
            "Simulink for future runtime execution",
            "Simscape Electrical for future sensor insertion templates",
        ],
        supported_now=[
            "Fetch and render the typed plugin manifest.",
            "Fetch generated MATLAB script text and dry-run Simulink build plans.",
            "Render four popup tabs from JSON without MATLAB execution.",
            "Map focus entries to current SVG targets or future Simulink paths.",
            "Render probe plans and Lab Delta comparison suggestions.",
        ],
        future_runtime_hooks=[
            "Launch MATLAB App Designer popup with command: citt.",
            "Call hilite_system for block, line, port, and annotation targets after a model exists.",
            "Insert signal logging or Simscape sensors from ProbePlan entries.",
            "Run MATLAB/Simulink simulations through an optional local adapter.",
            "Package +citt/, templates/, examples/, docs/, and app/ into a .mltbx toolbox.",
        ],
        agent_actions=[
            MatlabAgentActionStep(
                id="load_manifest",
                tab="overview",
                label="Load plugin manifest",
                action_kind="fetch_manifest",
                inputs=["GET /matlab_plugin/manifest"],
                expected_output="Four tabs and available lab summaries.",
                dry_run_note="This is fully supported by the current API.",
            ),
            MatlabAgentActionStep(
                id="render_overview",
                tab="overview",
                label="Render Overview tab",
                action_kind="render_tab",
                inputs=["MatlabLabSummary", "overview payload"],
                expected_output="Student-facing lab map with inputs, outputs, assumptions, and evidence.",
                dry_run_note="No MATLAB runtime is needed to render this tab.",
            ),
            MatlabAgentActionStep(
                id="render_teach",
                tab="teach",
                label="Render Teach tab",
                action_kind="render_tab",
                inputs=["MatlabTeachStep[]", "FocusMapEntry[]"],
                expected_output="Prompt-before-reveal steps and focus targets.",
                dry_run_note="Use generated hand-check text and focus-map metadata only.",
            ),
            MatlabAgentActionStep(
                id="highlight_focus",
                tab="teach",
                label="Highlight model focus",
                action_kind="highlight_target",
                inputs=["FocusMapEntry.target"],
                expected_output="Highlighted SVG target today or Simulink target in a future adapter.",
                requires_matlab_runtime=True,
                dry_run_note="Current API returns highlight plans; it must not claim hilite_system ran.",
            ),
            MatlabAgentActionStep(
                id="insert_probe",
                tab="probe",
                label="Insert or log probe",
                action_kind="insert_probe",
                inputs=["ProbePlan"],
                expected_output="Signal logging or sensor insertion plan.",
                requires_matlab_runtime=True,
                dry_run_note="Current API returns deterministic probe plans and MATLAB comments only.",
            ),
            MatlabAgentActionStep(
                id="run_simulation",
                tab="probe",
                label="Run simulation",
                action_kind="run_simulation",
                inputs=["MATLAB script artifact", "future Simulink model"],
                expected_output="Simulation evidence for the popup.",
                requires_matlab_runtime=True,
                dry_run_note="Current CI must not execute MATLAB; use generated text and deterministic hand checks.",
            ),
            MatlabAgentActionStep(
                id="compare_lab_delta",
                tab="lab_delta",
                label="Compare hand, simulation, and measured values",
                action_kind="compare_lab_delta",
                inputs=["LabDeltaRequest"],
                expected_output="Comparison rows, likely causes, next check, and reflection question.",
                dry_run_note="This is supported by deterministic Python heuristics.",
            ),
            MatlabAgentActionStep(
                id="refuse_unsupported",
                tab=None,
                label="Refuse unsupported runtime claims",
                action_kind="refuse_unsupported",
                inputs=["Any request requiring unconfigured MATLAB execution"],
                expected_output="Clear unsupported/future-adapter message.",
                dry_run_note="Do not fabricate MATLAB, Simulink, or bench results.",
            ),
        ],
        refusal_rules=[
            "Do not claim that MATLAB, Simulink, Simscape, hilite_system, or .mltbx packaging ran unless a future adapter reports that execution evidence.",
            "Do not turn LLM prose into final numerical answers.",
            "Do not diagnose biomedical safety or patient-connected device compliance.",
            "If a model region cannot be mapped to a focus target, return a clear missing-map message.",
            "If measured data uses unknown units or measurement points, ask for clarification before ranking causes strongly.",
        ],
        ci_validation=[
            "Validate JSON serialization of manifest, lab plan, adapter plan, artifacts, focus map, probe plan, and Lab Delta response.",
            "Inspect generated MATLAB script text for hand-check formulas and named outputs.",
            "Verify dry-run plans set requires_matlab_runtime=false at bundle level.",
            "Verify runtime action steps are marked requires_matlab_runtime=true when they would need MATLAB later.",
        ],
    )


def build_offline_bundle(
    lab_id: str,
    request: MatlabArtifactRequest | None = None,
) -> MatlabOfflineBundle:
    lab_plan = get_lab_plan(lab_id)
    artifacts = generate_artifacts(lab_id, request)
    lab_delta_example = compare_lab_delta(lab_id, lab_plan.lab_delta_seed_request)
    manifest = build_matlab_plugin_manifest()
    bundle_files = _offline_bundle_files(
        lab_id=lab_id,
        manifest=manifest,
        lab_plan=lab_plan,
        artifacts=artifacts,
        lab_delta_example=lab_delta_example,
    )
    return MatlabOfflineBundle(
        bundle_id=f"citt_{lab_id}_offline_bundle_v1",
        lab_id=lab_id,
        manifest=manifest,
        lab_plan=lab_plan,
        artifacts=artifacts,
        files=bundle_files,
        lab_delta_example=lab_delta_example,
        file_tree=[file.path for file in bundle_files],
        integrity_checks=[
            "Bundle contains manifest and lab plan JSON.",
            "Bundle contains generated artifacts for the selected lab.",
            "Bundle contains focus map and probe plan through the lab plan.",
            "Bundle includes a top-level citt.m MATLAB launcher and package stubs that open a four-tab popup from local JSON files without a server.",
            "Bundle is offline-first and does not require a local server or MATLAB runtime in CI.",
        ],
    )


def compare_lab_delta(lab_id: str, request: LabDeltaRequest) -> LabDeltaResponse:
    if lab_id not in {RC_ANTIALIAS_LAB_ID, INSTRUMENTATION_AMP_LAB_ID}:
        raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")

    rows = _comparison_rows(request)
    causes = _lab_delta_causes(request, rows)
    if not causes:
        causes.append(
            LabDeltaCause(
                id="measurement_noise_or_setup",
                title="Measurement noise or setup difference",
                explanation=(
                    "The numeric differences do not match a strong built-in pattern. "
                    "Treat this as a prompt to inspect probe placement, units, and "
                    "measurement noise before changing the model."
                ),
                confidence="low",
                related_keys=[row.id for row in rows],
                next_check="Confirm probe locations and units against the Overview tab.",
            )
        )

    next_check = causes[0].next_check
    return LabDeltaResponse(
        lab_id=lab_id,
        comparison_rows=rows,
        likely_causes=causes,
        next_probe_suggestion=_next_probe_suggestion(lab_id, causes),
        next_check=next_check,
        reflection_question=(
            "Which single assumption would you test first, and what measurement "
            "would make that assumption visible?"
        ),
        notes=_lab_delta_notes(request),
    )


def parse_lab_delta_upload(
    lab_id: str,
    request: MatlabLabDeltaUploadRequest,
) -> MatlabLabDeltaUploadResponse:
    get_lab_summary(lab_id)
    parsed_request, warnings = _parse_lab_delta_upload_request(request)
    response = compare_lab_delta(lab_id, parsed_request)
    return MatlabLabDeltaUploadResponse(
        lab_id=lab_id,
        parsed_request=parsed_request,
        lab_delta_response=response,
        warnings=warnings,
    )


def guided_steps_to_focus_map(
    guided_steps: Iterable[TutorStep],
    *,
    lab_id: str = "guided_step_bridge",
) -> list[FocusMapEntry]:
    entries: list[FocusMapEntry] = []
    for step in guided_steps:
        component_id = step.focus.components[0] if step.focus.components else None
        node_id = step.focus.nodes[0] if step.focus.nodes else None
        target_id = component_id or node_id or step.id
        target_type = "svg_component" if component_id else "svg_node" if node_id else "conceptual_path"
        entries.append(
            FocusMapEntry(
                id=f"{lab_id}_{step.id}",
                tab="teach",
                title=step.title,
                teaching_step_id=step.id,
                target=HighlightTarget(
                    id=target_id,
                    label=step.look_at or step.title,
                    target_type=target_type,
                    target_path=target_id,
                    simulink_path=f"{lab_id}/{target_id}",
                    svg_id=target_id,
                    description=step.body,
                ),
                reason=step.why_it_matters or step.body,
                surfaces=["web_svg", "simulink"],
                current_svg_components=step.focus.components,
                current_svg_nodes=step.focus.nodes,
                current_svg_goals=step.focus.goals,
                future_simulink_actions=[
                    f"Map SVG focus '{target_id}' to a Simulink block, line, or annotation.",
                    "Future MATLAB plugin may call hilite_system for the mapped target.",
                ],
                student_prompt=step.next_action,
            )
        )
    return entries


def _parse_lab_delta_upload_request(
    request: MatlabLabDeltaUploadRequest,
) -> tuple[LabDeltaRequest, list[str]]:
    upload_format = request.format
    content = request.content.strip()
    if upload_format == "auto":
        upload_format = "json" if content.startswith("{") or content.startswith("[") else "tsv" if "\t" in content else "csv"

    if upload_format == "json":
        parsed, warnings = _parse_lab_delta_json(content)
    else:
        delimiter = "\t" if upload_format == "tsv" else ","
        parsed, warnings = _parse_lab_delta_delimited(content, delimiter=delimiter)

    if request.notes:
        parsed.notes = f"{parsed.notes}\n{request.notes}" if parsed.notes else request.notes
    return parsed, warnings


def _parse_lab_delta_json(content: str) -> tuple[LabDeltaRequest, list[str]]:
    warnings: list[str] = []
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Lab Delta JSON upload could not be parsed: {exc}") from exc

    if isinstance(payload, dict) and any(
        key in payload for key in ["hand_values", "simulation_values", "measured_values"]
    ):
        return LabDeltaRequest.model_validate(payload), warnings

    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Lab Delta JSON upload must be a LabDeltaRequest object or a list of rows.")
    return _rows_to_lab_delta_request(rows, warnings)


def _parse_lab_delta_delimited(
    content: str,
    *,
    delimiter: str,
) -> tuple[LabDeltaRequest, list[str]]:
    warnings: list[str] = []
    reader = csv.DictReader(StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("Lab Delta upload must include a header row.")
    normalized_fields = {field.strip().lower() for field in reader.fieldnames if field}
    required = {"source", "key", "value"}
    missing = required - normalized_fields
    if missing:
        raise ValueError(
            "Lab Delta upload must include source, key, and value columns; "
            f"missing: {', '.join(sorted(missing))}."
        )
    return _rows_to_lab_delta_request(list(reader), warnings)


def _rows_to_lab_delta_request(
    rows: list[object],
    warnings: list[str],
) -> tuple[LabDeltaRequest, list[str]]:
    hand_values: dict[str, float] = {}
    simulation_values: dict[str, float] = {}
    measured_values: dict[str, float] = {}
    value_units: dict[str, str] = {}
    notes: list[str] = []

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            warnings.append(f"Row {index} is not an object and was ignored.")
            continue
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        source = str(normalized.get("source", "")).strip().lower()
        key = str(normalized.get("key", normalized.get("quantity", ""))).strip()
        value = normalized.get("value")
        unit = normalized.get("unit")
        note = normalized.get("note")

        if note:
            notes.append(str(note))
        if not key and source != "note":
            warnings.append(f"Row {index} has no key and was ignored.")
            continue
        if source == "note":
            if value:
                notes.append(str(value))
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            warnings.append(f"Row {index} value for {key or 'unknown'} is not numeric and was ignored.")
            continue

        if source == "hand":
            hand_values[key] = numeric_value
        elif source in {"sim", "simulation"}:
            simulation_values[key] = numeric_value
        elif source in {"measured", "measurement", "lab"}:
            measured_values[key] = numeric_value
        else:
            warnings.append(f"Row {index} has unsupported source {source!r} and was ignored.")
            continue

        if unit:
            value_units[key] = str(unit)

    return (
        LabDeltaRequest(
            hand_values=hand_values,
            simulation_values=simulation_values,
            measured_values=measured_values,
            value_units=value_units,
            notes="\n".join(notes) if notes else None,
        ),
        warnings,
    )


def _offline_bundle_files(
    *,
    lab_id: str,
    manifest: MatlabPluginManifest,
    lab_plan: MatlabLabPlan,
    artifacts: list[MatlabPluginArtifact],
    lab_delta_example: LabDeltaResponse,
) -> list[MatlabOfflineBundleFile]:
    artifact_index = [
        {
            "id": artifact.id,
            "kind": artifact.kind,
            "filename": artifact.filename,
            "path": f"examples/{lab_id}/artifacts/{artifact.filename}",
            "requires_matlab_runtime": artifact.requires_matlab_runtime,
        }
        for artifact in artifacts
    ]
    files = [
        MatlabOfflineBundleFile(
            path="citt.m",
            description="Top-level MATLAB launcher so students can type citt after adding the bundle directory to the MATLAB path.",
            content=_matlab_top_level_launcher_stub(lab_id),
        ),
        MatlabOfflineBundleFile(
            path="+citt/citt.m",
            description="Package-level MATLAB launcher alias. It loads bundled JSON instead of requiring a local server.",
            content=_matlab_package_entrypoint_stub(lab_id),
        ),
        MatlabOfflineBundleFile(
            path="+citt/loadOfflineBundle.m",
            description="Loads bundled manifest, lab plan, artifact index, and Lab Delta example from local JSON files.",
            content=_matlab_load_bundle_stub(lab_id),
        ),
        MatlabOfflineBundleFile(
            path="+citt/openPopup.m",
            description="Opens the four-tab MATLAB popup using bundled offline lab data.",
            content=_matlab_open_popup_stub(),
        ),
        MatlabOfflineBundleFile(
            path="+citt/renderOverviewTab.m",
            description="Renderer stub for the Overview tab data contract.",
            content=_matlab_render_stub("Overview", "bundle.lab_plan.overview"),
        ),
        MatlabOfflineBundleFile(
            path="+citt/renderTeachTab.m",
            description="Renderer stub for Teach tab steps and focus entries.",
            content=_matlab_render_stub("Teach", "bundle.lab_plan.teach_steps"),
        ),
        MatlabOfflineBundleFile(
            path="+citt/renderProbeTab.m",
            description="Renderer stub for Probe tab plans.",
            content=_matlab_render_stub("Probe", "bundle.lab_plan.probe_plan"),
        ),
        MatlabOfflineBundleFile(
            path="+citt/renderLabDeltaTab.m",
            description="Renderer stub for Lab Delta comparison examples.",
            content=_matlab_render_stub("Lab Delta", "bundle.lab_delta_example"),
        ),
        MatlabOfflineBundleFile(
            path=f"examples/{lab_id}/manifest.json",
            description="Bundled plugin manifest for offline MATLAB use.",
            content=_json_dump(manifest.model_dump()),
            mime_type="application/json",
        ),
        MatlabOfflineBundleFile(
            path=f"examples/{lab_id}/lab_plan.json",
            description="Bundled four-tab lab plan for offline MATLAB use.",
            content=_json_dump(lab_plan.model_dump()),
            mime_type="application/json",
        ),
        MatlabOfflineBundleFile(
            path=f"examples/{lab_id}/artifact_index.json",
            description="Index of bundled generated artifacts.",
            content=_json_dump(artifact_index),
            mime_type="application/json",
        ),
        MatlabOfflineBundleFile(
            path=f"examples/{lab_id}/lab_delta_example.json",
            description="Bundled Lab Delta example response.",
            content=_json_dump(lab_delta_example.model_dump()),
            mime_type="application/json",
        ),
        MatlabOfflineBundleFile(
            path="docs/offline_first.md",
            description="Short note explaining that the MATLAB plugin does not require a local server.",
            content=(
                "# CiTT Offline-First MATLAB Plugin\n\n"
                "The MATLAB plugin path loads bundled JSON and generated artifacts from the toolbox. "
                "A local FastAPI server is optional for development, web preview, or artifact refresh; "
                "it is not required for the student-facing MATLAB popup.\n"
            ),
            mime_type="text/markdown",
        ),
    ]
    for artifact in artifacts:
        files.append(
            MatlabOfflineBundleFile(
                path=f"examples/{lab_id}/artifacts/{artifact.filename}",
                description=artifact.description,
                content=artifact.content,
                mime_type=artifact.mime_type,
            )
        )
    return files


def _matlab_top_level_launcher_stub(lab_id: str) -> str:
    return f"""function varargout = citt(labId)
%CITT Open the CiTT MATLAB popup tutor using bundled offline artifacts.
%   This offline-first launcher does not require a local server.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "{lab_id}";
end

bundle = citt.loadOfflineBundle(labId);
fig = citt.openPopup(bundle);

if nargout > 0
    bundle.popup_figure = fig;
    varargout{{1}} = bundle;
end
end
"""


def _matlab_package_entrypoint_stub(lab_id: str) -> str:
    return f"""function varargout = citt(labId)
%CITT Package-level alias for the CiTT MATLAB popup tutor launcher.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "{lab_id}";
end

bundle = citt.loadOfflineBundle(labId);
fig = citt.openPopup(bundle);

if nargout > 0
    bundle.popup_figure = fig;
    varargout{{1}} = bundle;
end
end
"""


def _matlab_load_bundle_stub(lab_id: str) -> str:
    return f"""function bundle = loadOfflineBundle(labId)
%LOADOFFLINEBUNDLE Load CiTT bundled JSON artifacts without an API server.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "{lab_id}";
end

root = fileparts(fileparts(mfilename("fullpath")));
exampleDir = fullfile(root, "examples", char(labId));
bundle = struct();
bundle.manifest = jsondecode(fileread(fullfile(exampleDir, "manifest.json")));
bundle.lab_plan = jsondecode(fileread(fullfile(exampleDir, "lab_plan.json")));
bundle.artifact_index = jsondecode(fileread(fullfile(exampleDir, "artifact_index.json")));
bundle.lab_delta_example = jsondecode(fileread(fullfile(exampleDir, "lab_delta_example.json")));
end
"""


def _matlab_open_popup_stub() -> str:
    return """function fig = openPopup(bundle)
%OPENPOPUP Open the CiTT four-tab MATLAB popup from offline bundle data.

lab = bundle.lab_plan.lab;
titleText = "CiTT - " + oneLine(readField(lab, "title"));

fig = uifigure( ...
    "Name", titleText, ...
    "Position", [120 120 920 680] ...
);
main = uigridlayout(fig, [2 1]);
main.RowHeight = {54, "1x"};
main.Padding = [16 14 16 16];
main.RowSpacing = 10;

header = uilabel(main);
header.Text = "CiTT Popup Tutor: " + oneLine(readField(lab, "title"));
header.FontSize = 18;
header.FontWeight = "bold";

tabs = uitabgroup(main);
tabs.Layout.Row = 2;
tabs.Layout.Column = 1;

createTextTab(tabs, "Overview", overviewLines(bundle));
createTextTab(tabs, "Teach", teachLines(bundle));
createTextTab(tabs, "Probe", probeLines(bundle));
createTextTab(tabs, "Lab Delta", labDeltaLines(bundle));
end

function createTextTab(tabGroup, titleText, lines)
tab = uitab(tabGroup, "Title", titleText);
layout = uigridlayout(tab, [1 1]);
layout.Padding = [12 12 12 12];

textArea = uitextarea(layout);
textArea.Editable = "off";
textArea.FontName = "Menlo";
textArea.FontSize = 13;
textArea.Value = cellstr(lines(:));
end

function lines = overviewLines(bundle)
lab = bundle.lab_plan.lab;
overview = bundle.lab_plan.overview;

lines = strings(0, 1);
lines = addLine(lines, "Overview");
lines = addLine(lines, "");
lines = addLine(lines, "Lab title: " + oneLine(readField(lab, "title")));
lines = addLine(lines, "Objective: " + oneLine(readField(lab, "objective")));
lines = addLine(lines, "");
lines = addLine(lines, "Inputs");
lines = addBlock(lines, listLines(readField(lab, "inputs")));
lines = addLine(lines, "");
lines = addLine(lines, "Outputs");
lines = addBlock(lines, listLines(readField(lab, "outputs")));
lines = addLine(lines, "");
lines = addLine(lines, "Key parameters");
lines = addBlock(lines, mapLines(readField(lab, "key_parameters")));
lines = addLine(lines, "");
lines = addLine(lines, "Assumptions");
lines = addBlock(lines, listLines(readField(lab, "assumptions")));
lines = addLine(lines, "");
lines = addLine(lines, "Idealizations");
lines = addBlock(lines, listLines(readField(lab, "idealizations")));
lines = addLine(lines, "");
lines = addLine(lines, "BME safety boundary");
lines = addLine(lines, oneLine(readField(lab, "bme_safety_boundary")));
lines = addLine(lines, "");
lines = addLine(lines, "Artifact");
lines = addLine(lines, oneLine(readField(overview, "generated_artifact")));
lines = addLine(lines, "");
lines = addLine(lines, "Evidence to collect");
lines = addBlock(lines, listLines(readField(lab, "evidence_to_collect")));
lines = addLine(lines, "");
lines = addLine(lines, "Local server required: false");
end

function lines = teachLines(bundle)
steps = readField(bundle.lab_plan, "teach_steps");
focusMap = readField(bundle.lab_plan, "focus_map");

lines = strings(0, 1);
lines = addLine(lines, "Teach");
lines = addLine(lines, "");
for i = 1:numel(steps)
    step = steps(i);
    lines = addLine(lines, "Step " + string(i) + ": " + oneLine(readField(step, "title")));
    lines = addLine(lines, "Prompt: " + oneLine(readField(step, "prompt_before_reveal")));
    lines = addLine(lines, "Explanation: " + oneLine(readField(step, "explanation")));
    mistakes = listLines(readField(step, "common_mistakes"));
    if ~isempty(mistakes)
        lines = addLine(lines, "Common mistakes");
        lines = addBlock(lines, mistakes);
    end
    lines = addLine(lines, "");
end

lines = addLine(lines, "Focus map preview");
for i = 1:min(numel(focusMap), 8)
    entry = focusMap(i);
    target = readField(entry, "target");
    lines = addLine(lines, "- " + oneLine(readField(entry, "id")) + ": " + oneLine(readField(target, "label")));
end
end

function lines = probeLines(bundle)
probes = readField(bundle.lab_plan, "probe_plan");

lines = strings(0, 1);
lines = addLine(lines, "Probe");
lines = addLine(lines, "");
for i = 1:numel(probes)
    probe = probes(i);
    target = readField(probe, "target");
    lines = addLine(lines, oneLine(readField(probe, "title")));
    lines = addLine(lines, "Goal: " + oneLine(readField(probe, "student_goal")));
    lines = addLine(lines, "Target: " + oneLine(readField(target, "label")));
    lines = addLine(lines, "Quantity: " + oneLine(readField(probe, "quantity")) + " (" + oneLine(readField(probe, "unit")) + ")");
    lines = addLine(lines, "Question: " + oneLine(readField(probe, "student_question")));
    lines = addLine(lines, "Measurement: " + oneLine(readField(probe, "measurement_explanation")));
    logging = listLines(readField(probe, "suggested_logging"));
    if ~isempty(logging)
        lines = addLine(lines, "Suggested logging");
        lines = addBlock(lines, logging);
    end
    lines = addLine(lines, "");
end
end

function lines = labDeltaLines(bundle)
delta = bundle.lab_delta_example;
rows = readField(delta, "comparison_rows");
causes = readField(delta, "likely_causes");

lines = strings(0, 1);
lines = addLine(lines, "Lab Delta");
lines = addLine(lines, "");
lines = addLine(lines, "Comparison rows");
for i = 1:numel(rows)
    row = rows(i);
    lines = addLine(lines, "- " + oneLine(readField(row, "label")));
    lines = addLine(lines, "  hand: " + oneLine(readField(row, "hand_value")) + ...
        ", simulation: " + oneLine(readField(row, "simulation_value")) + ...
        ", measured: " + oneLine(readField(row, "measured_value")) + ...
        ", percent diff: " + oneLine(readField(row, "percent_difference")));
end
lines = addLine(lines, "");
lines = addLine(lines, "Likely causes");
for i = 1:numel(causes)
    cause = causes(i);
    lines = addLine(lines, "- " + oneLine(readField(cause, "title")) + ": " + oneLine(readField(cause, "explanation")));
    lines = addLine(lines, "  Next check: " + oneLine(readField(cause, "next_check")));
end
lines = addLine(lines, "");
lines = addLine(lines, "Next probe: " + oneLine(readField(delta, "next_probe_suggestion")));
lines = addLine(lines, "Reflection: " + oneLine(readField(delta, "reflection_question")));
end

function value = readField(container, fieldName)
if isstruct(container) && isfield(container, fieldName)
    value = container.(fieldName);
else
    value = [];
end
end

function text = oneLine(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif isnumeric(value) || islogical(value)
    if isscalar(value)
        text = string(num2str(value, 6));
    else
        text = string(mat2str(value));
    end
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = oneLine(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isstruct(value)
    try
        text = string(jsonencode(value));
    catch
        text = "<struct>";
    end
else
    text = string(value);
end
end

function lines = listLines(value)
items = toStringArray(value);
if isempty(items)
    lines = strings(0, 1);
else
    lines = "- " + items(:);
end
end

function lines = mapLines(value)
if isstruct(value)
    names = fieldnames(value);
    lines = strings(numel(names), 1);
    for i = 1:numel(names)
        name = string(names{i});
        lines(i) = "- " + name + ": " + oneLine(value.(names{i}));
    end
else
    lines = listLines(value);
end
end

function items = toStringArray(value)
if isempty(value)
    items = strings(0, 1);
elseif isstring(value)
    items = value(:);
elseif ischar(value)
    items = string(value);
elseif iscell(value)
    items = strings(numel(value), 1);
    for i = 1:numel(value)
        items(i) = oneLine(value{i});
    end
elseif isnumeric(value) || islogical(value)
    items = string(value(:));
else
    items = string(value);
end
end

function lines = addLine(lines, line)
lines(end + 1, 1) = string(line);
end

function lines = addBlock(lines, block)
if ~isempty(block)
    lines = [lines; string(block(:))];
end
end
"""


def _matlab_render_stub(tab_name: str, expression: str) -> str:
    function_name = f"render{tab_name.replace(' ', '')}Tab"
    return f"""function data = {function_name}(bundle)
%{function_name.upper()} Return data for the CiTT {tab_name} tab.
%   This is a renderer contract stub for future App Designer UI code.

data = {expression};
disp("CiTT {tab_name} tab data loaded from offline bundle.");
end
"""


def _overview_payload(lab: MatlabLabSummary) -> dict[str, object]:
    return {
        "title": lab.title,
        "objective": lab.objective,
        "inputs": lab.inputs,
        "outputs": lab.outputs,
        "key_parameters": lab.key_parameters,
        "assumptions": lab.assumptions,
        "idealizations": lab.idealizations,
        "bme_safety_boundary": lab.bme_safety_boundary,
        "generated_artifacts": lab.generated_artifact_kinds,
        "evidence_to_collect": lab.evidence_to_collect,
    }


def _teach_steps(lab_id: str) -> list[MatlabTeachStep]:
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return [
            MatlabTeachStep(
                id="overview_signal_flow",
                title="Trace the signal chain",
                prompt_before_reveal=(
                    "Before calculating, point to where the ECG-like signal, 60 Hz interference, "
                    "filter, sampler, and output each live."
                ),
                focus_entry_ids=["overview_signal_flow", "input_path", "rc_filter", "sampling_stage"],
                verified_value_refs=["fs", "target_fc"],
                explanation=(
                    "Anti-aliasing is a chain problem: the analog filter changes the waveform "
                    "before the sampler sees it."
                ),
                common_mistakes=[
                    "Treating the sampler as if it can remove analog interference by itself.",
                    "Looking only at the output without checking the input path.",
                ],
            ),
            MatlabTeachStep(
                id="calculate_cutoff",
                title="Calculate the RC cutoff",
                prompt_before_reveal="Predict whether the cutoff should use R*C or 2*pi*R*C.",
                focus_entry_ids=["rc_filter"],
                verified_value_refs=["hand_fc_hz", "nyquist"],
                explanation="For a first-order RC low-pass, fc = 1/(2*pi*R*C) in Hz and omega_c = 1/(R*C) in rad/s.",
                common_mistakes=[
                    "Using omega_c as if it were Hz.",
                    "Dropping the 2*pi factor.",
                    "Entering 100 nF as 100 uF.",
                ],
                reveal_policy="show_hand_check",
            ),
            MatlabTeachStep(
                id="connect_to_sampling",
                title="Connect cutoff to sampling",
                prompt_before_reveal="Compare 60 Hz, the cutoff, and Nyquist before looking at the sampled plot.",
                focus_entry_ids=["sampling_stage", "output_signal"],
                verified_value_refs=["attenuation_at_60_hz"],
                explanation=(
                    "The RC stage should reduce the 60 Hz component before the ADC-facing samples are interpreted."
                ),
                common_mistakes=[
                    "Checking Nyquist but forgetting the analog filter response.",
                    "Comparing sampled output to hand cutoff at a different measurement point.",
                ],
                reveal_policy="show_simulation_evidence",
            ),
        ]
    if lab_id == INSTRUMENTATION_AMP_LAB_ID:
        return [
            MatlabTeachStep(
                id="separate_diff_common",
                title="Separate differential and common-mode input",
                prompt_before_reveal=(
                    "Identify which part is the small sensor signal and which part is shared by both inputs."
                ),
                focus_entry_ids=["differential_input", "common_mode_input"],
                verified_value_refs=["v_diff", "v_common"],
                explanation=(
                    "The ideal instrumentation amplifier amplifies the differential input, not the shared common-mode level."
                ),
                common_mistakes=[
                    "Multiplying common-mode voltage by differential gain.",
                    "Swapping input polarity without tracking output sign.",
                ],
            ),
            MatlabTeachStep(
                id="feedback_gain_path",
                title="Inspect the feedback and gain-setting path",
                prompt_before_reveal="Point to the feedback loop and gain-setting resistor before using the gain formula.",
                focus_entry_ids=["feedback_loop", "gain_setting_resistor", "feedback_resistor"],
                verified_value_refs=["gain", "ideal_output_v"],
                explanation="The gain-setting resistor controls the ideal differential gain in this intro stub.",
                common_mistakes=[
                    "Assuming ideal op-amp input current flows into the input pins.",
                    "Ignoring resistor matching when discussing common-mode rejection.",
                ],
                reveal_policy="show_hand_check",
            ),
        ]
    raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")


def _lab_delta_seed_request(lab_id: str) -> LabDeltaRequest:
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return LabDeltaRequest(
            hand_values={"fc_hz": 40.0},
            simulation_values={"fc_hz": 40.1},
            measured_values={"fc_hz": 40.0 * 2 * math.pi},
            value_units={"fc_hz": "Hz"},
            notes="Seed example intentionally shows angular frequency reported as Hz.",
        )
    if lab_id == INSTRUMENTATION_AMP_LAB_ID:
        return LabDeltaRequest(
            hand_values={"gain": 21.0, "output_v": 0.021},
            simulation_values={"gain": 21.0, "output_v": 0.021},
            measured_values={"gain": 20.5, "output_v": 0.0205},
            value_units={"gain": "V/V", "output_v": "V"},
            notes="Seed example for modest gain error from resistor tolerance or loading.",
        )
    raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")


def _default_artifact_kinds(lab_id: str) -> list[MatlabArtifactKind]:
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return [
            "matlab_script",
            "simulink_build_script",
            "focus_map_json",
            "probe_plan_json",
            "app_designer_plan",
            "toolbox_manifest",
        ]
    if lab_id == INSTRUMENTATION_AMP_LAB_ID:
        return [
            "matlab_script",
            "focus_map_json",
            "probe_plan_json",
            "app_designer_plan",
            "toolbox_manifest",
        ]
    raise ValueError(f"Unknown MATLAB plugin lab: {lab_id}")


def _ordered_artifact_kinds(kinds: set[str]) -> list[str]:
    order = [
        "matlab_script",
        "simulink_build_script",
        "live_script_plan",
        "app_designer_plan",
        "toolbox_manifest",
        "focus_map_json",
        "probe_plan_json",
    ]
    return [kind for kind in order if kind in kinds]


def _rc_matlab_script_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="rc_antialias_adc_matlab_script",
        lab_id=lab_id,
        kind="matlab_script",
        filename="citt_rc_antialias_adc.m",
        title="RC anti-aliasing MATLAB script",
        description=(
            "Dry-run MATLAB script artifact for hand cutoff checks, simple filter "
            "simulation, plots, and future popup tab hooks."
        ),
        content=_rc_matlab_script(),
    )


def _rc_simulink_plan_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="rc_antialias_adc_simulink_plan",
        lab_id=lab_id,
        kind="simulink_build_script",
        filename="citt_rc_antialias_adc_simulink_plan.m",
        title="Simulink build-script plan",
        description=(
            "Placeholder build plan describing blocks, lines, logging, and highlight "
            "targets. It does not require MATLAB in CI."
        ),
        content="""% CiTT Simulink build-script plan for RC anti-aliasing before ADC
% This artifact describes a future build path; Python tests inspect text only.
% Future MATLAB plugin may call hilite_system for these blocks/lines.
% This artifact only describes the highlight plan; it does not require MATLAB in CI.
%
% Planned blocks:
%   input_path: ECG-like signal source plus 60 Hz interference
%   rc_filter: first-order RC low-pass subsystem
%   sampling_stage: zero-order hold / ADC sample stage
%   output_signal: logged sampled waveform
%
% Planned lines:
%   input_path -> rc_filter
%   rc_filter -> sampling_stage
%   sampling_stage -> output_signal
%
% Planned logs:
%   log_signal('input_path')
%   log_signal('rc_filter_output')
%   log_signal('sampled_output')
%
% Future Simulink highlight: input_path
% Future Simulink highlight: rc_filter
% Future Simulink highlight: sampling_stage
% Future Simulink highlight: output_signal
""",
    )


def _rc_live_script_plan_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="rc_antialias_adc_live_script_plan",
        lab_id=lab_id,
        kind="live_script_plan",
        filename="citt_rc_antialias_adc_live_script_plan.txt",
        title="Live Script teaching plan",
        description="Section plan for a future MATLAB Live Script export.",
        content="""1. Overview: anti-aliasing goal, fs, target_fc, R, C, safety boundary.
2. Teach: predict cutoff, calculate fc = 1/(2*pi*R*C), inspect attenuation.
3. Probe: log input, RC output, sampled output, and 60 Hz component.
4. Lab Delta: compare hand, simulation, and measured values with likely causes.
""",
    )


def _rc_focus_map_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="rc_antialias_adc_focus_map",
        lab_id=lab_id,
        kind="focus_map_json",
        filename="citt_rc_antialias_adc_focus_map.json",
        title="RC anti-aliasing focus map",
        description="Typed bridge from current SVG focus semantics to future Simulink highlights.",
        content=_json_dump([entry.model_dump() for entry in _rc_focus_map()]),
        mime_type="application/json",
    )


def _rc_probe_plan_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="rc_antialias_adc_probe_plan",
        lab_id=lab_id,
        kind="probe_plan_json",
        filename="citt_rc_antialias_adc_probe_plan.json",
        title="RC anti-aliasing probe plan",
        description="Suggested logging, sensor insertion, and student questions for the Probe tab.",
        content=_json_dump([probe.model_dump() for probe in _rc_probe_plan()]),
        mime_type="application/json",
    )


def _instrumentation_amp_script_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="instrumentation_amp_intro_matlab_script",
        lab_id=lab_id,
        kind="matlab_script",
        filename="citt_instrumentation_amplifier_intro.m",
        title="Instrumentation amplifier intro MATLAB stub",
        description="Future vertical-slice stub for gain and common-mode teaching.",
        content="""% CiTT generated artifact notice
% Instrumentation amplifier intro stub for future MATLAB popup tutor.
% This is a hand-check and teaching plan, not live MATLAB execution in CI.

v_diff = 1e-3;      % V
v_common = 1.0;     % V
R = 10000;          % ohm
Rg = 1000;          % ohm
gain = 1 + 2*R/Rg;
ideal_output_v = gain * v_diff;

cmrr_teaching_note = "Matched resistor ratios reject common-mode voltage in the ideal model.";
citt_results = struct( ...
    "gain", gain, ...
    "ideal_output_v", ideal_output_v, ...
    "cmrr_teaching_note", cmrr_teaching_note);

% CiTT Overview tab
% CiTT Teach tab
% CiTT Probe tab
% CiTT Lab Delta tab
% Future Simulink highlight: feedback_loop
% Future Simulink highlight: gain_setting_resistor
% Future Simulink highlight: differential_input
% Future Simulink highlight: common_mode_input
% Future Simulink highlight: output_node
""",
    )


def _instrumentation_amp_live_script_plan_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="instrumentation_amp_intro_live_script_plan",
        lab_id=lab_id,
        kind="live_script_plan",
        filename="citt_instrumentation_amplifier_intro_live_script_plan.txt",
        title="Instrumentation amplifier Live Script plan",
        description="Section plan for a future instrumentation-amplifier Live Script.",
        content="""1. Overview: differential signal, common-mode level, gain-setting resistor.
2. Teach: derive gain = 1 + 2R/Rg and separate differential from common-mode input.
3. Probe: inspect feedback loop, inverting input, noninverting input, and output node.
4. Lab Delta: compare ideal output with measured output and CMRR-related deviations.
""",
    )


def _instrumentation_amp_focus_map_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="instrumentation_amp_intro_focus_map",
        lab_id=lab_id,
        kind="focus_map_json",
        filename="citt_instrumentation_amplifier_intro_focus_map.json",
        title="Instrumentation amplifier focus map",
        description="Stub focus map for future feedback-loop highlighting.",
        content=_json_dump([entry.model_dump() for entry in _instrumentation_amp_focus_map()]),
        mime_type="application/json",
    )


def _instrumentation_amp_probe_plan_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id="instrumentation_amp_intro_probe_plan",
        lab_id=lab_id,
        kind="probe_plan_json",
        filename="citt_instrumentation_amplifier_intro_probe_plan.json",
        title="Instrumentation amplifier probe plan",
        description="Stub Probe tab plan for future instrumentation-amplifier lab.",
        content=_json_dump([probe.model_dump() for probe in _instrumentation_amp_probe_plan()]),
        mime_type="application/json",
    )


def _app_designer_plan_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id=f"{lab_id}_app_designer_plan",
        lab_id=lab_id,
        kind="app_designer_plan",
        filename=f"citt_{lab_id}_app_designer_plan.json",
        title="Four-tab App Designer layout plan",
        description="JSON plan for the future MATLAB App Designer popup.",
        content=_json_dump(
            {
                "entrypoint": "citt",
                "window_title": "CiTT Popup Tutor",
                "tabs": [
                    {"id": "overview", "widgets": ["lab summary", "parameters", "evidence checklist"]},
                    {"id": "teach", "widgets": ["step list", "prompt before reveal", "highlight target"]},
                    {"id": "probe", "widgets": ["probe selector", "logging plan", "measurement question"]},
                    {"id": "lab_delta", "widgets": ["comparison table", "likely causes", "reflection prompt"]},
                ],
                "lab_id": lab_id,
            }
        ),
        mime_type="application/json",
    )


def _toolbox_manifest_artifact(lab_id: str) -> MatlabPluginArtifact:
    return MatlabPluginArtifact(
        id=f"{lab_id}_toolbox_manifest",
        lab_id=lab_id,
        kind="toolbox_manifest",
        filename=f"citt_{lab_id}_toolbox_manifest.json",
        title="Future .mltbx package manifest",
        description="Dry-run manifest for a future MATLAB toolbox package.",
        content=_json_dump(
            {
                "package_name": "CiTT MATLAB Popup Tutor",
                "entrypoint": "citt.m",
                "package_entrypoint": "+citt/citt.m",
                "contents": [
                    "citt.m",
                    "+citt/",
                    "templates/",
                    "examples/",
                    "docs/",
                    "app/",
                ],
                "lab_id": lab_id,
                "requires_matlab_runtime_in_ci": False,
            }
        ),
        mime_type="application/json",
    )


def _rc_matlab_script() -> str:
    return """% CiTT generated artifact notice
% RC anti-aliasing before ADC
% Generated for the future MATLAB popup tutor. This script is inspectable text
% for the MVP API and does not make MATLAB a CI dependency.

%% CiTT Overview tab
% Lab: RC anti-aliasing before ADC
% Objective: compare hand cutoff, simple filter behavior, and sampled output.
% BME safety boundary: teaching signal-conditioning model, not patient safety approval.

%% Parameters
fs = 500;                 % Hz
target_fc = 40;           % Hz
R = 39788.7358;           % ohm
C = 100e-9;               % F
duration_s = 2.0;         % seconds
dt = 1/(20*fs);           % fine simulation step for the teaching artifact

%% Hand calculation
fc = 1/(2*pi*R*C);
nyquist = fs/2;
hand_fc_hz = fc;
attenuation_at_60_hz = 1/sqrt(1 + (60/fc)^2);

%% Example signal: ECG-like low-frequency component plus 60 Hz interference
t = 0:dt:duration_s;
ecg_like = 0.8*sin(2*pi*1.2*t) + 0.15*sin(2*pi*2.4*t);
interference_60hz = 0.25*sin(2*pi*60*t);
input_signal = ecg_like + interference_60hz;

%% Simple filter simulation
tau = R*C;
filtered_output = zeros(size(input_signal));
for k = 2:numel(t)
    alpha = dt/(tau + dt);
    filtered_output(k) = filtered_output(k-1) + alpha*(input_signal(k) - filtered_output(k-1));
end

sample_times = 0:(1/fs):duration_s;
sampled_output = interp1(t, filtered_output, sample_times, "linear");

%% Plots
figure("Name", "CiTT RC anti-aliasing before ADC");
subplot(3,1,1);
plot(t, input_signal);
title("Input: ECG-like signal + 60 Hz interference");
xlabel("Time (s)");
ylabel("Voltage (V)");

subplot(3,1,2);
plot(t, filtered_output);
title("Filtered output");
xlabel("Time (s)");
ylabel("Voltage (V)");

subplot(3,1,3);
stem(sample_times, sampled_output, ".");
title("Sampled output");
xlabel("Time (s)");
ylabel("Voltage (V)");

%% Named outputs
simulated_summary = struct( ...
    "fs_hz", fs, ...
    "target_fc_hz", target_fc, ...
    "hand_fc_hz", hand_fc_hz, ...
    "nyquist_hz", nyquist, ...
    "attenuation_at_60_hz", attenuation_at_60_hz);

citt_results = struct( ...
    "hand_fc_hz", hand_fc_hz, ...
    "simulated_summary", simulated_summary, ...
    "sample_times", sample_times, ...
    "sampled_output", sampled_output);

%% CiTT Teach tab
% Ask the student to predict whether 60 Hz is above or below the cutoff.
% Reveal fc = 1/(2*pi*R*C) only after the student commits to the role of R and C.

%% CiTT Probe tab
% Add voltage probe at RC output.
% Log input_signal and filtered_output.
% Compare pre-filter and post-filter 60 Hz component.

%% CiTT Lab Delta tab
% Compare hand_fc_hz, simulated cutoff, and measured cutoff.
% Likely causes include rad/s vs Hz, nF/uF mistakes, tolerance, loading,
% transient settling, Nyquist/sample-rate issues, ADC quantization, solver settings,
% and measurement noise.

%% Future model highlighting
% Future MATLAB plugin may call hilite_system for these blocks/lines.
% This artifact only describes the highlight plan; it does not require MATLAB in CI.
% Future Simulink highlight: input_path
% Future Simulink highlight: rc_filter
% Future Simulink highlight: sampling_stage
% Future Simulink highlight: output_signal
"""


def _rc_focus_map() -> list[FocusMapEntry]:
    return [
        FocusMapEntry(
            id="overview_signal_flow",
            tab="overview",
            title="Signal flow overview",
            teaching_step_id="overview",
            target=HighlightTarget(
                id="overview_signal_flow",
                label="Input to filter to sampler to output",
                target_type="conceptual_path",
                target_path="input_path->rc_filter->sampling_stage->output_signal",
                simulink_path="citt_rc_antialias_adc",
                description="Whole-model path students should understand before probing.",
            ),
            reason="The student needs the map before interpreting any local value.",
            surfaces=["web_svg", "simulink", "conceptual"],
            current_svg_components=["VSIG", "R", "C"],
            current_svg_nodes=["vin", "vout", "0"],
            future_simulink_actions=[
                "Highlight the full signal path from source through RC filter to sampling stage.",
                "Future MATLAB plugin may call hilite_system on connected blocks and lines.",
            ],
            student_prompt="Where does the anti-aliasing decision happen in this chain?",
        ),
        FocusMapEntry(
            id="input_path",
            tab="teach",
            title="Input path",
            teaching_step_id="identify_input",
            target=HighlightTarget(
                id="input_path",
                label="ECG-like signal plus 60 Hz interference",
                target_type="line",
                target_path="input_path",
                simulink_path="citt_rc_antialias_adc/Input Path",
                svg_id="VSIG",
                description="The signal before the RC stage.",
            ),
            reason="Students should see that the unwanted 60 Hz component enters before filtering.",
            surfaces=["web_svg", "simulink"],
            current_svg_components=["VSIG"],
            current_svg_nodes=["vin"],
            future_simulink_actions=["Highlight the source block and line into the RC subsystem."],
            student_prompt="Which frequency component do you expect the filter to reduce more?",
        ),
        FocusMapEntry(
            id="rc_filter",
            tab="teach",
            title="RC filter",
            teaching_step_id="calculate_cutoff",
            target=HighlightTarget(
                id="rc_filter",
                label="R-C low-pass stage",
                target_type="block",
                target_path="rc_filter",
                simulink_path="citt_rc_antialias_adc/RC Filter",
                svg_id="R,C",
                description="The first-order low-pass stage that sets cutoff.",
            ),
            reason="This is where fc = 1/(2*pi*R*C) becomes a model parameter.",
            surfaces=["web_svg", "simulink"],
            current_svg_components=["R", "C"],
            current_svg_nodes=["vout", "0"],
            future_simulink_actions=["Highlight the RC subsystem and its parameter annotation."],
            student_prompt="What happens to fc if C is accidentally entered in uF instead of nF?",
        ),
        FocusMapEntry(
            id="sampling_stage",
            tab="teach",
            title="Sampling stage",
            teaching_step_id="connect_to_adc",
            target=HighlightTarget(
                id="sampling_stage",
                label="ADC sampling stage",
                target_type="block",
                target_path="sampling_stage",
                simulink_path="citt_rc_antialias_adc/Sampling Stage",
                description="The point where Nyquist and sample time matter.",
            ),
            reason="Filtering must be interpreted relative to fs and Nyquist.",
            surfaces=["simulink", "conceptual"],
            current_svg_goals=["adc_sampled_output"],
            future_simulink_actions=["Highlight the zero-order hold or ADC sample block."],
            student_prompt="How does Nyquist compare with the 60 Hz interference?",
        ),
        FocusMapEntry(
            id="output_signal",
            tab="teach",
            title="Output signal",
            teaching_step_id="inspect_output",
            target=HighlightTarget(
                id="output_signal",
                label="Filtered and sampled output",
                target_type="line",
                target_path="output_signal",
                simulink_path="citt_rc_antialias_adc/Output Signal",
                description="The waveform sent to downstream analysis.",
            ),
            reason="This is the student-visible consequence of the filter and sampler.",
            surfaces=["simulink", "conceptual"],
            current_svg_nodes=["vout"],
            current_svg_goals=["vout"],
            future_simulink_actions=["Highlight the logged output line and scope block."],
            student_prompt="What visual change should the filtered output show compared with the input?",
        ),
        FocusMapEntry(
            id="lab_delta_measurement_point",
            tab="lab_delta",
            title="Lab Delta measurement point",
            teaching_step_id="compare_measurements",
            target=HighlightTarget(
                id="lab_delta_measurement_point",
                label="RC output measurement",
                target_type="port",
                target_path="rc_filter/output",
                simulink_path="citt_rc_antialias_adc/RC Filter/1",
                port="output",
                svg_id="vout",
                description="The probe point used to compare hand, simulation, and lab values.",
            ),
            reason="Lab Delta is only meaningful if all three values refer to the same point.",
            surfaces=["web_svg", "simulink"],
            current_svg_nodes=["vout", "0"],
            current_svg_goals=["cutoff_hz", "output_rms_v"],
            future_simulink_actions=["Attach logging or a voltage probe at the RC output port."],
            student_prompt="Are your hand value, simulation value, and measured value all taken at this point?",
        ),
    ]


def _instrumentation_amp_focus_map() -> list[FocusMapEntry]:
    targets = [
        (
            "feedback_loop",
            "Feedback loop",
            "block",
            "The loop that forces op-amp inputs together in the ideal model.",
            "Highlight the feedback loop around the input amplifier stage.",
        ),
        (
            "gain_setting_resistor",
            "Gain-setting resistor",
            "block",
            "The resistor that controls gain in the intro hand check.",
            "Highlight Rg and its gain annotation.",
        ),
        (
            "differential_input",
            "Differential input",
            "line",
            "The small sensor difference that should be amplified.",
            "Highlight the two sensor input lines as a differential pair.",
        ),
        (
            "common_mode_input",
            "Common-mode input",
            "annotation",
            "The shared body/reference level that should mostly reject.",
            "Highlight the common-mode annotation rather than treating it as signal gain.",
        ),
        (
            "inverting_input",
            "Inverting input",
            "port",
            "The op-amp input used in the feedback equality.",
            "Highlight the inverting input port.",
        ),
        (
            "noninverting_input",
            "Noninverting input",
            "port",
            "The op-amp input connected to the sensor side.",
            "Highlight the noninverting input port.",
        ),
        (
            "op_amp_output",
            "Op-amp output",
            "port",
            "The internal amplifier output before the difference stage.",
            "Highlight the op-amp output port.",
        ),
        (
            "feedback_resistor",
            "Feedback resistor",
            "block",
            "The resistor that closes the local feedback path.",
            "Highlight the feedback resistor branch.",
        ),
        (
            "output_node",
            "Output node",
            "line",
            "The final ideal differential output.",
            "Highlight the output node or logged signal.",
        ),
    ]
    return [
        FocusMapEntry(
            id=target_id,
            tab="teach",
            title=title,
            teaching_step_id=target_id,
            target=HighlightTarget(
                id=target_id,
                label=title,
                target_type=target_type,
                target_path=target_id,
                simulink_path=f"citt_instrumentation_amplifier_intro/{title}",
                svg_id=target_id,
                description=description,
            ),
            reason=description,
            surfaces=["web_svg", "simulink"],
            current_svg_components=[target_id],
            future_simulink_actions=[
                action,
                "Future MATLAB plugin may call hilite_system for this target.",
            ],
            student_prompt="What value or assumption does this highlighted region control?",
        )
        for target_id, title, target_type, description, action in targets
    ]


def _rc_probe_plan() -> list[ProbePlan]:
    return [
        ProbePlan(
            id="rc_output_voltage_probe",
            title="Add voltage probe at RC output",
            student_goal="Inspect the local signal after the low-pass stage and before sampling.",
            target=HighlightTarget(
                id="rc_filter_output",
                label="RC filter output",
                target_type="port",
                target_path="rc_filter/output",
                simulink_path="citt_rc_antialias_adc/RC Filter/1",
                port="output",
                svg_id="vout",
                description="Voltage at the capacitor/output node.",
            ),
            quantity="voltage",
            unit="V",
            expected_behavior="The 60 Hz component should be smaller after the RC stage.",
            student_question="Does the measured output match the cutoff you calculated by hand?",
            measurement_explanation=(
                "This probe checks the exact point where the filter output is handed "
                "to the sampling stage."
            ),
            suggested_logging=["input_signal", "filtered_output"],
            suggested_sensor_insertion=["Voltage sensor from vout to ground in a future Simscape model."],
            future_matlab_steps=[
                "Enable signal logging on the RC output line.",
                "Add a scope or logged signal named rc_filter_output.",
                "Associate the log with focus_map entry lab_delta_measurement_point.",
            ],
            matlab_comment_lines=[
                "% CiTT Probe tab: add voltage probe at RC output.",
                "% Future Simulink highlight: rc_filter",
            ],
        ),
        ProbePlan(
            id="compare_60hz_component",
            title="Compare pre-filter and post-filter 60 Hz component",
            student_goal="Estimate how much interference remains at the ADC input.",
            target=HighlightTarget(
                id="sixty_hz_comparison",
                label="60 Hz before/after comparison",
                target_type="conceptual_path",
                target_path="input_path->rc_filter_output",
                simulink_path="citt_rc_antialias_adc/Input Path to RC Filter Output",
                description="Frequency-component comparison across the filter.",
            ),
            quantity="attenuation",
            unit="ratio or dB",
            expected_behavior="The post-filter 60 Hz amplitude should be lower than the input amplitude.",
            student_question="Is 60 Hz far enough above cutoff to be meaningfully reduced?",
            measurement_explanation=(
                "This separates filter behavior from sampling behavior before discussing aliasing."
            ),
            suggested_logging=["input_signal", "filtered_output"],
            future_matlab_steps=[
                "Compute or estimate the 60 Hz component in both logged signals.",
                "Show the comparison in the Probe tab before Lab Delta diagnosis.",
            ],
            matlab_comment_lines=[
                "% CiTT Probe tab: compare pre-filter and post-filter 60 Hz component.",
            ],
        ),
        ProbePlan(
            id="sampled_output_probe",
            title="Log sampled output",
            student_goal="Inspect what the ADC-facing data stream would contain.",
            target=HighlightTarget(
                id="sampled_output",
                label="Sampled output",
                target_type="line",
                target_path="sampling_stage/output",
                simulink_path="citt_rc_antialias_adc/Sampling Stage/1",
                description="Output after the sampling stage.",
            ),
            quantity="sampled voltage",
            unit="V",
            expected_behavior="Samples should follow the filtered waveform at 500 Hz.",
            student_question="Does the sampled waveform preserve the filtered signal without alias surprises?",
            measurement_explanation=(
                "This probe connects the analog filter output to the ADC learning objective."
            ),
            suggested_logging=["sample_times", "sampled_output"],
            future_matlab_steps=[
                "Log the zero-order hold or ADC output line.",
                "Compare sampled_output against filtered_output at the same timestamps.",
            ],
            matlab_comment_lines=[
                "% CiTT Probe tab: log sampled output for ADC comparison.",
                "% Future Simulink highlight: sampling_stage",
            ],
        ),
    ]


def _instrumentation_amp_probe_plan() -> list[ProbePlan]:
    return [
        ProbePlan(
            id="feedback_resistor_current_probe",
            title="Add current sensor through feedback resistor",
            student_goal="Connect feedback current to the ideal op-amp input-current assumption.",
            target=HighlightTarget(
                id="feedback_resistor",
                label="Feedback resistor",
                target_type="block",
                target_path="feedback_resistor",
                simulink_path="citt_instrumentation_amplifier_intro/Feedback Resistor",
                svg_id="feedback_resistor",
                description="Feedback branch in the input amplifier stage.",
            ),
            quantity="current",
            unit="A",
            expected_behavior="Feedback branch current should reflect resistor voltage, not op-amp input current.",
            student_question="Where does the feedback current flow if ideal op-amp input current is zero?",
            measurement_explanation="This supports the future feedback-loop highlight workflow.",
            suggested_sensor_insertion=["Current sensor in series with the feedback resistor."],
            future_matlab_steps=[
                "Insert a current sensor in the feedback resistor branch.",
                "Highlight feedback_loop and feedback_resistor together.",
            ],
            matlab_comment_lines=[
                "% CiTT Probe tab: add current sensor through feedback resistor.",
                "% Future Simulink highlight: feedback_loop",
            ],
        )
    ]


def _comparison_rows(request: LabDeltaRequest) -> list[LabDeltaComparisonRow]:
    keys = sorted(
        set(request.hand_values)
        | set(request.simulation_values)
        | set(request.measured_values)
    )
    rows: list[LabDeltaComparisonRow] = []
    for key in keys:
        hand = request.hand_values.get(key)
        simulation = request.simulation_values.get(key)
        measured = request.measured_values.get(key)
        reference_source, reference = _preferred_reference(hand, simulation, measured)
        compared_source, compared = _preferred_compared(reference_source, hand, simulation, measured)
        if reference is None or compared is None:
            continue

        absolute_difference = abs(compared - reference)
        percent_difference = (
            absolute_difference / abs(reference) * 100.0
            if abs(reference) > 1e-30
            else None
        )
        rows.append(
            LabDeltaComparisonRow(
                id=key,
                label=_label_for_key(key),
                unit=request.value_units.get(key),
                hand_value=hand,
                simulation_value=simulation,
                measured_value=measured,
                reference_source=reference_source,
                compared_source=compared_source,
                absolute_difference=absolute_difference,
                percent_difference=percent_difference,
                note=_comparison_note(key, reference_source, compared_source),
            )
        )
    return rows


def _preferred_reference(
    hand: float | None,
    simulation: float | None,
    measured: float | None,
) -> tuple[str, float | None]:
    if hand is not None:
        return "hand", hand
    if simulation is not None:
        return "simulation", simulation
    return "measured", measured


def _preferred_compared(
    reference_source: str,
    hand: float | None,
    simulation: float | None,
    measured: float | None,
) -> tuple[str, float | None]:
    if measured is not None and reference_source != "measured":
        return "measured", measured
    if simulation is not None and reference_source != "simulation":
        return "simulation", simulation
    return "hand", hand


def _lab_delta_causes(
    request: LabDeltaRequest,
    rows: list[LabDeltaComparisonRow],
) -> list[LabDeltaCause]:
    causes: list[LabDeltaCause] = []
    seen: set[str] = set()

    def add(cause: LabDeltaCause) -> None:
        if cause.id not in seen:
            causes.append(cause)
            seen.add(cause.id)

    ratio_keys = _keys_with_ratio_near(request, (2 * math.pi,), tolerance=0.08)
    if ratio_keys:
        add(
            LabDeltaCause(
                id="rad_s_vs_hz",
                title="rad/s vs Hz confusion",
                explanation=(
                    "One value is near a 2*pi ratio from another value. That often "
                    "means angular frequency in rad/s was compared with frequency in Hz, "
                    "or the 2*pi factor was missed."
                ),
                confidence="high",
                related_keys=ratio_keys,
                next_check="Recalculate cutoff using fc = 1/(2*pi*R*C) in Hz and compare with omega_c = 1/(R*C) in rad/s.",
            )
        )

    prefix_keys = _keys_with_ratio_near(request, (1000.0,), tolerance=0.05)
    if prefix_keys:
        add(
            LabDeltaCause(
                id="unit_prefix_mistake",
                title="Unit prefix mistake",
                explanation=(
                    "One value is near a 1000x ratio from another. In this lab that "
                    "often points to nF/uF, kOhm/Ohm, or mV/V entry mistakes."
                ),
                confidence="high",
                related_keys=prefix_keys,
                next_check="Check every R and C entry with SI units before changing the model topology.",
            )
        )

    moderate_cutoff_keys = [
        row.id
        for row in rows
        if _is_cutoff_key(row.id)
        and row.percent_difference is not None
        and 5.0 <= row.percent_difference <= 35.0
        and row.id not in ratio_keys
    ]
    if moderate_cutoff_keys:
        add(
            LabDeltaCause(
                id="rc_tolerance_or_loading",
                title="R/C tolerance or source/load impedance",
                explanation=(
                    "The cutoff differs by a moderate amount rather than a clean "
                    "2*pi or 1000x factor. Component tolerance, source impedance, "
                    "capacitor tolerance, and ADC/load impedance are plausible next checks."
                ),
                confidence="medium",
                related_keys=moderate_cutoff_keys,
                next_check="Measure R and C directly, then check whether source or load impedance shifts the pole.",
            )
        )

    notes = (request.notes or "").lower()
    sample_keys = [
        row.id
        for row in rows
        if row.id in {"sample_rate_hz", "attenuation_db", "output_rms_v"}
        and row.percent_difference is not None
        and row.percent_difference > 3.0
    ]
    if sample_keys or any(word in notes for word in ["alias", "nyquist", "sample", "adc"]):
        add(
            LabDeltaCause(
                id="nyquist_or_adc_sampling",
                title="Nyquist, aliasing, or ADC sample-time issue",
                explanation=(
                    "A waveform or sampled-output difference can come from sample rate, "
                    "sample-time alignment, aliasing, or ADC quantization rather than the RC pole alone."
                ),
                confidence="medium",
                related_keys=sample_keys,
                next_check="Probe the analog RC output before the sampler, then compare it with the sampled output.",
            )
        )

    transient_keys = [
        row.id
        for row in rows
        if any(token in row.id for token in ["final", "transient", "settling", "amplitude"])
        and row.percent_difference is not None
        and row.percent_difference > 3.0
    ]
    if transient_keys or any(word in notes for word in ["transient", "settled", "settling", "initial condition"]):
        add(
            LabDeltaCause(
                id="transient_not_settled",
                title="Transient not settled or initial-condition mismatch",
                explanation=(
                    "A transient amplitude or final-value mismatch can occur when the "
                    "simulation stop time, initial condition, or measurement window differs."
                ),
                confidence="medium",
                related_keys=transient_keys,
                next_check="Run long enough for several RC time constants and compare the same time window.",
            )
        )

    if any(word in notes for word in ["clip", "clipping", "rail", "saturat", "output swing"]):
        add(
            LabDeltaCause(
                id="op_amp_output_limit",
                title="Op-amp rail or output swing limit",
                explanation=(
                    "Clipping language in the notes suggests a real output swing limit "
                    "or supply rail issue, which is outside the ideal first RC artifact."
                ),
                confidence="medium",
                related_keys=[],
                next_check="Check supply rails, output swing limits, and whether a buffer stage is saturating.",
            )
        )

    return causes


def _keys_with_ratio_near(
    request: LabDeltaRequest,
    targets: tuple[float, ...],
    *,
    tolerance: float,
) -> list[str]:
    keys = sorted(
        set(request.hand_values)
        | set(request.simulation_values)
        | set(request.measured_values)
    )
    matching: list[str] = []
    for key in keys:
        values = [
            value
            for value in (
                request.hand_values.get(key),
                request.simulation_values.get(key),
                request.measured_values.get(key),
            )
            if value is not None and abs(value) > 1e-30
        ]
        if len(values) < 2:
            continue
        for index, first in enumerate(values):
            for second in values[index + 1 :]:
                ratio = abs(first / second)
                normalized_ratio = max(ratio, 1 / ratio)
                if any(abs(normalized_ratio - target) / target <= tolerance for target in targets):
                    matching.append(key)
                    break
            if key in matching:
                break
    return matching


def _is_cutoff_key(key: str) -> bool:
    lowered = key.lower()
    return "fc" in lowered or "cutoff" in lowered


def _label_for_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _comparison_note(key: str, reference_source: str, compared_source: str) -> str:
    return f"Compared {compared_source} against {reference_source} for {key}."


def _next_probe_suggestion(lab_id: str, causes: list[LabDeltaCause]) -> str:
    cause_ids = {cause.id for cause in causes}
    if "nyquist_or_adc_sampling" in cause_ids:
        return "Probe the RC output before the sampling stage, then compare it with sampled_output."
    if "rad_s_vs_hz" in cause_ids or "unit_prefix_mistake" in cause_ids:
        return "Probe the RC output voltage and verify R, C, fc, and omega_c units before changing topology."
    if lab_id == INSTRUMENTATION_AMP_LAB_ID:
        return "Probe the differential input, common-mode input, and feedback resistor branch."
    return "Start with the Lab Delta measurement point at the RC output."


def _lab_delta_notes(request: LabDeltaRequest) -> list[str]:
    notes = [
        "Lab Delta suggestions are deterministic teaching heuristics, not bench diagnosis.",
        "Compare values only when they refer to the same node, signal, unit, and measurement window.",
    ]
    if request.notes:
        notes.append(f"Student/lab notes considered: {request.notes}")
    return notes


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
