# CiTT Simscape Model Build Task

You are operating inside MATLAB/Simulink with Simulink Agentic Toolkit.
This task is self-contained. Do not read external agent skill files, do not invoke subagents, and do not use shell tools.
Use the available MATLAB MCP tools to inspect, build, edit, and check the model.
When running in an external agent CLI, use the actual registered tool names: mcp_matlab_model_overview, mcp_matlab_model_read, mcp_matlab_model_edit, mcp_matlab_model_check, mcp_matlab_model_query_params, and mcp_matlab_model_resolve_params.
Use mcp_matlab_evaluate_matlab_code only for required artifact file writes or MATLAB checks that have no dedicated MCP tool; do not use it to bypass mcp_matlab_model_edit for structural model construction.
If your runtime exposes unprefixed aliases, the equivalent aliases are model_overview, model_read, model_edit, model_check, model_query_params, and model_resolve_params.
The structured circuit spec is embedded below; do not read the Source file path.

## External Agent Guardrails
- Do not call read_file for /Users/Raalm/.agents/skills or other external skill paths.
- Do not call run_shell_command; it is not available in this CiTT agent runner.
- Do not call invoke_agent or delegate to another agent.
- If the target model does not exist yet, create it with mcp_matlab_model_edit; do not treat an initial model_overview/model_read failure as permission to bypass SATK.
- Do not call local CiTT model-construction helpers or generate a model through raw MATLAB scripts.
- Do not write or run citt_build_simscape_model.m as the model-generation mechanism.
- If mcp_matlab_model_edit cannot create/edit the model, write an agent report explaining the SATK/MCP failure instead of producing model artifacts.

## Repo-Local SATK Agent Instructions
CiTT has vendored the Simulink Agentic Toolkit agent instructions into the repository. Use the embedded copy below; do not read external skill directories.
Local reference directory: `/Users/Raalm/Documents/GitHub/CiTT/matlab/resources/agent_instructions/simulink_agentic_toolkit`
CiTT addendum copy: `/Users/Raalm/Documents/GitHub/CiTT/matlab/resources/agent_instructions/simulink_agentic_toolkit/CITT_AGENTS.md`
Tool registry copy: `/Users/Raalm/Documents/GitHub/CiTT/matlab/resources/agent_instructions/simulink_agentic_toolkit/tools/registry.json`
Tool metadata copy: `/Users/Raalm/Documents/GitHub/CiTT/matlab/resources/agent_instructions/simulink_agentic_toolkit/tools/tools.json`

```markdown
<!-- Copyright 2026 The MathWorks, Inc. -->

# Simulink Agentic Toolkit — Agent Instructions

## Setup

If the user asks to set up the Simulink Agentic Toolkit, direct them to run the following in MATLAB:

```matlab
addpath('<path-to-setup-folder>')
setupAgenticToolkit("install")
```

This handles platform detection, MCP server download, toolkit installation, agent configuration, and skill registration. Do not attempt to run setup commands on the user's behalf.

## Domain Skills

Simulink domain skills are in `skills-catalog/model-based-design-core/`. Each skill has a `SKILL.md` with instructions and a `manifest.yaml` with metadata.

## MCP Tools

Seven MCP tools are available when the MCP server is connected (see `tools/registry.json`):
- `model_overview` — hierarchical model visualization
- `model_read` — block topology and expression notation
- `model_edit` — structural modifications
- `model_check` — structural validation (unconnected ports, dangling lines, Edit-Time Checks on States and Subcharts)
- `model_query_params` — random access to parameters
- `model_resolve_params` — resolve workspace variables
- `model_test` — Gherkin-based behavioral testing (requires Simulink Test)

## MATLAB Prerequisite

The MCP server uses `--matlab-session-mode=existing`. MATLAB must be running with `satk_initialize` executed (which calls `shareMATLABSession`) before MCP tools will work. The MATLAB MCP Server Toolbox must be installed once per MATLAB version. If tools fail to connect, guide the user to run `addpath('<toolkit_root>'); satk_initialize` in MATLAB.

```

```markdown
# CiTT-specific SATK agent addendum

These instructions specialize the repo-local Simulink Agentic Toolkit guidance for CiTT model-building tasks.

## Non-negotiable execution boundary

- Use the user-selected CLI command that launched the task. Do not switch providers or invoke an alternate CLI.
- Do not read external skill directories such as `/Users/Raalm/.agents/skills`, `/Users/Raalm/.codex/skills`, or provider-specific global config folders.
- Do not invoke subagents, shell tools, or local CiTT deterministic builders.
- Build through SATK/MCP model tools. If `model_edit` cannot create or edit the model, write an agent report explaining the SATK/MCP failure instead of producing substitute artifacts.

## Simscape-first modeling contract

- Build the physical path with Simscape/Simscape Electrical blocks whenever a physical component or node is present.
- Use physical `portName <-> portName` connections for electrical/physical networks.
- Include Solver Configuration and domain reference blocks for each physical network.
- Use controlled Simulink blocks only at explicit educational boundaries, such as PK input generation, ADC code calculation, or a documented wrapper around a physical sensor path.
- Keep omitted or symbolic component values as named model parameters; do not invent hidden numbers.
- Use `model_query_params` and `model_resolve_params` to inspect or resolve parameters before making numeric claims.
- Add voltage/current sensors and PS-Simulink Converter blocks for every requested measurable electrical output.
- Add logging blocks or outports so CiTT can measure outputs without visually inspecting the diagram.

## Focus and probe map contract

- Focus map entries must point to real model/block paths that can be highlighted.
- Probe map entries must identify the physical sensor/logging path, quantity, unit, and student-safe measurement instruction.
- Teaching questions should be plain text by default.
- If LaTeX is necessary, keep it short, balanced, and simple: inline `$...$` only, no custom commands, no environments, no raw HTML.
- Never emit malformed LaTeX in focus/probe maps. Prefer `Rf = 1 MOhm` over fragile formula markup.

## 14-inch UI and student usability

- CiTT is a teaching tool first. Keep the learning experience simple, clear, and focused on the current concept.
- The student should see the relevant model evidence, the current question, the key facts needed to answer it, and one obvious next action.
- Do not design focus/probe content that requires the student to inspect hidden files or cross-reference separate artifacts.
- Do not require the student to cross-reference hidden parameters. Put key values in component labels, focus-map explanations, or probe-map instructions.
- Prefer concise labels that fit in the learning UI.
- The model should remain readable when shown above the learning prompt on a 14-inch laptop screen.
- Teaching steps should support local model crops. Put the most relevant block paths first, and keep focus entries small enough that a cropped snapshot is readable.
- Avoid long block names and labels when a concise engineering label with units is enough.

## QA and visual acceptance requirements

- A command passing is not enough for UI work. Verify rendered screenshots or computer-vision output when changing model previews, LaTeX, teaching cards, or layout.
- Reject model preview snapshots that are mostly blank canvas, shifted into a corner, clipped, or too zoomed out to read labels.
- Check the actual current teaching focus, not only the whole model. If the full diagram is too wide, the teaching surface should show a relevant local region.
- Keep the teaching action surface small: no more than three visible primary controls; secondary actions belong behind a `+` menu.
- Bad or overly complex LaTeX must degrade to plain text. Prefer plain text in focus/probe maps unless short inline math materially improves the lesson.
- Treat user screenshots as QA evidence. If the screenshot is not readable on a 14-inch-class screen, the change is not done.

```

## SATK Project Library Policy
CiTT project root: `/Users/Raalm/Documents/GitHub/CiTT`

CiTT has no custom teaching block library configured for this release.
The SATK library gate should be satisfied by `.satk/reuse-libraries.json` with `confirmedNone=true`.
Do not stop to ask about reusable libraries for this build.
Use built-in MATLAB, Simulink, Simscape, and Simscape Electrical blocks unless the user later configures a CiTT teaching library.

Preset status:
- Saved SATK library config with confirmedNone=true via library.LibraryConfig.save.

## Simscape Utilization Contract
- Before editing, inspect the model with model_overview/model_read when a model already exists.
- For physical networks, use Simscape or Simscape Electrical library blocks rather than pure Simulink substitutes.
- Include Solver Configuration and domain reference blocks for every physical network.
- Preserve unit-bearing parameters and named workspace variables; resolve them with model_query_params/model_resolve_params when needed.
- Log requested outputs through sensors, PS-Simulink converters, To Workspace blocks, scopes, or outports.
- Run model_check after structural edits and report any unresolved unconnected ports, dangling lines, or lint failures.
- Write focus/probe maps that prove which physical blocks, sensors, and logged outputs support the lesson.

## Signal-Level Teaching/Test Interface Contract
- Keep the physical circuit in a subsystem named `CiTT_PhysicalCircuit` when practical.
- Add a signal-level wrapper subsystem named `CiTT_TestInterface` when the model includes Simscape physical ports or when CiTT model tests are expected.
- `CiTT_TestInterface` should expose standard Simulink Inport/Outport signals such as `Vin` and `Vout`.
- Inside the wrapper, use Simulink-PS Converter blocks to drive physical sources and sensor + PS-Simulink Converter blocks to expose measurements.
- Do not run behavioral model tests directly against Simscape physical modeling ports; test the signal-based wrapper.
- Add wrapper paths and measurement outputs to the probe map when they support the lesson.

## Stateflow Teaching Logic Contract
If the circuit spec includes ADC logic, threshold detection, artifact detection, mode switching, digital control, or state-dependent behavior:
- Use Stateflow for explicit decision/state logic when it is clearer than ad hoc Simulink switch blocks.
- Keep analog and physical behavior in Simscape.
- Expose Stateflow state or decision outputs through named Simulink signals when they are part of requested teaching or probe evidence.
- Add Stateflow chart paths and state names to the focus map when they support a teaching question.
- Add probe entries for ADC code, threshold decision, mode state, or artifact-detected signals when requested.
- Run model_check with stateflow_lint after chart editing.

## Product Boundary
The selected CLI parsed the circuit image/prompt into a structured model specification. Treat that spec as a starting point, not as numerical authority.
Your job is to build/check the Simulink/Simscape model. Do not write educational prose yet; CiTT will teach after the model exists.

## Simscape-First Requirements
- Build a Simscape-first model from the structured circuit spec.
- Use Simscape and Simscape Electrical physical components when available.
- Use physical electrical connections and component schematics.
- Include Electrical Reference and Solver Configuration blocks as needed.
- Add voltage/current sensors or logging for requested outputs.
- Route physical measurements through sensors and PS-Simulink Converter blocks before logging or ADC/math blocks.
- If model_test may be used, add a signal-level subsystem named CiTT_TestInterface with Simulink Inport/Outport blocks around the physical network.
- Use model_query_params and model_resolve_params for symbolic or workspace parameters before making numeric claims.
- If a source/component value is symbolic or omitted, keep it as a named model parameter instead of inventing a number.
- Values outside the requested/connected teaching path should not block structural model generation.
- Do not use a Simulink signal-flow substitute for the circuit.
- Do not solve with standalone MATLAB numeric code as the model-generation output.
- Do not bypass SATK/model_edit by calling local deterministic builder functions.
- Treat the supplied spec as build-ready; report an error if a required modeling detail is still missing.

## Required Output Files
- Save the model as `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_generated_model.slx`.
- Write focus map JSON to `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_focus_map.json`.
- Write probe map JSON to `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_probe_map.json`.
- Run model_check or equivalent checks and save notes to `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_report.md`.

## Focus Map Contract
Each focus map item must include: focus_id, label, explanation, model_paths, block_paths, line_handles_or_descriptions, related_components, related_nodes, teaching_question.
Keep focus-map text LaTeX-safe. Prefer plain text; if math is needed, use only short balanced inline `$...$` expressions.

## Probe Map Contract
Each probe map item must include: probe_id, focus_id, label, target_type, model_paths, block_paths, quantity, unit, suggested_sensor_or_logging, instructions.
Probe instructions must include the physical sensor/logging path and unit. Prefer plain text over LaTeX.

## Nonideal Device Profiles
No recognized part-number profile was detected. If the spec names a real op-amp part, preserve its nonideal behavior rather than silently replacing it with an ideal op-amp.

## Additional CiTT Prompt
Build the model as the engineering playground for CiTT.

Operate inside MATLAB/Simulink with Simulink Agentic Toolkit when available. This task is self-contained; do not read external agent skill files, do not invoke subagents, and do not use shell tools.

Prefer MATLAB MCP/SATK tools for model inspection and edits. In external agent CLIs, the registered tool names are usually mcp_matlab_model_overview, mcp_matlab_model_read, mcp_matlab_model_edit, mcp_matlab_model_check, mcp_matlab_model_query_params, and mcp_matlab_model_resolve_params. If your runtime exposes unprefixed aliases, the equivalent aliases are model_overview, model_read, model_edit, model_check, model_query_params, and model_resolve_params. Use mcp_matlab_evaluate_matlab_code only for required artifact file writes or MATLAB checks that have no dedicated MCP tool; do not use it to bypass model_edit for structural model construction.

Modeling rules:
- Build a Simscape-first model.
- Use Simscape Electrical blocks for sources, resistors, capacitors, inductors, op amps, sensors, and references when available.
- If the spec names a real op-amp part such as LM741/UA741, do not replace it with an ideal op-amp without modeling or documenting nonidealities. Add explicit Simscape elements for input bias current, input offset voltage, finite input resistance, finite open-loop gain, output swing, and slew-rate/bandwidth when relevant to the requested output.
- For LM741-like voltage followers, represent input bias current as small DC current sources at the op-amp inputs and add a focus/probe note explaining the V_error = I_bias * R_source mechanism.
- Include Electrical Reference and Solver Configuration blocks.
- Use physical connections so the model remains schematic-like.
- Add sensors or logging for every requested output.
- Save the model to the exact path requested by the task.
- Write focus and probe maps with model/block paths that CiTT can use for hilite_system and open_system.
- Run checks before finishing and record unresolved issues.
- Do not write a standalone MATLAB numeric script as the model-generation output.
- Do not call local CiTT model-construction helpers or generate a model through raw MATLAB scripts.
- Do not write or run citt_build_simscape_model.m as the model-generation mechanism.
- If mcp_matlab_model_edit cannot create/edit the model, write an agent report explaining the SATK/MCP failure instead of producing model artifacts.
- Do not write educational prose; CiTT will build the teaching plan after the model exists.
- Do not call read_file for /Users/Raalm/.agents/skills or other external skill paths.
- Do not call run_shell_command; it is not available in this CiTT agent runner.


## Structured Circuit Spec
Source: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/test_citt_parse_spec.json
```json
{
  "circuit_type": "rc_low_pass",
  "components": [
    {
      "id": "V1",
      "type": "voltage_source",
      "label": "Vin",
      "value": 1,
      "unit": "V",
      "terminals": [
        "n_in",
        "0"
      ],
      "confidence": 1
    },
    {
      "id": "R1",
      "type": "resistor",
      "label": "R1",
      "value": 1000,
      "unit": "ohm",
      "terminals": [
        "n_in",
        "n_out"
      ],
      "confidence": 1
    },
    {
      "id": "C1",
      "type": "capacitor",
      "label": "C1",
      "value": 1E-6,
      "unit": "F",
      "terminals": [
        "n_out",
        "0"
      ],
      "confidence": 1
    }
  ],
  "nodes": [
    "n_in",
    "n_out",
    "0"
  ],
  "connections": [
    {
      "from": "V1.positive",
      "to": "R1.left",
      "label": "n_in",
      "confidence": 1
    },
    {
      "from": "R1.right",
      "to": "C1.top",
      "label": "n_out",
      "confidence": 1
    },
    {
      "from": "V1.negative",
      "to": "C1.bottom",
      "label": "0",
      "confidence": 1
    }
  ],
  "ground_node": "0",
  "sources": "V1",
  "requested_outputs": "V(n_out)",
  "likely_analysis": "transient_or_ac",
  "assumptions": [
    "Ideal source",
    "Nominal component values"
  ],
  "ambiguities": [],
  "unsupported_or_unclear_regions": [],
  "suggested_simscape_blocks": [
    "Resistor",
    "Capacitor",
    "Electrical Reference",
    "Solver Configuration",
    "Voltage Sensor"
  ],
  "focus_points": {
    "id": "rc_output",
    "label": "RC output node",
    "reason": "Output node sets the measured low-pass response.",
    "related_components": [
      "R1",
      "C1"
    ],
    "related_nodes": "n_out",
    "teaching_question": "Why is n_out the natural probe point?"
  },
  "teaching_focus_points": {
    "id": "rc_output",
    "label": "RC output node",
    "reason": "Output node sets the measured low-pass response.",
    "related_components": [
      "R1",
      "C1"
    ],
    "related_nodes": "n_out",
    "teaching_question": "Why is n_out the natural probe point?"
  }
}
```