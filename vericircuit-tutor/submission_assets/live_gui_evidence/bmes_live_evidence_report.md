# CiTT BMES Live GUI Evidence Report

Generated: 2026-06-22
Refreshed after Benchmark 3 parameterized simulation: 2026-06-22

## Scope

This report summarizes real MATLAB/CiTT/Simulink GUI evidence captured under `vericircuit-tutor/submission_assets/live_gui_evidence/`.

Completed live GUI evidence:

- Benchmark 1: textbook RC anti-aliasing.
- Benchmark 2: two-electrode voltage clamp equilibrium.
- Benchmark 3: closed-loop mixed-signal neural clamp with educational scaled parameters.

Important boundary: Benchmark 3 uses **educational scaled benchmark parameters, not a clinically validated axon model**. The nominal timeline plots are from a Simulink/Simscape model run. The parameter sweep and fault-injection comparison plots are deterministic educational calculations generated from the same parameter set for fast visual comparison, and are labeled as such.

## Evidence Index

Global screenshots:

- `screenshots/00_app_open.png`: CiTT app opened in MATLAB.
- `screenshots/01_read_page.png`: live read/parse page.
- `screenshots/02_build_page.png`: live build page.
- `screenshots/03_simscape_model_arranged.png`: arranged Simscape/Simulink model evidence.
- `screenshots/04_teach_page.png`: teaching UI evidence.
- `screenshots/05_highlight_feedback_or_signal_path.png`: highlight evidence.
- `screenshots/06_probe_page.png`: natural-language probe evidence.
- `screenshots/07_evidence_page.png`: legacy evidence/tool section screenshot from the live GUI pass.

Benchmark 1 folder:

- `benchmark_01_textbook_rc/problem_statement.md`
- `benchmark_01_textbook_rc/llm_baseline_prompt.md`
- `benchmark_01_textbook_rc/llm_baseline_output_gemini_no_tools.md`
- `benchmark_01_textbook_rc/run_notes.md`
- `benchmark_01_textbook_rc/comparison.md`
- `benchmark_01_textbook_rc/screenshots/`
- `benchmark_01_textbook_rc/plots/rc_bode_live.png`
- `benchmark_01_textbook_rc/plots/rc_bode_annotated.png`

Benchmark 2 folder:

- `benchmark_02_tevc_equilibrium/problem_statement.md`
- `benchmark_02_tevc_equilibrium/llm_baseline_prompt.md`
- `benchmark_02_tevc_equilibrium/llm_baseline_output_gemini_no_tools.md`
- `benchmark_02_tevc_equilibrium/run_notes.md`
- `benchmark_02_tevc_equilibrium/comparison.md`
- `benchmark_02_tevc_equilibrium/workflow_total_prompt.md`
- `benchmark_02_tevc_equilibrium/screenshots/`
- `benchmark_02_tevc_equilibrium/artifacts/citt_generated_model_tevc.slx`

Benchmark 3 folder:

- `benchmark_03_mixed_signal/problem_statement.md`
- `benchmark_03_mixed_signal/llm_baseline_prompt.md`
- `benchmark_03_mixed_signal/llm_baseline_output_gemini_no_tools.md`
- `benchmark_03_mixed_signal/run_notes.md`
- `benchmark_03_mixed_signal/comparison.md`
- `benchmark_03_mixed_signal/artifacts/citt_generated_model.slx`
- `benchmark_03_mixed_signal/artifacts/benchmark_03_simulation_metrics.json`
- `benchmark_03_mixed_signal/artifacts/benchmark_03_simulation_report.md`
- `benchmark_03_mixed_signal/artifacts/benchmark_03_evidence_pack.md`
- `benchmark_03_mixed_signal/screenshots/09_highlight_command_path.png`
- `benchmark_03_mixed_signal/screenshots/10_highlight_adc_sampling_path.png`
- `benchmark_03_mixed_signal/screenshots/11_highlight_feedback_path.png`
- `benchmark_03_mixed_signal/screenshots/15_evidence_thread_exported.png`
- `benchmark_03_mixed_signal/plots/mixed_signal_full_timeline.png`
- `benchmark_03_mixed_signal/plots/membrane_voltage_and_clamp_current.png`
- `benchmark_03_mixed_signal/plots/amplifier_saturation.png`
- `benchmark_03_mixed_signal/plots/adc_codes_and_digital_logic.png`
- `benchmark_03_mixed_signal/plots/digital_state_machine_trace.png`
- `benchmark_03_mixed_signal/plots/parameter_sweep_heatmap.png`
- `benchmark_03_mixed_signal/plots/fault_injection_summary.png`

## Benchmark 1: RC Anti-Aliasing

CiTT parsed an ECG front-end RC low-pass filter problem, built/opened a Simscape model, captured a manually arranged model screenshot, taught the cutoff-frequency reasoning, highlighted the signal path, answered a natural-language probe, and generated Bode evidence.

Key evidence:

- `benchmark_01_textbook_rc/screenshots/03_simscape_model_arranged.png`
- `benchmark_01_textbook_rc/screenshots/04_teach_cutoff_formula.png`
- `benchmark_01_textbook_rc/screenshots/05_highlight_signal_path.png`
- `benchmark_01_textbook_rc/screenshots/06_probe_page.png`
- `benchmark_01_textbook_rc/plots/rc_bode_live.png`
- `benchmark_01_textbook_rc/plots/rc_bode_annotated.png`

Measured/derived values shown in the live probe evidence:

- `R = 39.8 kOhm`
- `C = 100 nF`
- `tau = 0.00398 s`
- `fc = 39.9887 Hz`
- `60 Hz = -5.1205 dB`
- `250 Hz = -16.0298 dB`

The annotated Bode plot also shows the 100 uF unit-mistake case, where the cutoff drops to about `0.03999 Hz` and the 5 Hz ECG component is attenuated by about `-41.94 dB`.

## Benchmark 2: TEVC Equilibrium

CiTT parsed the two-electrode voltage clamp equivalent circuit, treated omitted biological dynamics as modeling assumptions, and generated a Simscape-first physical electrical model using built-in MATLAB/Simulink/Simscape/Simscape Electrical blocks. The model includes command source, buffer path, finite-gain amplifier, `Ro`, `Rm`, symbolic `Re`, `VM_PROBE`, amplifier-output probe, clamp-current probe, electrical reference, and solver configuration.

Key evidence:

- `benchmark_02_tevc_equilibrium/screenshots/01_read_page.png`
- `benchmark_02_tevc_equilibrium/screenshots/03_simscape_model_arranged.png`
- `benchmark_02_tevc_equilibrium/screenshots/05_teach_reveal_feedback_loop.png`
- `benchmark_02_tevc_equilibrium/screenshots/06_teach_step2_vm.png`
- `benchmark_02_tevc_equilibrium/screenshots/10_probe_measure_probe_vm_explicit.png`
- `benchmark_02_tevc_equilibrium/screenshots/12_chat_probe_vm_restored.png`
- `benchmark_02_tevc_equilibrium/screenshots/13_latex_probe_restored.png`

Structural verification:

- SATK `model_check(root, all)` reported healthy.
- Focus map decoded with 5 focus items.
- Probe map decoded with 5 probe items.

Caveat:

- `V_c` and `R_e` remain symbolic because the benchmark does not provide numeric values. Numeric simulation/probe values require assigning those values first.

## Benchmark 3: Mixed-Signal Neural Clamp

CiTT built and opened a closed-loop mixed-signal neural clamp model, the user manually arranged the model, and the benchmark was rerun with a nominal educational parameter set. The resulting evidence includes model screenshots, command/ADC/feedback highlights, teaching/probe UI evidence, an exported evidence pack, Simulink/Simscape nominal timeline plots, and deterministic educational sweep/fault plots.

Key GUI evidence:

- `benchmark_03_mixed_signal/screenshots/06_model_after_user_arrangement.png`
- `benchmark_03_mixed_signal/screenshots/07_model_parameterized_after_simulation.png`
- `benchmark_03_mixed_signal/screenshots/08_citt_teach_probe_after_benchmark3_simulation.png`
- `benchmark_03_mixed_signal/screenshots/09_highlight_command_path.png`
- `benchmark_03_mixed_signal/screenshots/10_highlight_adc_sampling_path.png`
- `benchmark_03_mixed_signal/screenshots/11_highlight_feedback_path.png`
- `benchmark_03_mixed_signal/screenshots/15_evidence_thread_exported.png`

Simulation metrics from `benchmark_03_mixed_signal/artifacts/benchmark_03_simulation_metrics.json`:

- Simulation source: Simulink/Simscape model run.
- Settling time: not settled in the 60 ms window.
- Overshoot: `413.9 %`.
- Final tracking error: `186.2 mV`.
- Saturation duration: `60 ms`.
- Max clamp current: `5.099 nA`.
- Max amplifier output: `1 V`.
- Model warning: discontinuities in algebraic loops may prevent the algebraic loop solver from solving the loop.

Interpretation:

- The nominal generated model stays at rail/current limit and does not settle in the requested window. This is useful device-performance and limitation evidence for the product story, not a clinical validation claim.
- The failure to settle is an intended evidence point: it shows that the generated model exposes nonideal amplifier, current-limit, rail-saturation, and mixed-signal timing effects that a text-only LLM answer would likely miss or hand-wave.
- The plot set demonstrates transient behavior, ADC quantization, digital state, saturation, parameter sensitivity, and fault sensitivity.

## Gemini-Only Baseline Comparison

A Gemini-only no-tools baseline was run on the same three benchmark prompts. The baseline was instructed not to use MATLAB, Simulink, Simscape, SATK, Python, calculators, or executable tools.

On the textbook RC benchmark, Gemini-only performed well: it correctly estimated the cutoff frequency, attenuation at `5 Hz`, `60 Hz`, and Nyquist, and diagnosed the `100 uF` vs `100 nF` lab mistake. This shows that CiTT is not merely competing on simple arithmetic. CiTT's added value is model grounding: the same task produced an inspectable Simscape/Simulink model, visible probe location, focus-map teaching, natural-language probe output, Lab Delta/unit-mistake diagnosis, and annotated Bode evidence.

On the TEVC benchmark, Gemini-only gave a plausible feedback explanation and the correct tracking-ratio intuition. However, it mixed two limitations: it stated that both `Vc` and `Re` prevent a numerical `Vm`, while under the ideal-buffer assumption `Re` does not affect the DC tracking solution. Its formula formatting is also easy to misread. CiTT instead preserved symbolic parameters, built a Simscape-first model, and connected the feedback explanation to actual focus and probe maps.

On the mixed-signal neural-clamp benchmark, Gemini-only correctly stated that exact transients, ADC code sequences, saturation intervals, settling time, and overshoot require executable simulation. However, it also introduced unsupported assumptions and unit-scale errors, including writing a current limit as `nF` instead of `nA` and describing a `500 nF` capacitance fault as `500 uF` in one version. CiTT's advantage is therefore not that LLM reasoning is useless, but that Gemini-only reasoning lacks executable model grounding. CiTT adds Simscape/Simulink artifacts, highlightable model paths, probe maps, simulation plots, metrics JSON, warnings, and explicit limitation evidence.

## Probe And Lab Delta Status

Natural-language probe is demonstrated in the chat-style learning dialog, including `benchmark_02_tevc_equilibrium/screenshots/12_chat_probe_vm_restored.png`, `benchmark_02_tevc_equilibrium/screenshots/13_latex_probe_restored.png`, and Benchmark 3 teach/probe evidence.

Full Lab Delta CSV comparison was not completed because no real external lab CSV was supplied for this live pass. This is logged as a remaining limitation rather than claimed as completed evidence.

## What CiTT Demonstrates Beyond LLM-Only

CiTT produced inspectable MATLAB/Simulink/Simscape artifacts rather than only text explanations. The live workflow shows:

- model construction from circuit prompt/schematic,
- visible Simscape/Simulink diagrams,
- focus-map driven teaching highlights,
- probe-map driven natural-language measurement targets,
- exported evidence files that connect model, teaching, and probe outputs,
- simulation plots and failure/limitation evidence for the mixed-signal benchmark.

## Dependencies

The captured workflow depends on:

- MATLAB,
- Simulink,
- Simscape,
- Simscape Electrical,
- SATK/model tooling,
- CiTT MATLAB plugin,
- configured Gemini/Codex agent flow.

Default modeling assumption for these benchmarks: no custom Simscape libraries and no custom project-specific block libraries; use built-in MATLAB/Simulink/Simscape/Simscape Electrical blocks whenever possible.

## BMES Criteria Mapping

Product need:

- Students and instructors need an inspectable bridge from circuit descriptions to executable models and guided teaching steps.

Novelty:

- The workflow combines circuit parsing, Simscape-first build, model highlights, teaching prompts, natural-language probes, and evidence export in one MATLAB-centered tutor loop.

Technical feasibility:

- Benchmarks 1 and 2 demonstrate generated/opened models, captured GUI evidence, and probe/teaching interactions. Benchmark 3 adds a mixed-signal transient simulation with ADC/digital/saturation plots and model-limitation evidence.

Economic plan:

- The prototype leverages existing MATLAB/Simulink/Simscape infrastructure and focuses on educational workflow value rather than hardware deployment.

Clarity:

- Screenshots, run notes, comparison files, metrics JSON, plots, and artifact maps are stored with each benchmark for review.

## Limitations

- Benchmark 2 cannot produce numeric simulation values until numeric `V_c` and `R_e` are supplied.
- Benchmark 3 is educational and parameterized; it is not a clinically validated axon model.
- Benchmark 3 nominal model produced an algebraic-loop warning and did not settle in the 60 ms window, which should be presented as product-limitation evidence.
- The evidence view was fixed to expose the exported Evidence message in the chat thread; a stale verification text block from prior Bode work may still appear in one screenshot, so the authoritative Benchmark 3 export artifact is `benchmark_03_mixed_signal/artifacts/benchmark_03_evidence_pack.md`.
- Lab Delta CSV comparison was not completed as a full experimental-data workflow in this evidence pass.
