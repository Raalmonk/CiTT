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

## Product Boundary
The selected CLI parsed the circuit image/prompt into a structured model specification. Treat that spec as a starting point, not as numerical authority.
Your job is to build/check the Simulink/Simscape model. Do not write educational prose yet; CiTT will teach after the model exists.

## Simscape-First Requirements
- Build a Simscape-first model from the structured circuit spec.
- Use Simscape and Simscape Electrical physical components when available.
- Use physical electrical connections and component schematics.
- Include Electrical Reference and Solver Configuration blocks as needed.
- Add voltage/current sensors or logging for requested outputs.
- If a source/component value is symbolic or omitted, keep it as a named model parameter instead of inventing a number.
- Values outside the requested/connected teaching path should not block structural model generation.
- Do not use a Simulink signal-flow substitute for the circuit.
- Do not solve with standalone MATLAB numeric code as the model-generation output.
- Do not bypass SATK/model_edit by calling local deterministic Simscape builder functions.
- Treat the supplied spec as build-ready; report an error if a required modeling detail is still missing.

## Required Output Files
- Save the model as `matlab/work/citt_generated_model.slx`.
- Write focus map JSON to `matlab/work/citt_focus_map.json`.
- Write probe map JSON to `matlab/work/citt_probe_map.json`.
- Run model_check or equivalent checks and save notes to `matlab/work/citt_agent_report.md`.

## Focus Map Contract
Each focus map item must include: focus_id, label, explanation, model_paths, block_paths, line_handles_or_descriptions, related_components, related_nodes, teaching_question.

## Probe Map Contract
Each probe map item must include: probe_id, focus_id, label, target_type, model_paths, block_paths, quantity, unit, suggested_sensor_or_logging, instructions.

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
Source: matlab/work/citt_last_circuit_spec.json
```json
{
  "source_path": "submission_assets/benchmark_02_tevc_equilibrium/input_schematic.png",
  "circuit_type": "simplified_two_electrode_voltage_clamp_equilibrium_feedback_model",
  "components": [
    {
      "id": "V_c",
      "type": "voltage_source_command",
      "label": "Vc command",
      "value": "V_c",
      "unit": "V",
      "terminals": [
        "n_vc",
        "n_ref"
      ],
      "confidence": 0.98
    },
    {
      "id": "BUF1",
      "type": "ideal_buffer",
      "label": "Ideal buffer",
      "value": 1,
      "unit": "V/V",
      "terminals": [
        "n_vc",
        "n_buffer_out"
      ],
      "confidence": 0.98
    },
    {
      "id": "AMP1",
      "type": "finite_gain_differential_amplifier",
      "label": "Diff amp A = 100",
      "value": 100,
      "unit": "V/V",
      "terminals": [
        "n_buffer_out",
        "n_feedback_sense",
        "n_amp_out",
        "n_ref"
      ],
      "confidence": 0.98
    },
    {
      "id": "R_o",
      "type": "resistor",
      "label": "Ro 10 Ohm",
      "value": 10,
      "unit": "Ohm",
      "terminals": [
        "n_amp_out",
        "n_vm"
      ],
      "confidence": 0.98
    },
    {
      "id": "R_m",
      "type": "resistor",
      "label": "Membrane Rm = 10 Ohm",
      "value": 10,
      "unit": "Ohm",
      "terminals": [
        "n_vm",
        "n_ref"
      ],
      "confidence": 0.95
    },
    {
      "id": "R_e",
      "type": "resistor",
      "label": "Re feedback voltage electrode resistance",
      "value": "R_e",
      "unit": "Ohm",
      "terminals": [
        "n_vm",
        "n_feedback_sense"
      ],
      "confidence": 0.9
    },
    {
      "id": "VM_PROBE",
      "type": "voltage_probe",
      "label": "probe Vm",
      "value": [],
      "unit": "V",
      "terminals": [
        "n_vm",
        "n_ref"
      ],
      "confidence": 0.98
    },
    {
      "id": "I_CLAMP_PROBE",
      "type": "current_probe",
      "label": "probe clamp current",
      "value": [],
      "unit": "A",
      "terminals": [
        "n_amp_out",
        "n_vm"
      ],
      "confidence": 0.95
    },
    {
      "id": "AMP_OUT_PROBE",
      "type": "voltage_probe",
      "label": "probe amplifier output",
      "value": [],
      "unit": "V",
      "terminals": [
        "n_amp_out",
        "n_ref"
      ],
      "confidence": 0.92
    }
  ],
  "nodes": [
    "n_ref",
    "n_vc",
    "n_buffer_out",
    "n_feedback_sense",
    "n_amp_out",
    "n_vm"
  ],
  "connections": [
    {
      "from": "V_c.positive",
      "to": "BUF1.input",
      "label": "command voltage into ideal buffer",
      "confidence": 0.98
    },
    {
      "from": "BUF1.output",
      "to": "AMP1.noninverting_input",
      "label": "buffered command drives differential amplifier positive input",
      "confidence": 0.98
    },
    {
      "from": "AMP1.output",
      "to": "R_o.terminal1",
      "label": "amplifier output drives output/electrode resistance",
      "confidence": 0.98
    },
    {
      "from": "R_o.terminal2",
      "to": "R_m.terminal1",
      "label": "clamp output connects to membrane voltage node Vm",
      "confidence": 0.95
    },
    {
      "from": "R_m.terminal2",
      "to": "n_ref",
      "label": "passive membrane resistance returns to reference/ground",
      "confidence": 0.86
    },
    {
      "from": "n_vm",
      "to": "R_e.terminal1",
      "label": "Vm sensed by feedback voltage electrode",
      "confidence": 0.92
    },
    {
      "from": "R_e.terminal2",
      "to": "AMP1.inverting_input",
      "label": "feedback voltage returns to differential amplifier negative input",
      "confidence": 0.92
    },
    {
      "from": "VM_PROBE.positive",
      "to": "n_vm",
      "label": "Vm voltage probe positive terminal",
      "confidence": 0.98
    },
    {
      "from": "VM_PROBE.negative",
      "to": "n_ref",
      "label": "Vm voltage probe reference terminal",
      "confidence": 0.98
    },
    {
      "from": "I_CLAMP_PROBE.series",
      "to": "R_o",
      "label": "clamp current probe in series with output path through Ro",
      "confidence": 0.95
    },
    {
      "from": "AMP_OUT_PROBE.positive",
      "to": "n_amp_out",
      "label": "amplifier output voltage probe positive terminal",
      "confidence": 0.92
    },
    {
      "from": "AMP_OUT_PROBE.negative",
      "to": "n_ref",
      "label": "amplifier output voltage probe reference terminal",
      "confidence": 0.92
    }
  ],
  "ground_node": "n_ref",
  "sources": {
    "id": "V_c",
    "type": "command_voltage",
    "label": "Vc command",
    "value": "V_c",
    "unit": "V",
    "positive_node": "n_vc",
    "negative_node": "n_ref",
    "confidence": 0.98
  },
  "requested_outputs": [
    "Vm",
    "amplifier output voltage at n_amp_out",
    "clamp current through Ro",
    "feedback loop highlight"
  ],
  "likely_analysis": "equilibrium_dc_operating_point_or_static_feedback_tracking_analysis",
  "assumptions": [
    "The diagram is a simplified TEVC equilibrium equivalent circuit, not a full axon biophysics model.",
    "Membrane capacitance and ion-channel dynamics are intentionally ignored per prompt and are not build blockers.",
    "Rm is modeled as a passive 10 Ohm membrane resistance from Vm to the reference node.",
    "Ro is modeled as a 10 Ohm series output/electrode resistance between amplifier output and Vm.",
    "The differential amplifier is modeled with finite gain A = 100 using buffered command voltage minus sensed feedback voltage.",
    "Re value is not specified and should be preserved as a named Simscape parameter R_e.",
    "Vc is not numerically specified and should be preserved as a named Simscape parameter V_c.",
    "Clamp current is interpreted as the current through Ro into the membrane node."
  ],
  "ambiguities": [
    "The image does not show an explicit ground symbol; n_ref is inferred as the extracellular/reference node for Vc, amplifier, and membrane resistance.",
    "The exact numerical value of Re is omitted.",
    "The polarity convention for clamp current is not explicitly marked; positive current is assumed from amplifier output through Ro toward Vm.",
    "The feedback electrode connection is drawn conceptually; it is interpreted as Re between Vm and the amplifier inverting input."
  ],
  "unsupported_or_unclear_regions": [],
  "suggested_simscape_blocks": [
    "Simscape Electrical Voltage Source for Vc command",
    "Simscape Electrical Controlled Voltage Source or PS Gain block for ideal buffer",
    "Simscape Electrical Controlled Voltage Source implementing Vout = 100*(Vbuffer - Vfeedback)",
    "Simscape Electrical Resistor for Ro",
    "Simscape Electrical Resistor for Rm",
    "Simscape Electrical Resistor for Re",
    "Electrical Reference",
    "Solver Configuration",
    "Voltage Sensor for Vm",
    "Voltage Sensor for amplifier output",
    "Current Sensor in series with Ro"
  ],
  "focus_points": [
    {
      "id": "fp_feedback_loop",
      "label": "Feedback loop",
      "reason": "Shows how Vm is sensed through Re and fed back to the differential amplifier to drive Vm toward Vc.",
      "related_components": [
        "V_c",
        "BUF1",
        "AMP1",
        "R_o",
        "R_m",
        "R_e"
      ],
      "related_nodes": [
        "n_vc",
        "n_buffer_out",
        "n_feedback_sense",
        "n_amp_out",
        "n_vm"
      ],
      "teaching_question": "What signal does the differential amplifier compare against the buffered command voltage?"
    },
    {
      "id": "fp_vm_probe",
      "label": "Membrane voltage Vm",
      "reason": "Vm is the requested controlled output and the key variable for tracking Vc.",
      "related_components": [
        "R_m",
        "R_o",
        "VM_PROBE"
      ],
      "related_nodes": [
        "n_vm",
        "n_ref"
      ],
      "teaching_question": "Where is Vm measured relative to the reference node in this equivalent circuit?"
    },
    {
      "id": "fp_clamp_current",
      "label": "Clamp current through Ro",
      "reason": "The current through Ro represents the clamp output current needed to hold the membrane voltage.",
      "related_components": [
        "AMP1",
        "R_o",
        "I_CLAMP_PROBE",
        "R_m"
      ],
      "related_nodes": [
        "n_amp_out",
        "n_vm"
      ],
      "teaching_question": "Why must the amplifier output current pass through Ro before reaching the membrane node?"
    },
    {
      "id": "fp_finite_gain_error",
      "label": "Finite amplifier gain",
      "reason": "A finite gain of 100 means the tracking error between command and sensed Vm is not forced exactly to zero.",
      "related_components": [
        "AMP1",
        "R_e",
        "R_m",
        "R_o"
      ],
      "related_nodes": [
        "n_buffer_out",
        "n_feedback_sense",
        "n_amp_out",
        "n_vm"
      ],
      "teaching_question": "How does finite differential gain change the error needed to produce a nonzero clamp output?"
    },
    {
      "id": "fp_electrode_resistance",
      "label": "Voltage electrode resistance Re",
      "reason": "Re is part of the feedback sense path and can affect measured feedback if the sensing input is not perfectly ideal.",
      "related_components": [
        "R_e",
        "AMP1"
      ],
      "related_nodes": [
        "n_vm",
        "n_feedback_sense"
      ],
      "teaching_question": "What assumption would make the voltage drop across Re negligible?"
    }
  ],
  "teaching_focus_points": [
    {
      "id": "fp_feedback_loop",
      "label": "Feedback loop",
      "reason": "Shows how Vm is sensed through Re and fed back to the differential amplifier to drive Vm toward Vc.",
      "related_components": [
        "V_c",
        "BUF1",
        "AMP1",
        "R_o",
        "R_m",
        "R_e"
      ],
      "related_nodes": [
        "n_vc",
        "n_buffer_out",
        "n_feedback_sense",
        "n_amp_out",
        "n_vm"
      ],
      "teaching_question": "What signal does the differential amplifier compare against the buffered command voltage?"
    },
    {
      "id": "fp_vm_probe",
      "label": "Membrane voltage Vm",
      "reason": "Vm is the requested controlled output and the key variable for tracking Vc.",
      "related_components": [
        "R_m",
        "R_o",
        "VM_PROBE"
      ],
      "related_nodes": [
        "n_vm",
        "n_ref"
      ],
      "teaching_question": "Where is Vm measured relative to the reference node in this equivalent circuit?"
    },
    {
      "id": "fp_clamp_current",
      "label": "Clamp current through Ro",
      "reason": "The current through Ro represents the clamp output current needed to hold the membrane voltage.",
      "related_components": [
        "AMP1",
        "R_o",
        "I_CLAMP_PROBE",
        "R_m"
      ],
      "related_nodes": [
        "n_amp_out",
        "n_vm"
      ],
      "teaching_question": "Why must the amplifier output current pass through Ro before reaching the membrane node?"
    },
    {
      "id": "fp_finite_gain_error",
      "label": "Finite amplifier gain",
      "reason": "A finite gain of 100 means the tracking error between command and sensed Vm is not forced exactly to zero.",
      "related_components": [
        "AMP1",
        "R_e",
        "R_m",
        "R_o"
      ],
      "related_nodes": [
        "n_buffer_out",
        "n_feedback_sense",
        "n_amp_out",
        "n_vm"
      ],
      "teaching_question": "How does finite differential gain change the error needed to produce a nonzero clamp output?"
    },
    {
      "id": "fp_electrode_resistance",
      "label": "Voltage electrode resistance Re",
      "reason": "Re is part of the feedback sense path and can affect measured feedback if the sensing input is not perfectly ideal.",
      "related_components": [
        "R_e",
        "AMP1"
      ],
      "related_nodes": [
        "n_vm",
        "n_feedback_sense"
      ],
      "teaching_question": "What assumption would make the voltage drop across Re negligible?"
    }
  ]
}
```
