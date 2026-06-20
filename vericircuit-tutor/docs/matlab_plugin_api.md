# MATLAB Plugin API

CiTT now exposes an additive MATLAB popup tutor contract under `/matlab_plugin`. The API preserves the existing web/API/solver architecture while adding generated MATLAB/Simulink-compatible artifacts for future BME learning labs.

The MATLAB plugin itself should be offline-first. A future `.mltbx` can bundle the generated JSON and artifact files so `citt` opens without a local server. The API is still useful for web preview, development, optional refresh, and CI inspection before MATLAB execution exists.

## Why Preserve The API Without Requiring A Server

The API remains the shared contract and generator surface for:

- The current web preview.
- A future MATLAB App Designer popup launched with `citt` from bundled files.
- A future `.mltbx` toolbox that bundles generated offline artifacts and may optionally fetch API results.
- A future local MATLAB execution adapter.
- A future MCP/agent bridge hidden behind GUI buttons.

The student-facing experience should stay graphical and guided. Generated MATLAB text is an artifact for the popup/toolbox, not a requirement that students hand-write setup code or start a server.

## Endpoints

```text
GET  /matlab_plugin/manifest
GET  /matlab_plugin/labs
POST /matlab_plugin/labs/{lab_id}/artifact
GET  /matlab_plugin/labs/{lab_id}/plan
GET  /matlab_plugin/labs/{lab_id}/adapter_plan
POST /matlab_plugin/labs/{lab_id}/offline_bundle
GET  /matlab_plugin/labs/{lab_id}/focus_map
GET  /matlab_plugin/labs/{lab_id}/probe_plan
POST /matlab_plugin/labs/{lab_id}/lab_delta
POST /matlab_plugin/labs/{lab_id}/lab_delta/parse_upload
```

Implemented labs:

- `rc_antialias_adc`
- `instrumentation_amplifier_intro` as a future-slice stub

## Manifest

Request:

```http
GET /matlab_plugin/manifest
```

Response shape:

```json
{
  "plugin_id": "citt_matlab_popup_tutor",
  "title": "CiTT MATLAB Popup Tutor",
  "tabs": ["overview", "teach", "probe", "lab_delta"],
  "matlab_entrypoint": "citt",
  "default_deployment_mode": "offline_toolbox",
  "local_server_required": false,
  "api_prefix": "/matlab_plugin",
  "ci_boundary": "Generated artifacts, plans, and JSON manifests are testable without MATLAB installed.",
  "labs": [
    {
      "id": "rc_antialias_adc",
      "title": "RC anti-aliasing before ADC",
      "objective": "Connect the hand cutoff calculation to a Simulink-style filter and sampled waveform before an ADC.",
      "generated_artifact_kinds": [
        "matlab_script",
        "simulink_build_script",
        "focus_map_json",
        "probe_plan_json",
        "app_designer_plan",
        "toolbox_manifest"
      ]
    }
  ]
}
```

## Labs

Request:

```http
GET /matlab_plugin/labs
```

The response is the manifest `labs` array. Each lab summary includes inputs, outputs, key parameters, assumptions, idealizations, BME safety boundary, generated artifact kinds, and evidence to collect.

## Artifacts

Request:

```http
POST /matlab_plugin/labs/rc_antialias_adc/artifact
Content-Type: application/json

{
  "kinds": ["matlab_script", "focus_map_json"],
  "include_focus_map": true,
  "include_probe_plan": true,
  "include_app_designer_plan": true
}
```

If `kinds` is omitted, the service returns the default artifact set for the lab.

Response excerpt:

```json
[
  {
    "id": "rc_antialias_adc_matlab_script",
    "lab_id": "rc_antialias_adc",
    "kind": "matlab_script",
    "filename": "citt_rc_antialias_adc.m",
    "requires_matlab_runtime": false,
    "content": "% CiTT generated artifact notice\n% RC anti-aliasing before ADC\n..."
  }
]
```

The RC script includes:

- `fs`, `target_fc`, `R`, and `C`.
- `fc = 1/(2*pi*R*C)`.
- `nyquist = fs/2`.
- ECG-like signal plus 60 Hz interference.
- Simple first-order filter simulation.
- Input, filtered output, and sampled output plots.
- `hand_fc_hz`, `simulated_summary`, and `citt_results`.
- Comments for the Overview, Teach, Probe, and Lab Delta tabs.
- Future highlight comments for `input_path`, `rc_filter`, `sampling_stage`, and `output_signal`.

## Lab Plan

Request:

```http
GET /matlab_plugin/labs/rc_antialias_adc/plan
```

The lab plan is the direct four-tab contract for a popup or MATLAB agent. It contains:

- `lab`: the lab summary from the manifest.
- `overview`: title, objective, inputs, outputs, assumptions, idealizations, safety boundary, artifacts, and evidence.
- `teach_steps`: prompt-before-reveal teaching steps with focus entry IDs, verified value refs, explanations, and common mistakes.
- `focus_map`: typed current-SVG and future-Simulink targets.
- `probe_plan`: deterministic probe/logging/sensor plans.
- `lab_delta_seed_request`: a sample comparison payload for preview and smoke tests.
- `adapter_plan`: dry-run MATLAB agent plan.

Response excerpt:

```json
{
  "lab": {"id": "rc_antialias_adc", "tabs": ["overview", "teach", "probe", "lab_delta"]},
  "teach_steps": [
    {
      "id": "calculate_cutoff",
      "prompt_before_reveal": "Predict whether the cutoff should use R*C or 2*pi*R*C.",
      "focus_entry_ids": ["rc_filter"],
      "verified_value_refs": ["hand_fc_hz", "nyquist"],
      "reveal_policy": "show_hand_check"
    }
  ],
  "adapter_plan": {"mode": "dry_run_contract", "launch_command": "citt"}
}
```

## MATLAB Agent Adapter Plan

Request:

```http
GET /matlab_plugin/labs/rc_antialias_adc/adapter_plan
```

This endpoint resolves the current MATLAB-agent problem without pretending runtime execution exists. It tells a future agent or App Designer adapter:

- What is supported now through the API.
- Which actions are future runtime hooks.
- Which actions would require MATLAB.
- How to refuse unsupported execution claims.
- What CI can validate without MATLAB.

Response excerpt:

```json
{
  "lab_id": "rc_antialias_adc",
  "adapter_id": "matlab_app_designer_adapter_v1",
  "launch_command": "citt",
  "mode": "dry_run_contract",
  "agent_actions": [
    {
      "id": "highlight_focus",
      "action_kind": "highlight_target",
      "requires_matlab_runtime": true,
      "dry_run_note": "Current API returns highlight plans; it must not claim hilite_system ran."
    },
    {
      "id": "compare_lab_delta",
      "action_kind": "compare_lab_delta",
      "requires_matlab_runtime": false,
      "dry_run_note": "This is supported by deterministic Python heuristics."
    }
  ],
  "refusal_rules": [
    "Do not claim that MATLAB, Simulink, Simscape, hilite_system, or .mltbx packaging ran unless a future adapter reports that execution evidence."
  ]
}
```

## Offline Bundle

Request:

```http
POST /matlab_plugin/labs/rc_antialias_adc/offline_bundle
Content-Type: application/json

{
  "kinds": ["matlab_script", "toolbox_manifest"],
  "include_focus_map": false,
  "include_probe_plan": false,
  "include_app_designer_plan": false
}
```

Response shape:

```json
{
  "bundle_id": "citt_rc_antialias_adc_offline_bundle_v1",
  "lab_id": "rc_antialias_adc",
  "requires_matlab_runtime": false,
  "manifest": {"plugin_id": "citt_matlab_popup_tutor"},
  "lab_plan": {"adapter_plan": {"mode": "dry_run_contract"}},
  "artifacts": [],
  "file_tree": [
    "citt.m",
    "+citt/citt.m",
    "+citt/loadOfflineBundle.m",
    "examples/rc_antialias_adc/manifest.json"
  ],
  "integrity_checks": [
    "Bundle contains manifest and lab plan JSON.",
    "Bundle is a dry-run contract and does not require MATLAB runtime in CI."
  ]
}
```

This is not a built `.mltbx`; it is the inspectable package contract that a future toolbox builder can consume. It includes `files` entries such as top-level `citt.m`, `+citt/citt.m`, `+citt/loadOfflineBundle.m`, bundled JSON, and generated artifacts. Those files load local JSON and do not require a local FastAPI server.

## Focus Map

Request:

```http
GET /matlab_plugin/labs/rc_antialias_adc/focus_map
```

Response excerpt:

```json
[
  {
    "id": "rc_filter",
    "tab": "teach",
    "title": "RC filter",
    "teaching_step_id": "calculate_cutoff",
    "target": {
      "id": "rc_filter",
      "label": "R-C low-pass stage",
      "target_type": "block",
      "target_path": "rc_filter",
      "simulink_path": "citt_rc_antialias_adc/RC Filter",
      "svg_id": "R,C"
    },
    "reason": "This is where fc = 1/(2*pi*R*C) becomes a model parameter.",
    "surfaces": ["web_svg", "simulink"],
    "future_simulink_actions": [
      "Highlight the RC subsystem and its parameter annotation."
    ]
  }
]
```

Highlight targets can represent:

- `block`
- `line`
- `port`
- `annotation`
- `svg_component`
- `svg_node`
- `conceptual_path`

This is the bridge from current SVG focus semantics to future Simulink highlight calls such as `hilite_system`. The artifact only describes the plan; it does not execute MATLAB.

The instrumentation-amplifier stub proves the schema can represent future focus targets such as:

- `feedback_loop`
- `gain_setting_resistor`
- `differential_input`
- `common_mode_input`
- `inverting_input`
- `noninverting_input`
- `op_amp_output`
- `feedback_resistor`
- `output_node`

## Probe Plan

Request:

```http
GET /matlab_plugin/labs/rc_antialias_adc/probe_plan
```

Response excerpt:

```json
[
  {
    "id": "rc_output_voltage_probe",
    "title": "Add voltage probe at RC output",
    "student_goal": "Inspect the local signal after the low-pass stage and before sampling.",
    "quantity": "voltage",
    "unit": "V",
    "student_question": "Does the measured output match the cutoff you calculated by hand?",
    "suggested_logging": ["input_signal", "filtered_output"],
    "future_matlab_steps": [
      "Enable signal logging on the RC output line.",
      "Add a scope or logged signal named rc_filter_output."
    ]
  }
]
```

Probe plans describe what a future MATLAB popup should do, including suggested logging and sensor insertion. They do not modify Simulink models in the current MVP.

## Lab Delta

Request:

```http
POST /matlab_plugin/labs/rc_antialias_adc/lab_delta
Content-Type: application/json

{
  "hand_values": {"fc_hz": 40.0},
  "simulation_values": {"fc_hz": 40.1},
  "measured_values": {"fc_hz": 251.3},
  "value_units": {"fc_hz": "Hz"},
  "notes": "Measured value may have been reported as angular frequency."
}
```

Response excerpt:

```json
{
  "lab_id": "rc_antialias_adc",
  "comparison_rows": [
    {
      "id": "fc_hz",
      "label": "Fc Hz",
      "unit": "Hz",
      "hand_value": 40.0,
      "simulation_value": 40.1,
      "measured_value": 251.3,
      "reference_source": "hand",
      "compared_source": "measured",
      "absolute_difference": 211.3,
      "percent_difference": 528.25
    }
  ],
  "likely_causes": [
    {
      "id": "rad_s_vs_hz",
      "title": "rad/s vs Hz confusion",
      "confidence": "high",
      "next_check": "Recalculate cutoff using fc = 1/(2*pi*R*C) in Hz and compare with omega_c = 1/(R*C) in rad/s."
    }
  ],
  "next_probe_suggestion": "Probe the RC output voltage and verify R, C, fc, and omega_c units before changing topology.",
  "reflection_question": "Which single assumption would you test first, and what measurement would make that assumption visible?"
}
```

Lab Delta currently uses deterministic educational heuristics:

- Near `2*pi` ratio: rad/s vs Hz or missing `2*pi`.
- Near `1000x` ratio: unit prefix mistake such as nF/uF or kOhm/Ohm.
- Moderate cutoff mismatch: R/C tolerance or source/load impedance.
- Sampling or waveform mismatch: Nyquist, aliasing, ADC sample-time issue, or quantization.
- Transient/final-value mismatch: initial conditions, stop time, or unsettled transient.
- Clipping notes: op-amp rail or output swing limits.

These are tutor suggestions, not bench diagnosis or biomedical design verification.

## Lab Delta Upload Parsing

Request:

```http
POST /matlab_plugin/labs/rc_antialias_adc/lab_delta/parse_upload
Content-Type: application/json

{
  "format": "csv",
  "content": "source,key,value,unit\nhand,fc_hz,40,Hz\nsimulation,fc_hz,40.1,Hz\nmeasured,fc_hz,251.3,Hz\n"
}
```

Supported text formats:

- `csv`
- `tsv`
- `json`
- `auto`

CSV/TSV rows use:

```text
source,key,value,unit,note
hand,fc_hz,40,Hz,
simulation,fc_hz,40.1,Hz,
measured,fc_hz,251.3,Hz,reported from scope cursor
```

JSON may be either a normal `LabDeltaRequest` object or a row list. The endpoint returns both the parsed request and the deterministic Lab Delta response:

```json
{
  "lab_id": "rc_antialias_adc",
  "parsed_request": {
    "hand_values": {"fc_hz": 40.0},
    "simulation_values": {"fc_hz": 40.1},
    "measured_values": {"fc_hz": 251.3},
    "value_units": {"fc_hz": "Hz"}
  },
  "lab_delta_response": {
    "likely_causes": [{"id": "rad_s_vs_hz"}]
  },
  "warnings": []
}
```

This is text parsing only. It does not persist files, execute MATLAB, or certify lab measurements.

## Future MATLAB Popup Consumption

A MATLAB App Designer popup can call:

1. `/matlab_plugin/manifest` to populate tabs and lab choices.
2. `/matlab_plugin/labs/{lab_id}/artifact` to fetch generated MATLAB/Simulink plans.
3. `/matlab_plugin/labs/{lab_id}/focus_map` to map lesson steps to model highlights.
4. `/matlab_plugin/labs/{lab_id}/probe_plan` to present guided probe buttons.
5. `/matlab_plugin/labs/{lab_id}/lab_delta` after the student enters or uploads measured values.

The popup can then render four tabs:

- Overview: lab summary, assumptions, parameters, safety boundary, evidence checklist.
- Teach: lesson steps and highlight targets.
- Probe: suggested logging/sensors and measurement questions.
- Lab Delta: comparison table, likely causes, next check, reflection question.

## Current Web Preview

The React workspace includes a lightweight `Plugin` panel that consumes the same API:

- Manifest tabs and lab summaries.
- Generated artifact filenames and MATLAB script excerpt.
- Teach steps from the four-tab lab plan.
- Adapter action steps and dry-run refusal boundaries.
- Offline bundle file-tree and integrity checks.
- Focus-map entries for current SVG and future Simulink targets.
- Probe-plan entries.
- A deterministic Lab Delta preview response.

This preview is intentionally small. It validates the shared API contract without replacing the existing Learn, Coach, Inspect, Lab, or Scope panels.

## Future Toolbox Packaging

A future `.mltbx` package can bundle:

```text
citt.m
+citt/
templates/
examples/
docs/
app/
```

The toolbox can either call the API or include offline generated artifacts. Live MATLAB execution, Simulink model mutation, `hilite_system`, and packaging are future adapter work.

## Runtime Work Not Implemented Yet

- Live MATLAB execution.
- Live Simulink model creation or mutation.
- Simscape sensor insertion.
- `hilite_system` calls.
- `.mltbx` packaging.
- Persistent student or lab sessions.
- Full device-level biomedical safety verification.

The API now represents the first five items as explicit adapter or bundle plans and supports text-based Lab Delta upload parsing. The offline bundle path is the MATLAB plugin default; the API server is optional for development, web preview, and refresh. It still does not execute MATLAB or persist lab sessions.
