# CiTT Performance Evidence Pack

Generated: 2026-06-23 00:16:29
Purpose: functional proof and technical-feasibility evidence for the CiTT MATLAB plugin workflow.

## 1. Original Circuit / Prompt

- **Image:** not recorded
- **Prompt:** # Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic

Model a closed-loop neural clamp system with membrane capacitance Cm, membrane leakage resistance Rm, optional simplified nonlinear membrane current, electrode series resistance, finite-gain amplifier, output current limit, rail saturation, command voltage step Vc(t), ADC sampling and quantization of Vm, digital comparator or finite-state control logic, DAC or command update path, and requested outputs Vm(t), clamp current, amplifier output, ADC code sequence, digital control state, saturation flags, settling time, and overshoot.

This problem is intentionally too complex for reliable LLM-only closed-form solving. It requires simulation.

## Educational Scaled Benchmark Parameters

Use the following values to make the benchmark executable and visually inspectable. These are **educational scaled benchmark parameters, not a clinically validated axon model**. They are chosen to produce stable transient behavior, visible ADC/digital effects, and clear saturation/fault evidence.

Nominal analog and membrane parameters:

- `V_rest = -65e-3 V`
- `V_cmd_initial = -65e-3 V`
- `V_cmd_final = -20e-3 V`
- `command_step_time = 5e-3 s`
- `R_m = 20e6 ohm`
- `C_m = 500e-12 F`
- `E_leak = -65e-3 V`
- `R_e = 2e6 ohm`
- `R_series_output = 100e3 ohm`
- `I_membrane_nonlinear_max = 0.5e-9 A`
- `V_nonlinear_threshold = -40e-3 V`
- `V_nonlinear_slope = 6e-3 V`

Amplifier and clamp parameters:

- `A_ol = 2e4 V/V`
- `amplifier_bandwidth_hz = 2000`
- `output_rails = [-1.0, 1.0] V`
- `output_current_limit = 5e-9 A`
- `output_resistance = 50 ohm`
- `input_offset = 0 V`
- `input_noise_rms = 100e-6 V` optional

ADC and digital-control parameters:

- `T_s = 2e-4 s`
- `fs = 5000 Hz`
- `adc_bits = 12`
- `adc_input_range = [-0.2, 0.2] V`
- `adc_lsb = (0.2 - (-0.2)) / 2^12`
- `digital_settled_threshold = 1e-3 V`
- `digital_settled_hold_time = 2e-3 s`
- `saturation_voltage_threshold = 0.95 V`
- `saturation_current_threshold = 4.8e-9 A`

Simulation parameters:

- `t_stop = 60e-3 s`
- `max_step = 1e-5 s`
- Plot `Vm` and command in mV, clamp current in nA, amplifier output in V, ADC code as integer, and digital state as integer.

Parameter sweep:

- `A_ol_values = [1e3, 3e3, 1e4, 3e4, 1e5]`
- `R_e_values = [0.2e6, 0.5e6, 1e6, 2e6, 5e6]`
- Metric: final tracking error in mV and saturation duration in ms.

Fault injection cases:

1. `wrong_Cm_10x`: set `C_m = 5e-9 F`; expected effect is slower settling.
2. `low_adc_rate`: set `T_s = 2e-3 s`, `fs = 500 Hz`; expected effect is coarse digital timing and aliasing risk.
3. `high_electrode_resistance`: set `R_e = 10e6 ohm`; expected effect is larger tracking error and amplifier demand.
4. `low_current_limit`: set `output_current_limit = 1e-9 A`; expected effect is clamp current saturation and slower response.
5. `narrow_rails`: set `output_rails = [-0.05, 0.05] V`; expected effect is amplifier voltage saturation.
6. `unit_mistake_capacitance`: set `C_m = 500e-9 F`; expected effect is an unrealistic time constant and failed settling.

Required generated plots:

- `mixed_signal_full_timeline.png`
- `membrane_voltage_and_clamp_current.png`
- `amplifier_saturation.png`
- `adc_codes_and_digital_logic.png`
- `digital_state_machine_trace.png`
- `parameter_sweep_heatmap.png`
- `fault_injection_summary.png`
- **Spec source:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_spec_parameterized.json
- **Circuit type:** not specified

## 2. Gemini Structured Circuit Spec

- **Source:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_spec_parameterized.json
- **Likely analysis:** not specified
- **Components:** 5
- **Nodes:** not specified
- **Requested outputs:** not specified

```json
{
  "benchmark": "mixed_signal_neural_clamp",
  "title": "Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic",
  "source": "live SATK/Simscape model plus educational scaled benchmark simulation parameters",
  "parameter_set_label": "educational scaled benchmark parameters",
  "parameter_set_warning": "Not a clinically validated axon model.",
  "components": [
    {
      "id": "membrane",
      "type": "simscape_electrical_membrane",
      "parameters": {
        "V_rest_V": -0.065,
        "R_m_ohm": 2.0E+7,
        "C_m_F": 5E-10,
        "E_leak_V": -0.065,
        "I_membrane_nonlinear_max_A": 5E-10,
        "V_nonlinear_threshold_V": -0.04,
        "V_nonlinear_slope_V": 0.006
      }
    },
    {
      "id": "electrode",
      "type": "series_resistance",
      "parameters": {
        "R_e_ohm": 2.0E+6,
        "R_series_output_ohm": 100000
      }
    },
    {
      "id": "amplifier",
      "type": "finite_gain_nonideal",
      "features": [
        "rail saturation",
        "current limit",
        "finite bandwidth"
      ],
      "parameters": {
        "A_ol_V_per_V": 20000,
        "amplifier_bandwidth_hz": 2000,
        "output_rails_V": [
          -1,
          1
        ],
        "output_current_limit_A": 5E-9,
        "output_resistance_ohm": 50,
        "input_offset_V": 0,
        "input_noise_rms_V": 0.0001
      }
    },
    {
      "id": "adc",
      "type": "sample_and_quantize",
      "parameters": {
        "T_s_s": 0.0002,
        "fs_hz": 5000,
        "adc_bits": 12,
        "adc_input_range_V": [
          -0.2,
          0.2
        ],
        "adc_lsb_V": 9.765625E-5
      }
    },
    {
      "id": "logic",
      "type": "digital_state_control",
      "states": [
        "idle",
        "acquire",
        "clamp",
        "saturated",
        "settled"
      ],
      "parameters": {
        "digital_settled_threshold_V": 0.001,
        "digital_settled_hold_time_s": 0.002,
        "saturation_voltage_threshold_V": 0.95,
        "saturation_current_threshold_A": 4.8E-9
      }
    }
  ],
  "simulation": {
    "t_stop_s": 0.06,
    "max_step_s": 1E-5,
    "plot_units": {
      "Vm": "mV",
      "V_cmd": "mV",
      "I_clamp": "nA",
      "V_amp": "V",
      "ADC_code": "integer",
      "digital_state": "integer"
    }
  },
  "parameter_sweep": {
    "A_ol_values": [
      1000,
      3000,
      10000,
      30000,
      100000
    ],
    "R_e_values_ohm": [
      200000,
      500000,
      1.0E+6,
      2.0E+6,
      5.0E+6
    ],
    "metrics": [
      "final_tracking_error_mV",
      "saturation_duration_ms"
    ]
  },
  "fault_injection_cases": [
    {
      "id": "wrong_Cm_10x",
      "change": "C_m = 5e-9 F",
      "expected_effect": "slower settling"
    },
    {
      "id": "low_adc_rate",
      "change": "T_s = 2e-3 s, fs = 500 Hz",
      "expected_effect": "coarse digital timing / aliasing risk"
    },
    {
      "id": "high_electrode_resistance",
      "change": "R_e = 10e6 ohm",
      "expected_effect": "larger tracking error / amplifier demand"
    },
    {
      "id": "low_current_limit",
      "change": "output_current_limit = 1e-9 A",
      "expected_effect": "clamp current saturation and slower response"
    },
    {
      "id": "narrow_rails",
      "change": "output_rails = [-0.05, 0.05] V",
      "expected_effect": "amplifier voltage saturation"
    },
    {
      "id": "unit_mistake_capacitance",
      "change": "C_m = 500e-9 F",
      "expected_effect": "unrealistic time constant and failed settling"
    }
  ],
  "focus_map": [
    "command_path",
    "membrane_node",
    "feedback_loop",
    "amplifier_saturation",
    "adc_sampling",
    "digital_control_logic",
    "clamp_current_probe"
  ],
  "probe_map": [
    "Vm(t)",
    "V_cmd(t)",
    "clamp current I_clamp(t)",
    "amplifier output V_amp(t)",
    "ADC code(t)",
    "digital state(t)",
    "saturation flag(t)",
    "settling time",
    "overshoot",
    "final tracking error"
  ],
  "required_plots": [
    "mixed_signal_full_timeline.png",
    "membrane_voltage_and_clamp_current.png",
    "amplifier_saturation.png",
    "adc_codes_and_digital_logic.png",
    "digital_state_machine_trace.png",
    "parameter_sweep_heatmap.png",
    "fault_injection_summary.png"
  ],
  "limitations": [
    "Educational scaled parameters are selected for stable, visible benchmark behavior and are not medical-use validation.",
    "If the generated Simscape model cannot execute in a local MATLAB install, deterministic fallback plots must be labeled as fallback evidence."
  ]
}
```

## 3. SATK / Simscape Model Artifacts

- **Generated model:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_generated_model.slx
- **Agent task:** not recorded
- **Agent run:** recorded (installed_example_repro), success=true

## 4. Model Check Result

- **Status:** PASS
- **Report:** release/example_repro/benchmark_03_mixed_signal/citt_model_check_report.md

Messages:
- Diagram update completed.
- Model checksum captured.
- Model Advisor command not found on this MATLAB path.

## 5. Simulation Curve / Data Summary

- **Status:** PASS
- **Summary:** not recorded
- **Plot/screenshot:** not captured by the current simulation run
- **Output variables:** none recorded

Messages:
- none

## 6. Requirement Pass/Fail Table

This table uses only evidence currently present in the MATLAB plugin state and saved artifacts.

| Requirement | Evidence | Result | Status |
| --- | --- | --- | --- |
| Original circuit input captured | prompt text | prompt recorded | PASS |
| Structured circuit spec available | submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_spec_parameterized.json | structured spec loaded | PASS |
| Spec has no blocking topology ambiguity | unsupported_or_unclear_regions / ambiguities | no blocking regions recorded | PASS |
| Simscape model artifact generated | submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_generated_model.slx | file exists | PASS |
| Model check completed without update errors | release/example_repro/benchmark_03_mixed_signal/citt_model_check_report.md | model check succeeded | PASS |
| Simulation executed and summary captured |   | simulation succeeded; no output variables recorded | WARN |
| Focus/highlight map available | submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_focus_map.json | 8 map item(s) | PASS |
| Probe map or probe action available | submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_probe_map.json | 9 probe map item(s) | PASS |
| Lab Delta comparison available |   | Lab Delta not run | NOT_RUN |
| Educational scope guardrail stated | Evidence Pack risk section | pack states educational use, not clinical/device verification | PASS |

## 6A. Detailed Requirement-to-Simulation Report

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_requirement_report.md (missing)
- **JSON report:** not recorded

```json
{
  "rows": []
}
```

## 7. Focus Map / Highlight Map

- **Artifact:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_focus_map.json

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

- **Artifact:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_probe_map.json

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

```json
{
  "success": true,
  "target_id": "probe_vm"
}
```

## 10. Lab Delta Analysis

Lab Delta has not been run or no comparison rows were found.

## 10A. Parameter Sweep / Tolerance Analysis

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_parameter_sweep_report.md (missing)
Report has not been generated yet.

## 10B. Risk / Fault Injection

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_fault_injection_report.md (missing)
Report has not been generated yet.

## 10C. Explainability Action Map

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_explainability_map.md (missing)
Report has not been generated yet.

## 10D. Learning Gain / Student Assessment

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_learning_assessment_report.md (missing)
Report has not been generated yet.

## 10E. BOM / Cost + Licensing Reality

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_economics_plan.md (missing)
Report has not been generated yet.

## 10F. Regulatory / Scope Guardrail

- **Markdown report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_scope_guardrail.md (missing)
Report has not been generated yet.

## 11. Limitations

- Simulation executed and summary captured is marked WARN.
- Lab Delta comparison available is marked NOT_RUN.
- Simulation completed without recorded output variables; quantitative performance claims should be added after signal logging is configured.
- No lab measurement CSV has been compared against simulation yet.

## 12. Risk Table

| Risk | Evidence / Trigger | Mitigation | Severity |
| --- | --- | --- | --- |
| Student mistakes a teaching model for certified device behavior | CiTT generates educational Simscape evidence | State scope boundary in every export and show model assumptions before use. | Medium |
| Patient-connected circuit hazards are under-modeled | Spec appears to involve biosignals or electrodes | Require isolation, leakage-current, EMC, and hardware safety review outside CiTT before patient-connected use. | High |
| ADC undersampling or aliasing is missed | Spec mentions sampling or ADC behavior | Add a requirement row for Nyquist margin and verify it from logged simulation data. | Medium |

## 13. BMES Functional Proof Draft

CiTT demonstrates functional feasibility by turning a circuit image or prompt into auditable MATLAB evidence rather than a standalone chatbot answer. In the current workflow, Gemini is used only to produce a structured circuit specification; the build step then hands that specification to a Simulink Agentic Toolkit-compatible task, producing the generated Simscape model at submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_generated_model.slx. The Evidence Pack records the original input, the structured spec, model path, focus map, probe map, model-check output, simulation summary, Lab Delta comparison, limitations, and risk controls in one reviewable artifact. For this run, the requirement table contains 8 PASS, 1 WARN, 0 FAIL, and 1 NOT_RUN items. This makes the proof falsifiable: missing model checks, absent signal logging, unresolved topology ambiguity, or unavailable lab measurements are visible instead of hidden. The teaching value comes from connecting each verification artifact back to focus-map highlights and probe locations, allowing students to inspect why a node, component, or requirement matters. The current scope remains educational and proposal-facing, not medical-device verification. The next strongest evidence would be logged performance requirements, parameter sweeps, and a measured lab CSV for the same circuit. Primary current limitation: Simulation executed and summary captured is marked WARN.

## Artifact Index

- **Circuit image:** not recorded
- **Circuit spec:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_spec_parameterized.json
- **Agent task:** not recorded
- **Generated model:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_generated_model.slx
- **Focus map:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_focus_map.json
- **Probe map:** submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_probe_map.json
- **Model check report:** release/example_repro/benchmark_03_mixed_signal/citt_model_check_report.md
- **Simulation summary:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_simulation_summary.json (missing)
- **Lab Delta report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_lab_delta_report.json (missing)
- **Requirement report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_requirement_report.md (missing)
- **Parameter sweep report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_parameter_sweep_report.md (missing)
- **Fault injection report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_fault_injection_report.md (missing)
- **Explainability map report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_explainability_map.md (missing)
- **Assessment report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_learning_assessment_report.md (missing)
- **Economics plan:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_economics_plan.md (missing)
- **Scope guardrail:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_scope_guardrail.md (missing)
- **Evidence pack:** release/example_repro/benchmark_03_mixed_signal/citt_evidence_pack.md
