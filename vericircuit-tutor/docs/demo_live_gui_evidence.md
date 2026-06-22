# CiTT Live GUI Evidence Demo

This document is the demo map for the release evidence package. The final evidence entry point is:

```text
vericircuit-tutor/submission_assets/live_gui_evidence/
```

Use the live GUI evidence package as final proof. Older offline draft reports, placeholder panels, and source benchmark folders under `submission_assets/` are provenance only.

## Demo Goal

Show that CiTT is not just a chatbot. It turns circuit prompts/images into inspectable MATLAB, Simulink, and Simscape artifacts, then teaches from those artifacts through model highlights, natural-language probes, plots, metrics, and exported evidence.

## Global Evidence

- `submission_assets/live_gui_evidence/README.md`
- `submission_assets/live_gui_evidence/bmes_live_evidence_report.md`
- `submission_assets/live_gui_evidence/screenshots/00_app_open.png`
- `submission_assets/live_gui_evidence/screenshots/01_read_page.png`
- `submission_assets/live_gui_evidence/screenshots/02_build_page.png`
- `submission_assets/live_gui_evidence/screenshots/03_simscape_model_arranged.png`
- `submission_assets/live_gui_evidence/screenshots/04_teach_page.png`
- `submission_assets/live_gui_evidence/screenshots/05_highlight_feedback_or_signal_path.png`
- `submission_assets/live_gui_evidence/screenshots/06_probe_page.png`

## Benchmark 1 RC Demo

Scenario: textbook RC anti-aliasing filter for an ECG-style input before an ADC.

What the demo proves:

- Gemini/CiTT parses the circuit into a structured RC/ADC spec.
- The SATK/MCP agent flow builds and opens a Simscape model.
- The model is manually arranged and captured.
- Teaching links the cutoff formula to the RC components and `Vout` node.
- Highlighting selects the signal path/focus region.
- Natural-language probe returns measurement-style values in the learning dialog.
- Bode evidence shows both the intended filter and the 100 uF unit-mistake case.

Key paths:

- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/problem_statement.md`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/run_notes.md`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/comparison.md`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/llm_baseline_output_gemini_no_tools.md`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/screenshots/03_simscape_model_arranged.png`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/screenshots/04_teach_cutoff_formula.png`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/screenshots/05_highlight_signal_path.png`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/screenshots/06_probe_page.png`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/plots/rc_bode_live.png`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/plots/rc_bode_annotated.png`

Live values recorded in the evidence report:

- `R = 39.8 kOhm`
- `C = 100 nF`
- `tau = 0.00398 s`
- `fc = 39.9887 Hz`
- `60 Hz attenuation = -5.1205 dB`
- `250 Hz attenuation = -16.0298 dB`

Gemini-only baseline contrast:

- Gemini-only performs well on this textbook RC calculation and should not be described as failing.
- CiTT adds executable model grounding: generated Simscape/Simulink model, visible output-probe placement, focus-map teaching, natural-language probe output, Lab Delta/unit-mistake diagnosis, and annotated Bode evidence.

Limitations:

- ADC internals such as resolution, input impedance, aperture effects, and detailed sample-and-hold dynamics are not fully modeled in this benchmark.
- The Bode plot is teaching evidence for a first-order RC stage, not proof of a complete clinical ECG acquisition system.

## Benchmark 2 TEVC Demo

Scenario: two-electrode voltage clamp equivalent circuit with command source, amplifier path, membrane branch, electrode resistance, and probes.

What the demo proves:

- CiTT accepts a more biomedical circuit abstraction with omitted biological dynamics.
- The generated Simscape-first model uses built-in physical/electrical blocks.
- The model includes command source, buffer path, finite-gain amplifier, `Ro`, `Rm`, symbolic `Re`, membrane-voltage probe, amplifier-output probe, clamp-current probe, electrical reference, and solver configuration.
- Teaching focuses on the feedback loop and membrane voltage.
- Natural-language probes are visible in the chat-style learning dialog.
- Focus and probe maps decode successfully.

Key paths:

- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/problem_statement.md`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/run_notes.md`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/comparison.md`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/llm_baseline_output_gemini_no_tools.md`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/workflow_total_prompt.md`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/artifacts/citt_generated_model_tevc.slx`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/artifacts/citt_focus_map.json`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/artifacts/citt_probe_map.json`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/screenshots/03_simscape_model_arranged.png`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/screenshots/05_teach_reveal_feedback_loop.png`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/screenshots/06_teach_step2_vm.png`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/screenshots/12_chat_probe_vm_restored.png`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/screenshots/13_latex_probe_restored.png`

Limitations:

- `V_c` and `R_e` remain symbolic because the benchmark does not provide numeric values.
- Numeric simulation/probe values require assigning missing parameters first.
- The model is a teaching abstraction, not a validated electrophysiology model.

Gemini-only baseline contrast:

- Gemini-only explains the TEVC feedback concept and finite-gain tracking intuition.
- It also mixes the `Vc` and `Re` limitations: `Vc` prevents an absolute numeric `Vm`, while `Re` is irrelevant under the ideal-buffer DC assumption.
- CiTT adds the generated physical model, decoded focus/probe maps, model-check evidence, and GUI-backed teaching/probe screenshots.

## Benchmark 3 Mixed-Signal Demo

Scenario: closed-loop mixed-signal neural clamp with analog membrane dynamics, amplifier limits, ADC/digital behavior, feedback, and educational parameter sweeps.

What the demo proves:

- CiTT can produce and open a larger mixed-signal Simulink/Simscape model.
- The user arranged the model and captured evidence after simulation.
- Teaching/probe evidence appears in the same learning surface.
- Highlight actions identify command, ADC sampling, and feedback paths.
- The exported evidence pack links requirements, model evidence, plots, warnings, limitations, and risk controls.
- Simulation exposed non-settling, rail/current limiting, ADC/digital behavior, parameter sensitivity, and fault sensitivity.

Key paths:

- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/problem_statement.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/problem_statement_parameterized.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/run_notes.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/comparison.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/llm_baseline_output_gemini_no_tools.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/citt_generated_model.slx`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/benchmark_03_simulation_metrics.json`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/benchmark_03_simulation_report.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/artifacts/benchmark_03_evidence_pack.md`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/06_model_after_user_arrangement.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/07_model_parameterized_after_simulation.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/08_citt_teach_probe_after_benchmark3_simulation.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/09_highlight_command_path.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/10_highlight_adc_sampling_path.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/11_highlight_feedback_path.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/screenshots/15_evidence_thread_exported.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/mixed_signal_full_timeline.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/membrane_voltage_and_clamp_current.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/amplifier_saturation.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/adc_codes_and_digital_logic.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/digital_state_machine_trace.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/parameter_sweep_heatmap.png`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/plots/fault_injection_summary.png`

Simulation metrics recorded in the live evidence report:

- Source: Simulink/Simscape model run.
- Settling time: not settled in the 60 ms window.
- Overshoot: `413.9 %`.
- Final tracking error: `186.2 mV`.
- Saturation duration: `60 ms`.
- Max clamp current: `5.099 nA`.
- Max amplifier output: `1 V`.
- Model warning: discontinuities in algebraic loops may prevent the algebraic loop solver from solving the loop.

Limitations:

- Benchmark 3 uses educational scaled benchmark parameters, not a clinically validated axon model.
- The nominal model staying at rail/current limit is limitation-discovery evidence, not a design-success claim.
- Parameter-sweep and fault-injection comparison plots are deterministic educational comparisons generated from the benchmark parameter set.
- Full Lab Delta CSV comparison was not completed because no real external lab CSV was supplied.

Gemini-only baseline contrast:

- Gemini-only correctly states that exact transient waveforms, ADC code sequences, saturation intervals, settling time, and overshoot require executable simulation.
- It also shows no-tools risks on complex prompts: unit slips, unsupported model assumptions, capacitance-scale mistakes, and over-strong qualitative claims.
- CiTT adds generated model artifacts, highlightable model paths, probe maps, simulation plots, metrics JSON, warnings, and explicit limitation evidence.

## Suggested Live Narration

1. Start with the product need: students use AI for biomedical circuits, but a fluent answer can hide wrong units, signs, or assumptions.
2. Open CiTT in MATLAB and show the plugin, not the legacy web UI.
3. Use Benchmark 1 to show a clean RC teaching path and probe output.
4. Use Benchmark 2 to show symbolic biomedical modeling and honest assumptions.
5. Use Benchmark 3 to show that the generated model can expose failure modes instead of smoothing them over in prose.
6. Close on the evidence package: screenshots, model artifacts, focus/probe maps, plots, metrics, and limitations are reviewable.

## Evidence Boundaries

- Do not use `bmes_evidence_report_OFFLINE_DRAFT.md` as final proof.
- Do not claim full Lab Delta comparison unless a real external lab CSV is supplied.
- Treat Gemini-only no-tools outputs as comparison artifacts, not executable model evidence.
- Do not claim medical-device verification, clinical validity, or patient-specific decision support.
