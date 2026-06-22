# CiTT Performance Evidence Pack

Generated: 2026-06-23 00:16:20
Purpose: functional proof and technical-feasibility evidence for the CiTT MATLAB plugin workflow.

## 1. Original Circuit / Prompt

- **Image:** not recorded
- **Prompt:** # Benchmark 1: Textbook RC Anti-Aliasing

An ECG acquisition front end uses a first-order RC low-pass filter before a 500 Hz ADC.

R = 39.8 kOhm and C = 100 nF. The input contains a 5 Hz ECG-like component and 60 Hz interference.

Tasks:
- Compute the cutoff frequency.
- Compute attenuation at 60 Hz.
- Compute attenuation at the Nyquist frequency.
- Identify where the output voltage should be probed in a Simscape/Simulink model.
- Diagnose a lab mistake where the student accidentally used 100 uF instead of 100 nF.
- **Spec source:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_spec_reproduced.json
- **Circuit type:** rc_low_pass_anti_aliasing

## 2. Gemini Structured Circuit Spec

- **Source:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_spec_reproduced.json
- **Likely analysis:** ac_frequency_response
- **Components:** 3
- **Nodes:** n_in, n_out, 0
- **Requested outputs:** V(n_out)

```json
{
  "circuit_type": "rc_low_pass_anti_aliasing",
  "components": [
    {
      "id": "V1",
      "type": "voltage_source",
      "label": "V1",
      "value": 1,
      "unit": "V",
      "terminals": [
        "positive",
        "negative"
      ],
      "confidence": 1
    },
    {
      "id": "R1",
      "type": "resistor",
      "label": "R1",
      "value": 39800,
      "unit": "Ohm",
      "terminals": [
        "left",
        "right"
      ],
      "confidence": 1
    },
    {
      "id": "C1",
      "type": "capacitor",
      "label": "C1",
      "value": 1E-7,
      "unit": "F",
      "terminals": [
        "top",
        "bottom"
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
  "likely_analysis": "ac_frequency_response",
  "assumptions": [
    "500 Hz ADC",
    "first-order educational RC stage"
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
    "focus_id": "rc_output",
    "label": "RC output node",
    "explanation": "The low-pass output is the node between R1 and C1.",
    "model_paths": [],
    "block_paths": [],
    "related_components": [
      "R1",
      "C1"
    ],
    "related_nodes": "n_out",
    "teaching_question": "Why is n_out the correct place to probe the filtered signal?"
  }
}
```

## 3. SATK / Simscape Model Artifacts

- **Generated model:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/rc_reproduced_model.slx
- **Agent task:** not recorded
- **Agent run:** recorded (installed_example_repro), success=true

## 4. Model Check Result

- **Status:** PASS
- **Report:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_model_check_report.md

Messages:
- Diagram update completed.
- Model checksum captured.
- Model Advisor command not found on this MATLAB path.

## 5. Simulation Curve / Data Summary

Simulation has not been run or no summary JSON was found.
- **Expected summary:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_simulation_summary.json (missing)

## 6. Requirement Pass/Fail Table

This table uses only evidence currently present in the MATLAB plugin state and saved artifacts.

| Requirement | Evidence | Result | Status |
| --- | --- | --- | --- |
| Original circuit input captured | prompt text | prompt recorded | PASS |
| Structured circuit spec available | /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_spec_reproduced.json | structured spec loaded: rc_low_pass_anti_aliasing | PASS |
| Spec has no blocking topology ambiguity | unsupported_or_unclear_regions / ambiguities | no blocking regions recorded | PASS |
| Simscape model artifact generated | /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/rc_reproduced_model.slx | file exists | PASS |
| Model check completed without update errors | /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_model_check_report.md | model check succeeded | PASS |
| Simulation executed and summary captured |   | simulation not run | NOT_RUN |
| Focus/highlight map available | /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_focus_map.json | 1 map item(s) | PASS |
| Probe map or probe action available | /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_probe_map.json | 1 probe map item(s) | PASS |
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

- **Artifact:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_focus_map.json

| ID | Label | Model / Block Paths | Teaching Note |
| --- | --- | --- | --- |
| focus_1 | RC output node | rc_reproduced_model | Why is n_out the correct place to probe the filtered signal? |

## 8. Probe Map

- **Artifact:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_probe_map.json

| ID | Label | Model / Block Paths | Teaching Note |
| --- | --- | --- | --- |
| model_output | RC output node | rc_reproduced_model | V(n_out) |

## 9. Last Probe Action

```json
{
  "success": true,
  "target_id": "probe_vout"
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

- Simulation executed and summary captured is marked NOT_RUN.
- Lab Delta comparison available is marked NOT_RUN.
- No simulation data summary or curve screenshot has been captured in this run.
- No lab measurement CSV has been compared against simulation yet.

## 12. Risk Table

| Risk | Evidence / Trigger | Mitigation | Severity |
| --- | --- | --- | --- |
| Student mistakes a teaching model for certified device behavior | CiTT generates educational Simscape evidence | State scope boundary in every export and show model assumptions before use. | Medium |
| Generated model omits physical safety context | No patient-connected trigger detected | Keep explicit educational boundary and require instructor review for hardware labs. | Medium |
| ADC undersampling or aliasing is missed | Spec mentions sampling or ADC behavior | Add a requirement row for Nyquist margin and verify it from logged simulation data. | Medium |

## 13. BMES Functional Proof Draft

CiTT demonstrates functional feasibility by turning a circuit image or prompt into auditable MATLAB evidence rather than a standalone chatbot answer. In the current workflow, Gemini is used only to produce a structured circuit specification; the build step then hands that specification to a Simulink Agentic Toolkit-compatible task, producing the generated Simscape model at /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/rc_reproduced_model.slx. The Evidence Pack records the original input, the structured spec, model path, focus map, probe map, model-check output, simulation summary, Lab Delta comparison, limitations, and risk controls in one reviewable artifact. For this run, the requirement table contains 8 PASS, 0 WARN, 0 FAIL, and 2 NOT_RUN items. This makes the proof falsifiable: missing model checks, absent signal logging, unresolved topology ambiguity, or unavailable lab measurements are visible instead of hidden. The teaching value comes from connecting each verification artifact back to focus-map highlights and probe locations, allowing students to inspect why a node, component, or requirement matters. The current scope remains educational and proposal-facing, not medical-device verification. The next strongest evidence would be logged performance requirements, parameter sweeps, and a measured lab CSV for the same circuit. Primary current limitation: Simulation executed and summary captured is marked NOT_RUN.

## Artifact Index

- **Circuit image:** not recorded
- **Circuit spec:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_spec_reproduced.json
- **Agent task:** not recorded
- **Generated model:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/rc_reproduced_model.slx
- **Focus map:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_focus_map.json
- **Probe map:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_probe_map.json
- **Model check report:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_model_check_report.md
- **Simulation summary:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_simulation_summary.json (missing)
- **Lab Delta report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_lab_delta_report.json (missing)
- **Requirement report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_requirement_report.md (missing)
- **Parameter sweep report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_parameter_sweep_report.md (missing)
- **Fault injection report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_fault_injection_report.md (missing)
- **Explainability map report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_explainability_map.md (missing)
- **Assessment report:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_learning_assessment_report.md (missing)
- **Economics plan:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_economics_plan.md (missing)
- **Scope guardrail:** /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work/citt_scope_guardrail.md (missing)
- **Evidence pack:** /Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/release/example_repro/benchmark_01_textbook_rc/citt_evidence_pack.md
