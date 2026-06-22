# CiTT BMES Live GUI Evidence Report

Generated: 2026-06-22

## Scope

This report summarizes real MATLAB/CiTT/Simulink GUI evidence captured under `vericircuit-tutor/submission_assets/live_gui_evidence/`.

Completed live GUI evidence:
- Benchmark 1: Textbook RC anti-aliasing.
- Benchmark 2: Two-electrode voltage clamp equilibrium.

Optional complex demo:
- Benchmark 3 mixed-signal neural clamp is not complete and is not claimed as completed evidence.

## Evidence Index

Global screenshots:
- `screenshots/00_app_open.png`: CiTT app opened in MATLAB.
- `screenshots/01_read_page.png`: live read/parse page.
- `screenshots/02_build_page.png`: live build page.
- `screenshots/03_simscape_model_arranged.png`: arranged Simscape/Simulink model evidence.
- `screenshots/04_teach_page.png`: teaching UI evidence.
- `screenshots/05_highlight_feedback_or_signal_path.png`: highlight evidence.
- `screenshots/06_probe_page.png`: natural-language probe evidence.
- `benchmark_02_tevc_equilibrium/screenshots/12_chat_probe_vm_restored.png`: natural-language probe invoked from the dialog with result printed back into the dialog.

Benchmark 1 folder:
- `benchmark_01_textbook_rc/run_notes.md`
- `benchmark_01_textbook_rc/comparison.md`
- `benchmark_01_textbook_rc/llm_baseline_prompt.md`
- `benchmark_01_textbook_rc/screenshots/`
- `benchmark_01_textbook_rc/plots/rc_bode_live.png`
- `benchmark_01_textbook_rc/plots/rc_bode_annotated.png`

Benchmark 2 folder:
- `benchmark_02_tevc_equilibrium/run_notes.md`
- `benchmark_02_tevc_equilibrium/comparison.md`
- `benchmark_02_tevc_equilibrium/llm_baseline_prompt.md`
- `benchmark_02_tevc_equilibrium/workflow_total_prompt.md`
- `benchmark_02_tevc_equilibrium/screenshots/`
- `benchmark_02_tevc_equilibrium/artifacts/citt_generated_model_tevc.slx`

## Benchmark 1: RC Anti-Aliasing

CiTT parsed an ECG front-end RC low-pass filter problem, built/opened a Simscape model, captured a manually arranged model screenshot, taught the cutoff-frequency reasoning, highlighted the signal path, and answered a natural-language probe.

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

Annotated Bode evidence:
- The nominal 100 nF filter preserves the 5 Hz ECG component at about `-0.067 dB`.
- The 100 uF mistake moves cutoff to about `0.03999 Hz` and attenuates the 5 Hz ECG component by about `-41.94 dB`.
- The single nominal RC pole only gives about `-16.03 dB` at the 250 Hz Nyquist frequency, demonstrating why one pole is weak as an anti-aliasing filter.

## Benchmark 2: TEVC Equilibrium

CiTT parsed the two-electrode voltage clamp equivalent circuit, treated omitted biological dynamics as modeling assumptions, and generated a Simscape-first physical electrical model. The model includes command source, buffer path, finite-gain amplifier, `Ro`, `Rm`, symbolic `Re`, `VM_PROBE`, amplifier-output probe, clamp-current probe, electrical reference, and solver configuration.

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

## What CiTT Demonstrates Beyond LLM-Only

CiTT produced inspectable MATLAB/Simulink/Simscape artifacts rather than only text explanations. The live workflow shows:
- model construction from circuit prompt/schematic,
- visible Simscape/Simulink diagrams,
- focus-map driven teaching highlights,
- probe-map driven natural-language measurement targets,
- evidence files that connect model, teaching, and probe outputs.

The LLM-only baseline prompts are saved, but raw baseline outputs are not fabricated.

## Dependencies

The captured workflow depends on:
- MATLAB,
- Simulink,
- Simscape,
- Simscape Electrical,
- SATK/model tooling,
- CiTT MATLAB plugin,
- Gemini/Codex agent flow where configured.

## BMES Criteria Mapping

Product need:
- Students and instructors need an inspectable bridge from circuit descriptions to executable models and guided teaching steps.

Novelty:
- The workflow combines circuit parsing, Simscape-first build, model highlights, teaching prompts, and natural-language probes in one MATLAB-centered tutor loop.

Technical feasibility:
- Benchmarks 1 and 2 demonstrate generated/opened models, captured GUI evidence, and probe/teaching interactions.

Economic plan:
- The prototype leverages MATLAB/Simulink/Simscape infrastructure and focuses on educational workflow value rather than hardware deployment.

Clarity:
- Screenshots, run notes, comparison files, and artifact maps are stored with each benchmark for review.

## Limitations

- Benchmark 3 is not complete.
- Benchmark 2 cannot produce numeric simulation values until numeric `V_c` and `R_e` are supplied.
- The HTML UI required fixes for evidence-view navigation and has known layout rough edges.
- Lab Delta CSV comparison was not completed as a full experimental-data workflow in this evidence pass.
