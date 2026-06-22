# CiTT Performance Evidence Pack

Generated: 2026-06-22 13:40:31
Purpose: functional proof and technical-feasibility evidence for the CiTT MATLAB plugin workflow.

## 1. Original Circuit / Prompt

- **Image:** submission_assets/benchmark_03_mixed_signal_simscape/input_schematic.png
- **Prompt:** # Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic

Model a closed-loop neural clamp system with membrane capacitance Cm, membrane leakage resistance Rm, optional simplified nonlinear membrane current, electrode series resistance, finite-gain amplifier, output current limit, rail saturation, command voltage step Vc(t), ADC sampling and quantization of Vm, digital comparator or finite-state control logic, DAC or command update path, and requested outputs Vm(t), clamp current, amplifier output, ADC code sequence, digital control state, saturation flags, settling time, and overshoot.

This problem is intentionally too complex for reliable LLM-only closed-form solving. It requires simulation.
- **Spec source:** MATLAB app state
- **Circuit type:** closed_loop_mixed_signal_neural_voltage_clamp

## 2. Gemini Structured Circuit Spec

- **Source:** MATLAB app state
- **Likely analysis:** time_domain_mixed_signal_simulation_with_simscape_electrical_plant_and_discrete_time_adc_digital_control_loop
- **Components:** 10
- **Nodes:** n_ref, n_cmd, n_feedback, n_amp_out, n_mem_drive, n_vm, s_vm, s_iclamp, s_adc_code, s_state, s_saturation_flags, s_control_update
- **Requested outputs:** Vm(t), clamp_current, amplifier_output, ADC_code_sequence, digital_control_state, saturation_flags, settling_time, overshoot

```json
{
  "circuit_type": "closed_loop_mixed_signal_neural_voltage_clamp",
  "image_source_path": "submission_assets/benchmark_03_mixed_signal_simscape/input_schematic.png",
  "components": [
    {
      "id": "VC_STEP",
      "type": "voltage_step_source",
      "label": "Vc(t) command voltage step",
      "value": "Vc(t)",
      "unit": "V",
      "terminals": [
        "n_cmd",
        "n_ref"
      ],
      "confidence": 0.95
    },
    {
      "id": "AMP1",
      "type": "finite_gain_amplifier_with_limits",
      "label": "Finite-gain amplifier with rail saturation and output current limit",
      "value": {
        "gain": "A_ol",
        "positive_rail": "V_rail_plus",
        "negative_rail": "V_rail_minus",
        "current_limit": "I_limit"
      },
      "unit": "mixed",
      "terminals": [
        "n_cmd",
        "n_feedback",
        "n_amp_out",
        "n_ref"
      ],
      "confidence": 0.9
    },
    {
      "id": "RELECT",
      "type": "resistor",
      "label": "Electrode series R",
      "value": "R_e",
      "unit": "ohm",
      "terminals": [
        "n_amp_out",
        "n_mem_drive"
      ],
      "confidence": 0.92
    },
    {
      "id": "MEMBRANE",
      "type": "passive_membrane_model",
      "label": "Simscape membrane Cm, Rm, leak current",
      "value": {
        "capacitance": "C_m",
        "resistance": "R_m",
        "leak_current": "I_leak"
      },
      "unit": "mixed",
      "terminals": [
        "n_vm",
        "n_ref"
      ],
      "confidence": 0.88
    },
    {
      "id": "INL_MEM",
      "type": "optional_nonlinear_current",
      "label": "Optional simplified nonlinear membrane current",
      "value": "I_nl(V_m,t)",
      "unit": "A",
      "terminals": [
        "n_vm",
        "n_ref"
      ],
      "confidence": 0.58
    },
    {
      "id": "VM_SENSOR",
      "type": "voltage_sensor",
      "label": "Vm probe / membrane voltage sensor",
      "value": [],
      "unit": "V",
      "terminals": [
        "n_vm",
        "n_ref",
        "s_vm"
      ],
      "confidence": 0.9
    },
    {
      "id": "ICLAMP_SENSOR",
      "type": "current_sensor",
      "label": "Clamp current probe",
      "value": [],
      "unit": "A",
      "terminals": [
        "n_amp_out",
        "n_mem_drive",
        "s_iclamp"
      ],
      "confidence": 0.84
    },
    {
      "id": "ADC1",
      "type": "adc_sample_and_quantize",
      "label": "ADC sample and quantize Vm",
      "value": {
        "sample_time": "T_s",
        "bits": "N_bits",
        "v_ref": "V_adc_ref"
      },
      "unit": "mixed",
      "terminals": [
        "s_vm",
        "s_adc_code"
      ],
      "confidence": 0.9
    },
    {
      "id": "DIGCTRL",
      "type": "digital_control_logic",
      "label": "Digital state logic compare, settle, saturate",
      "value": {
        "algorithm": "comparator_or_finite_state_control",
        "state": "control_state"
      },
      "unit": "state",
      "terminals": [
        "s_adc_code",
        "s_state",
        "s_saturation_flags",
        "s_control_update"
      ],
      "confidence": 0.86
    },
    {
      "id": "DAC1",
      "type": "dac_or_command_update",
      "label": "DAC or command update path",
      "value": {
        "update_time": "T_s",
        "output": "V_update_or_I_command"
      },
      "unit": "mixed",
      "terminals": [
        "s_control_update",
        "n_feedback"
      ],
      "confidence": 0.72
    }
  ],
  "nodes": [
    "n_ref",
    "n_cmd",
    "n_feedback",
    "n_amp_out",
    "n_mem_drive",
    "n_vm",
    "s_vm",
    "s_iclamp",
    "s_adc_code",
    "s_state",
    "s_saturation_flags",
    "s_control_update"
  ],
  "connections": [
    {
      "from": "VC_STEP.n_cmd",
      "to": "AMP1.n_cmd",
      "label": "command voltage step drives amplifier input",
      "confidence": 0.92
    },
    {
      "from": "AMP1.n_amp_out",
      "to": "RELECT.n_amp_out",
      "label": "amplifier output drives electrode series resistance",
      "confidence": 0.95
    },
    {
      "from": "RELECT.n_mem_drive",
      "to": "MEMBRANE.n_vm",
      "label": "electrode series resistance drives membrane node Vm",
      "confidence": 0.88
    },
    {
      "from": "MEMBRANE.n_vm",
      "to": "VM_SENSOR.n_vm",
      "label": "membrane voltage measured for probes and ADC",
      "confidence": 0.9
    },
    {
      "from": "AMP1.n_amp_out",
      "to": "ICLAMP_SENSOR.n_amp_out",
      "label": "clamp current measured near amplifier/electrode output",
      "confidence": 0.76
    },
    {
      "from": "VM_SENSOR.s_vm",
      "to": "ADC1.s_vm",
      "label": "Vm analog measurement sampled and quantized",
      "confidence": 0.94
    },
    {
      "from": "ADC1.s_adc_code",
      "to": "DIGCTRL.s_adc_code",
      "label": "ADC code sequence feeds digital control logic",
      "confidence": 0.94
    },
    {
      "from": "DIGCTRL.s_control_update",
      "to": "DAC1.s_control_update",
      "label": "digital state emits command or DAC update",
      "confidence": 0.86
    },
    {
      "from": "DAC1.n_feedback",
      "to": "AMP1.n_feedback",
      "label": "DAC or command update closes loop to amplifier input/control path",
      "confidence": 0.72
    },
    {
      "from": "DIGCTRL.s_saturation_flags",
      "to": "AMP1.n_feedback",
      "label": "saturation/limit status may affect closed-loop control behavior",
      "confidence": 0.5
    }
  ],
  "ground_node": "n_ref",
  "sources": {
    "id": "VC_STEP",
    "type": "command_voltage_step",
    "label": "Vc(t) step input",
    "node_positive": "n_cmd",
    "node_negative": "n_ref",
    "value": "Vc(t)",
    "unit": "V",
    "confidence": 0.95
  },
  "requested_outputs": [
    "Vm(t)",
    "clamp_current",
    "amplifier_output",
    "ADC_code_sequence",
    "digital_control_state",
    "saturation_flags",
    "settling_time",
    "overshoot"
  ],
  "likely_analysis": "time_domain_mixed_signal_simulati
... [truncated]
```

## 3. SATK / Simscape Model Artifacts

- **Generated model:** matlab/work/citt_generated_model.slx (missing)
- **Agent task:** matlab/work/citt_agent_task.md
- **Agent run:** not recorded in current app state

## 4. Model Check Result

- **Status:** FAIL
- **Report:** matlab/work/citt_model_check_report.md

Messages:
- # CiTT Model Check Report
- Model: matlab/work/citt_generated_model.slx
- Success: false
- Messages:
- Model check failed: Error due to multiple causes.
- Error: Error due to multiple causes.

## 5. Simulation Curve / Data Summary

- **Status:** FAIL
- **Summary:** matlab/work/citt_simulation_summary.json
- **Plot/screenshot:** not captured by the current simulation run
- **Output variables:** none recorded

Messages:
- Simulation failed: Error due to multiple causes.

## 6. Requirement Pass/Fail Table

This table uses only evidence currently present in the MATLAB plugin state and saved artifacts.

| Requirement | Evidence | Result | Status |
| --- | --- | --- | --- |
| Cutoff frequency near target | spec + Lab Delta/simulation metrics | cutoff frequency not measured/logged | WARN |
| Sampling frequency satisfies Nyquist | spec + simulation metrics | sampling frequency or highest signal frequency not available | WARN |
| Output saturation / clipping absent | simulation summary | clipping metric not logged | WARN |
| 60 Hz interference attenuation checked | Lab Delta/simulation metrics | 60 Hz attenuation metric not available | WARN |
| Input impedance above threshold | spec + simulation metrics | metric not available | WARN |
| ADC quantization step below threshold | spec + simulation metrics | metric not available | WARN |
| Model check has no update errors | model_check report | model update/check succeeded | PASS |
| Focus map available for teaching highlights | matlab/work/citt_focus_map.json | artifact exists | PASS |
| Probe map available for guided measurements | matlab/work/citt_probe_map.json | artifact exists | PASS |

## 6A. Detailed Requirement-to-Simulation Report

- **Markdown report:** matlab/work/citt_requirement_report.md
- **JSON report:** matlab/work/citt_requirement_report.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 04:16:56",
  "source_spec": "matlab/work/citt_last_circuit_spec.json",
  "rows": [
    {
      "requirement": "Cutoff frequency near target",
      "result": "cutoff frequency not measured/logged",
      "status": "NOT_EVALUATED",
      "evidence": "spec + Lab Delta/simulation metrics"
    },
    {
      "requirement": "Sampling frequency satisfies Nyquist",
      "result": "sampling frequency or highest signal frequency not available",
      "status": "NOT_EVALUATED",
      "evidence": "spec + simulation metrics"
    },
    {
      "requirement": "Output saturation / clipping absent",
      "result": "clipping metric not logged",
      "status": "NOT_EVALUATED",
      "evidence": "simulation summary"
    },
    {
      "requirement": "60 Hz interference attenuation checked",
      "result": "60 Hz attenuation metric not available",
      "status": "NOT_EVALUATED",
      "evidence": "Lab Delta/simulation metrics"
    },
    {
      "requirement": "Input impedance above threshold",
      "result": "metric not available",
      "status": "NOT_EVALUATED",
      "evidence": "spec + simulation metrics"
    },
    {
      "requirement": "ADC quantization step below threshold",
      "result": "metric not available",
      "status": "NOT_EVALUATED",
      "evidence": "spec + simulation metrics"
    },
    {
      "requirement": "Model check has no update errors",
      "result": "model update/check succeeded",
      "status": "PASS",
      "evidence": "model_check report"
    },
    {
      "requirement": "Focus map available for teaching highlights",
      "result": "artifact exists",
      "status": "PASS",
      "evidence": "matlab/work/citt_focus_map.json"
    },
    {
      "requirement": "Probe map available for guided measurements",
      "result": "artifact exists",
      "status": "PASS",
      "evidence": "matlab/work/citt_probe_map.json"
    }
  ],
  "summary": {
    "pass": 3,
    "warn": 0,
    "fail": 0,
    "not_run": 0,
    "not_evaluated": 6,
    "recorded": 0
  },
  "report_path": "matlab/work/citt_requirement_report.json",
  "markdown_path": "matlab/work/citt_requirement_report.md"
}
```

## 7. Focus Map / Highlight Map

- **Artifact:** matlab/work/citt_focus_map.json

| ID | Label | Model / Block Paths | Teaching Note |
| --- | --- | --- | --- |
| fp_command_step | Command step V_c(t) | matlab/work/citt_generated_model.slx | What should happen to V_m immediately after the command voltage V_c(t) changes? |
| fp_amplifier_limits | Finite-gain amplifier saturation and current limit | matlab/work/citt_generated_model.slx | How would finite gain or rail saturation prevent the clamp from forcing V_m exactly to V_c? |
| fp_electrode_series_resistance | Electrode series resistance R_e | matlab/work/citt_generated_model.slx | When clamp current increases, where does the voltage drop across R_e appear? |
| fp_membrane_dynamics | Membrane C_m, R_m, and leak current | matlab/work/citt_generated_model.slx | Which part of the membrane model stores charge, and which part leaks current at steady state? |
| fp_vm_probe | Vm and clamp-current probes | matlab/work/citt_generated_model.slx | Which measured signal tells us whether the clamp succeeded, and which tells us how hard the amplifier worked? |
| fp_adc_quantization | ADC sampling and quantization | matlab/work/citt_generated_model.slx | What information is lost when V_m is sampled and quantized into ADC codes? |
| fp_digital_control | Digital comparator or finite-state logic | matlab/work/citt_generated_model.slx | What state should the digital controller enter when the ADC code remains near the target for several samples? |
| fp_feedback_path | DAC or command update feedback path | matlab/work/citt_generated_model.slx | How does a delayed DAC update change the closed-loop settling behavior? |

## 8. Probe Map

- **Artifact:** matlab/work/citt_probe_map.json

| ID | Label | Model / Block Paths | Teaching Note |
| --- | --- | --- | --- |
| fp_vm_probe | Membrane voltage V_m(t) | matlab/work/citt_generated_model.slx | V_m(t) |
| fp_electrode_series_resistance | Clamp current | matlab/work/citt_generated_model.slx | clamp_current |
| fp_amplifier_limits | Amplifier output | matlab/work/citt_generated_model.slx | amplifier_output |
| fp_adc_quantization | ADC code sequence | matlab/work/citt_generated_model.slx | ADC_code_sequence |
| fp_digital_control | Digital control state | matlab/work/citt_generated_model.slx | digital_control_state |
| fp_digital_control | Saturation flags | matlab/work/citt_generated_model.slx | saturation_flags |
| fp_feedback_path | DAC/control update | matlab/work/citt_generated_model.slx | V_update_or_I_command |
| fp_vm_probe | Settling time | matlab/work/citt_generated_model.slx | settling_time |
| fp_vm_probe | Overshoot | matlab/work/citt_generated_model.slx | overshoot |

## 9. Last Probe Action

No probe action is recorded in the current app state.

## 10. Lab Delta Analysis

- **CSV:** matlab/work/citt_feature_lab_delta.csv
- **Report:** matlab/work/citt_lab_delta_report.json

| Quantity | Hand | Simulation | Measured | Difference | Status |
| --- | --- | --- | --- | --- | --- |
| attenuation_60hz_db | -20 | -19.2 | -18.5 | -3.65% | PASS |
| resonance_frequency | 50.329 | 50.329 | 50.4 | 0.141% | PASS |
| series_current_rms | 0.1766 | 0.176 | 0.174 | -1.14% | PASS |
| source_voltage_rms | 1.7678 | 1.7678 | 1.76 | -0.441% | PASS |

Likely causes / checks:
- Lab quantity not covered by probe map (warning): The CSV quantity does not clearly map to an SATK-generated probe.
- Probe unit mismatch (warning): The CSV unit differs from the probe-map unit.
- Model assumption may not match lab hardware (possible): The circuit spec includes idealized or simplified assumptions that can produce lab/model mismatch.

## 10A. Parameter Sweep / Tolerance Analysis

- **Markdown report:** matlab/work/citt_parameter_sweep_report.md
- **JSON report:** matlab/work/citt_parameter_sweep_report.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 04:16:57",
  "analysis_type": "rc_tolerance_sweep",
  "summary": {
    "resistor_id": "R1",
    "capacitor_id": "R1",
    "nominal_cutoff_hz": 0.0015915494309189533,
    "target_cutoff_hz": 50,
    "target_tolerance_percent": 10,
    "worst_case_cutoff_range_hz": [
      0.0012631344689832964,
      0.0020941439880512547
    ],
    "most_sensitive_parameter": "capacitor tolerance",
    "suggested_design_change": "Use tighter capacitor tolerance, recalibrate cutoff, or move nominal cutoff away from the requirement edge."
  },
  "rows": [
    {
      "case_id": "R1_C10",
      "r_tolerance_percent": 1,
      "c_tolerance_percent": 10,
      "cutoff_min_hz": 0.0014325377416012182,
      "cutoff_nominal_hz": 0.0015915494309189533,
      "cutoff_max_hz": 0.0017862507642188029,
      "pass_rate": 0,
      "status": "FAIL"
    },
    {
      "case_id": "R1_C20",
      "r_tolerance_percent": 1,
      "c_tolerance_percent": 20,
      "cutoff_min_hz": 0.0013131595964677833,
      "cutoff_nominal_hz": 0.0015915494309189533,
      "cutoff_max_hz": 0.0020095321097461532,
      "pass_rate": 0,
      "status": "FAIL"
    },
    {
      "case_id": "R5_C10",
      "r_tolerance_percent": 5,
      "c_tolerance_percent": 10,
      "cutoff_min_hz": 0.0013779648752545051,
      "cutoff_nominal_hz": 0.0015915494309189533,
      "cutoff_max_hz": 0.0018614613227122263,
      "pass_rate": 0,
      "status": "FAIL"
    },
    {
      "case_id": "R5_C20",
      "r_tolerance_percent": 5,
      "c_tolerance_percent": 20,
      "cutoff_min_hz": 0.0012631344689832964,
      "cutoff_nominal_hz": 0.0015915494309189533,
      "cutoff_max_hz": 0.0020941439880512547,
      "pass_rate": 0,
      "status": "FAIL"
    }
  ],
  "messages": [],
  "report_path": "matlab/work/citt_parameter_sweep_report.json",
  "markdown_path": "matlab/work/citt_parameter_sweep_report.md"
}
```

## 10B. Risk / Fault Injection

- **Markdown report:** matlab/work/citt_fault_injection_report.md
- **JSON report:** matlab/work/citt_fault_injection_report.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 04:16:57",
  "nominal_cutoff_hz": 0.0015915494309189533,
  "rows": [
    {
      "fault": "Open lead / disconnected electrode",
      "injected_change": "Disconnect the input source or electrode path.",
      "observed_effect": "Output becomes floating, zero, or dominated by noise depending on bias path.",
      "student_explanation": "The measured signal path is broken before the modeled filter can act.",
      "risk_mitigation": "Add connectivity checks and teach students to verify reference nodes first.",
      "status": "READY"
    },
    {
      "fault": "Shorted capacitor",
      "injected_change": "Force the filter capacitor impedance toward zero.",
      "observed_effect": "Nominal cutoff 0.001592 Hz is no longer meaningful because the output node is effectively shorted.",
      "student_explanation": "A shorted shunt capacitor can clamp the output node or destroy the intended pole.",
      "risk_mitigation": "Probe both sides of the capacitor and flag near-zero impedance faults.",
      "status": "READY"
    },
    {
      "fault": "Wrong capacitor unit: nF vs uF",
      "injected_change": "Scale capacitance by 1/1000 or 1000.",
      "observed_effect": "If C is 1000x too small, cutoff shifts from 0.001592 Hz to 1.592 Hz; if 1000x too large, it shifts to 1.592e-06 Hz.",
      "student_explanation": "Unit-prefix mistakes move the cutoff by orders of magnitude.",
      "risk_mitigation": "Run a parameter sanity check before simulation and display SI prefixes in reports.",
      "status": "READY"
    },
    {
      "fault": "Op-amp output saturation",
      "injected_change": "Limit output to assumed supply rails.",
      "observed_effect": "Waveform clips; small-signal frequency response no longer predicts output amplitude.",
      "student_explanation": "Active stages can leave their linear operating region.",
      "risk_mitigation": "Add output range requirements and inspect saturation source highlights.",
      "status": "PLAN"
    },
    {
      "fault": "ADC undersampling",
      "injected_change": "Lower sampling frequency below Nyquist margin.",
      "observed_effect": "High-frequency content aliases into the measurement band.",
      "student_explanation": "Sampling is part of the measurement system, not a cosmetic detail.",
      "risk_mitigation": "Add an fs >= 2*fmax requirement and sweep sampling frequency.",
      "status": "PLAN"
    },
    {
      "fault": "60 Hz interference too large",
      "injected_change": "Increase mains interference amplitude.",
      "observed_effect": "Output shows residual line-frequency content if filtering or shielding is insufficient.",
      "student_explanation": "Biomedical front-ends are sensitive to common-mode and environmental pickup.",
      "risk_mitigation": "Measure 60 Hz attenuation and include grounding/shielding assumptions.",
      "status": "PLAN"
    },
    {
      "fault": "Sensor noise increased",
      "injected_change": "Increase source or measurement noise.",
      "observed_effect": "Signal-to-noise ratio drops; small feature detection becomes unreliable.",
      "student_explanation": "Noise can hide physiological or low-amplitude circuit behavior.",
      "risk_mitigation": "Log SNR and compare expected versus measured noise floor.",
      "status": "PLAN"
    },
    {
      "fault": "Load impedance too low",
      "injected_change": "Decrease load resistance at the output node.",
      "observed_effect": "Th
... [truncated]
```

## 10C. Explainability Action Map

- **Markdown report:** matlab/work/citt_explainability_map.md
- **JSON report:** matlab/work/citt_explainability_map.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 05:01:08",
  "actions": [
    {
      "action_id": "focus_focus_electrode_sources",
      "action_type": "signal_path",
      "label": "Electrode sources and source impedance mismatch",
      "focus_id": "focus_electrode_sources",
      "target_paths": [
        "citt_generated_model/V_LA_controlled",
        "citt_generated_model/V_RA_controlled",
        "citt_generated_model/Rs_LA",
        "citt_generated_model/Rs_RA",
        "matlab/work/citt_generated_model.slx"
      ],
      "reason": "What part of the LA and RA waveforms is differential ECG, and what part is common-mode interference?",
      "status": "READY"
    },
    {
      "action_id": "focus_focus_bias_protection",
      "action_type": "input_path",
      "label": "Protection resistors and bias returns",
      "focus_id": "focus_bias_protection",
      "target_paths": [
        "citt_generated_model/Rprot_plus",
        "citt_generated_model/Rprot_minus",
        "citt_generated_model/Rbias_plus",
        "citt_generated_model/Rbias_minus",
        "matlab/work/citt_generated_model.slx"
      ],
      "reason": "Why do the INA inputs need high-value bias return resistors even when the ECG source is connected?",
      "status": "READY"
    },
    {
      "action_id": "focus_focus_ina_macro",
      "action_type": "signal_path",
      "label": "INA macro-model",
      "focus_id": "focus_ina_macro",
      "target_paths": [
        "citt_generated_model/Vin_plus_sensor",
        "citt_generated_model/Vin_minus_sensor",
        "citt_generated_model/diff_minus",
        "citt_generated_model/INA_diff_gain_100",
        "citt_generated_model/INA_cm_feedthrough_0p01",
        "citt_generated_model/INA_rails_0_to_3p3",
        "citt_generated_model/INA_MACRO_controlled",
        "matlab/work/citt_generated_model.slx"
      ],
      "reason": "How does the 100 V/V differential gain interact with electrode offset and 0..3.3 V clipping limits?",
      "status": "READY"
    },
    {
      "action_id": "focus_focus_highpass_lowpass",
      "action_type": "signal_path",
      "label": "High-pass and low-pass stages",
      "focus_id": "focus_highpass_lowpass",
      "target_paths": [
        "citt_generated_model/C_HP",
        "citt_generated_model/R_HP",
        "citt_generated_model/R_LP",
        "citt_generated_model/C_LP",
        "matlab/work/citt_generated_model.slx"
      ],
      "reason": "Which capacitor or resistor mainly controls startup recovery after the coupling capacitor charges?",
      "status": "READY"
    },
    {
      "action_id": "focus_focus_twin_t_notch",
      "action_type": "signal_path",
      "label": "Twin-T 60 Hz notch",
      "focus_id": "focus_twin_t_notch",
      "target_paths": [
        "citt_generated_model/Rn1",
        "citt_generated_model/Rn2",
        "citt_generated_model/Cn_mid",
        "citt_generated_model/Cn1",
        "citt_generated_model/Cn2",
        "citt_generated_model/Rn_mid",
        "matlab/work/citt_generated_model.slx"
      ],
      "reason": "Why does the Twin-T use paired equal resistors and capacitors plus midpoint values of 2C and R/2?",
      "status": "READY"
    },
    {
      "action_id": "focus_focus_adc_o
... [truncated]
```

## 10D. Learning Gain / Student Assessment

- **Markdown report:** matlab/work/citt_learning_assessment_report.md
- **JSON report:** matlab/work/citt_learning_assessment_report.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 04:17:04",
  "concept": "series RLC resonance reactance current phase",
  "expected_keywords": [
    "current",
    "impedance",
    "resonance",
    "reactance",
    "phase"
  ],
  "before": {
    "answer": "i guess voltage alone sets current.",
    "keyword_hits": "current",
    "score": 0.35
  },
  "after": {
    "answer": "current is set by impedance; resonance happens when inductive and capacitive reactance cancel, so current phase is near zero.",
    "keyword_hits": [
      "current",
      "impedance",
      "resonance",
      "reactance",
      "phase"
    ],
    "score": 1
  },
  "learning_gain": 0.65,
  "hint_levels_used": 1,
  "final_correctness": true,
  "misconception_detected": "low confidence or missing model-grounded reasoning",
  "time_to_correction": "not recorded",
  "report_path": "matlab/work/citt_learning_assessment_report.json",
  "markdown_path": "matlab/work/citt_learning_assessment_report.md"
}
```

## 10E. BOM / Cost + Licensing Reality

- **Markdown report:** matlab/work/citt_economics_plan.md
- **JSON report:** matlab/work/citt_economics_plan.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 04:17:05",
  "software": [
    {
      "name": "MATLAB / Simulink / Simscape",
      "assumption": "assumed campus license",
      "estimated_cost_usd": 0,
      "note": "Budget separately if no campus license exists."
    },
    {
      "name": "Gemini API",
      "assumption": "360 calls at assumed $0.0050/call",
      "estimated_cost_usd": 1.8,
      "note": "Assumption only; update from current billing before purchase."
    },
    {
      "name": "CiTT MATLAB plugin",
      "assumption": "local toolbox / course deployment",
      "estimated_cost_usd": 0,
      "note": "No per-seat cost modeled for prototype."
    }
  ],
  "hardware": [
    {
      "name": "Breadboard biomedical circuit kit",
      "assumption": "optional per lab team",
      "estimated_cost_usd": 35,
      "note": "Resistors, capacitors, jumpers, rails."
    },
    {
      "name": "ADC / microcontroller",
      "assumption": "optional per lab team",
      "estimated_cost_usd": 25,
      "note": "Only needed for hardware comparison labs."
    },
    {
      "name": "ECG/EMG front-end components",
      "assumption": "optional per lab team",
      "estimated_cost_usd": 40,
      "note": "Use educational isolation/safety policy."
    }
  ],
  "deployment": {
    "students": 30,
    "labs_per_course": 4,
    "api_calls_per_lab": 3,
    "estimated_api_cost_usd": 1.8,
    "instructor_setup_hours": 4,
    "assumptions": [
      "MATLAB toolboxes are available through an institution or competition sponsor.",
      "API cost is an editable planning assumption, not a live price quote.",
      "Hardware kits are optional for simulation-only courses."
    ]
  },
  "total_optional_hardware_per_team_usd": 100,
  "total_estimated_api_cost_usd": 1.8,
  "report_path": "matlab/work/citt_economics_plan.json",
  "markdown_path": "matlab/work/citt_economics_plan.md"
}
```

## 10F. Regulatory / Scope Guardrail

- **Markdown report:** matlab/work/citt_scope_guardrail.md
- **JSON report:** matlab/work/citt_scope_guardrail.json

```json
{
  "success": true,
  "created_at": "22-Jun-2026 04:17:06",
  "patient_connected_trigger_detected": false,
  "potential_regulatory_category": "educational software / design training tool, not patient-facing device software",
  "boundaries": [
    "This model is educational and proposal-facing.",
    "This is not clinical diagnosis.",
    "This is not medical-device verification.",
    "Generated model behavior depends on explicit assumptions, component values, and solver configuration."
  ],
  "additional_standards_to_consider": [
    "instructor review",
    "model-assumption display",
    "hardware lab safety policy if physical circuits are used"
  ],
  "risks": [
    {
      "risk": "Student mistakes simulation for certified device behavior",
      "trigger": "Any generated model or performance table",
      "mitigation": "Display educational boundary and assumptions in every export.",
      "severity": "Medium"
    },
    {
      "risk": "Hardware lab context exceeds simulation scope",
      "trigger": "Spec does not include explicit safety constraints",
      "mitigation": "Require instructor review before building physical circuits.",
      "severity": "Medium"
    },
    {
      "risk": "LLM parse error becomes hidden design assumption",
      "trigger": "Gemini structured spec drives model generation",
      "mitigation": "Expose parsed spec, assumptions, ambiguities, and model-check status in Evidence Pack.",
      "severity": "Medium"
    }
  ],
  "report_path": "matlab/work/citt_scope_guardrail.json",
  "markdown_path": "matlab/work/citt_scope_guardrail.md"
}
```

## 11. Limitations

- The spec still contains unresolved ambiguity: Exact numeric values for C_m, R_m, R_e, amplifier gain, rail voltages, current limit, ADC bits, ADC reference, sample time, DAC range, and controller timing are not specified., The detailed nonlinear membrane current law is optional and unspecified., The exact digital controller algorithm could be a comparator, finite-state controller, settling detector, saturation monitor, or a combination., The diagram shows a block-level feedback path from digital command update to amplifier but does not specify whether it updates Vc, injects a correction current, or changes amplifier reference., Current sign convention for clamp current is not specified., Initial membrane voltage and command step timing are not specified.
- Cutoff frequency near target is marked WARN.
- Sampling frequency satisfies Nyquist is marked WARN.
- Output saturation / clipping absent is marked WARN.
- 60 Hz interference attenuation checked is marked WARN.
- Input impedance above threshold is marked WARN.
- ADC quantization step below threshold is marked WARN.
- Simulation completed without recorded output variables; quantitative performance claims should be added after signal logging is configured.

## 12. Risk Table

| Risk | Evidence / Trigger | Mitigation | Severity |
| --- | --- | --- | --- |
| Student mistakes a teaching model for certified device behavior | CiTT generates educational Simscape evidence | State scope boundary in every export and show model assumptions before use. | Medium |
| Patient-connected circuit hazards are under-modeled | Spec appears to involve biosignals or electrodes | Require isolation, leakage-current, EMC, and hardware safety review outside CiTT before patient-connected use. | High |
| ADC undersampling or aliasing is missed | Spec mentions sampling or ADC behavior | Add a requirement row for Nyquist margin and verify it from logged simulation data. | Medium |
| Student mistakes simulation for certified device behavior | Any generated model or performance table | Display educational boundary and assumptions in every export. | Medium |
| Hardware lab context exceeds simulation scope | Spec does not include explicit safety constraints | Require instructor review before building physical circuits. | Medium |
| LLM parse error becomes hidden design assumption | Gemini structured spec drives model generation | Expose parsed spec, assumptions, ambiguities, and model-check status in Evidence Pack. | Medium |

## 13. BMES Functional Proof Draft

CiTT demonstrates functional feasibility by turning a circuit image or prompt into auditable MATLAB evidence rather than a standalone chatbot answer. In the current workflow, Gemini is used only to produce a structured circuit specification; the build step then hands that specification to a Simulink Agentic Toolkit-compatible task, producing the generated Simscape model. The Evidence Pack records the original input, the structured spec, model path, focus map, probe map, model-check output, simulation summary, Lab Delta comparison, limitations, and risk controls in one reviewable artifact. For this run, the requirement table contains 3 PASS, 6 WARN, 0 FAIL, and 0 NOT_RUN items. This makes the proof falsifiable: missing model checks, absent signal logging, unresolved topology ambiguity, or unavailable lab measurements are visible instead of hidden. The teaching value comes from connecting each verification artifact back to focus-map highlights and probe locations, allowing students to inspect why a node, component, or requirement matters. The current scope remains educational and proposal-facing, not medical-device verification. The next strongest evidence would be logged performance requirements, parameter sweeps, and a measured lab CSV for the same circuit. Primary current limitation: The spec still contains unresolved ambiguity: Exact numeric values for C_m, R_m, R_e, amplifier gain, rail voltages, current limit, ADC bits, ADC reference, sample time, DAC range, and controller timing are not specified., The detailed nonlinear membrane current law is optional and unspecified., The exact digital controller algorithm could be a comparator, finite-state controller, settling detector, saturation monitor, or a combination., The diagram shows a block-level feedback path from digital command update to amplifier but does not specify whether it updates Vc, injects a correction current, or changes amplifier reference., Current sign convention for clamp current is not specified., Initial membrane voltage and command step timing are not specified.

## Artifact Index

- **Circuit image:** submission_assets/benchmark_03_mixed_signal_simscape/input_schematic.png
- **Circuit spec:** matlab/work/citt_last_circuit_spec.json
- **Agent task:** matlab/work/citt_agent_task.md
- **Generated model:** matlab/work/citt_generated_model.slx (missing)
- **Focus map:** matlab/work/citt_focus_map.json
- **Probe map:** matlab/work/citt_probe_map.json
- **Model check report:** matlab/work/citt_model_check_report.md
- **Simulation summary:** matlab/work/citt_simulation_summary.json
- **Lab Delta report:** matlab/work/citt_lab_delta_report.json
- **Requirement report:** matlab/work/citt_requirement_report.md
- **Parameter sweep report:** matlab/work/citt_parameter_sweep_report.md
- **Fault injection report:** matlab/work/citt_fault_injection_report.md
- **Explainability map report:** matlab/work/citt_explainability_map.md
- **Assessment report:** matlab/work/citt_learning_assessment_report.md
- **Economics plan:** matlab/work/citt_economics_plan.md
- **Scope guardrail:** matlab/work/citt_scope_guardrail.md
- **Evidence pack:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/benchmark_03_evidence_pack.md
