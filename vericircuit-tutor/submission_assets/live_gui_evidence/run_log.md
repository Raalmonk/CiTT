# Live GUI Evidence Run Log

## 2026-06-22

- Opened MATLAB and launched CiTT with `addpath("/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/matlab"); citt`.
- Captured initial CiTT app screenshot at `screenshots/00_app_open.png`.
- Found the app restored a previous pacemaker task on launch. Continued by creating a new task for Benchmark 1.
- macOS blocked direct coordinate clicking via System Events because assistive access is not allowed.
- Fixed a practical test/control issue by adding CiTT `TestHooks` for visible app actions: new task, set prompt/image, navigate, read, prepare build, build model, and open model.
- Parsed Benchmark 1 RC anti-aliasing prompt through the visible CiTT app session.
- Fixed a build-readiness issue: text-only prompts with "no image attached" were incorrectly treated as blocking unsupported regions. These are now non-blocking modeling boundaries.
- Prepared the build brief through the visible CiTT app session.
- Started the model build through CiTT's Build Model callback. The external Codex/SATK agent generated fresh live artifacts:
  - `/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/matlab/work/citt_generated_model.slx`
  - `/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/matlab/work/citt_focus_map.json`
  - `/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/matlab/work/citt_probe_map.json`
  - `/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/matlab/work/citt_agent_report.md`
- Opened the generated Simulink/Simscape model through CiTT's Open Model callback.
- Captured an unarranged model proof screenshot at `benchmark_01_textbook_rc/screenshots/03_simscape_model_open_pre_arrangement.png`.
- Stopped before manual arrangement as required.
- User manually arranged and saved the RC Simulink/Simscape model.
- Captured arranged model screenshot at `benchmark_01_textbook_rc/screenshots/03_simscape_model_arranged.png`.
- Ran CiTT Teach and captured:
  - `benchmark_01_textbook_rc/screenshots/04_teach_page.png`
  - `benchmark_01_textbook_rc/screenshots/04_teach_cutoff_formula.png`
- Observed that the HTML CiTT app does not currently include MathJax/KaTeX or the old LaTeX preview renderer. The cutoff step shows formula-related reasoning in plain text, not rendered LaTeX.
- Ran CiTT focus highlight for `fp_cutoff_frequency` and captured `benchmark_01_textbook_rc/screenshots/05_highlight_signal_path.png`.
- Ran CiTT natural-language Probe for nominal filtered output. Probe target selection and highlighting succeeded, but numeric measurement summary remained preview-only because source amplitudes/phases are preserved as named parameters.
- Fixed stale hard-coded probe placeholder text in `resources/ui/citt_app.html`; it now says `Measure a model signal in plain language`.
- Captured refreshed probe screenshot at `benchmark_01_textbook_rc/screenshots/06_probe_page.png`.
- Generated CiTT Bode plot evidence at `benchmark_01_textbook_rc/plots/rc_bode_live.png`.
- Benchmark 1 screenshots are complete for the live GUI workflow.

Previously observed UI issues:
- The HTML app title/status updated correctly, but the main page body sometimes remained on the teaching/model-preview layout after navigation. This was logged; it did not prevent model generation/opening.
- HTML Teach initially lacked visible rendered formula output for the RC cutoff step; this is fixed in the refresh below.

## 2026-06-22 Fix Refresh

- Fixed RC Teach reveal text so the cutoff step emits formula-bearing content through the existing HTML rich-text/LaTeX renderer.
- Fixed natural-language Probe measurement for RC parameter/frequency-response probes. The command `measure cutoff frequency and attenuation at 60 Hz and 250 Hz` now matches `probe_frequency_attenuation_checks`, reads `R1_39p8k.R` and `C1_100nF.c`, and prints numeric results back into the learning/probe dialog.
- Refreshed screenshots:
  - `screenshots/04_teach_page.png`
  - `benchmark_01_textbook_rc/screenshots/04_teach_cutoff_formula.png`
  - `screenshots/06_probe_page.png`
  - `benchmark_01_textbook_rc/screenshots/06_probe_page.png`
- Verified visible Probe output: `fc = 39.9887 Hz`, `5 Hz = -0.0674 dB`, `60 Hz = -5.1205 dB`, and `250 Hz = -16.0298 dB`.
- Refreshed Benchmark 1 plot evidence with annotated Bode diagnostics at `benchmark_01_textbook_rc/plots/rc_bode_annotated.png`. The plot marks 5 Hz ECG, 60 Hz interference, 250 Hz Nyquist, nominal cutoff, and the 100 uF lab-mistake cutoff.

## 2026-06-22 Benchmark 2 TEVC

- Ran Benchmark 2 TEVC equilibrium workflow in the visible CiTT/MATLAB session.
- Parsed TEVC prompt and schematic; biological simplifications were treated as assumptions rather than blockers.
- Built a Simscape-first TEVC model using built-in MATLAB/Simulink/Simscape/Simscape Electrical blocks.
- Preserved `V_c` and `R_e` as symbolic parameters because the benchmark does not provide numeric values.
- Captured Benchmark 2 read, build, arranged Simulink model, teaching, highlight, and natural-language probe screenshots under `benchmark_02_tevc_equilibrium/screenshots/`.
- User manually dragged/arranged the TEVC model view; refreshed `benchmark_02_tevc_equilibrium/screenshots/03_simscape_model_arranged.png` and `benchmark_02_tevc_equilibrium/screenshots/11_after_manual_drag_citt_window.png`.
- Added `workflow_total_prompt.md`, `llm_baseline_prompt.md`, `comparison.md`, and `run_notes.md` for Benchmark 2.
- Reverted an overcorrection that exposed `Probe, lab delta, evidence` as a tool panel. The intended UI remains the Codex-style learning dialog: model on top, teaching/probe chat below.
- Captured restored chat-style probe evidence at `benchmark_02_tevc_equilibrium/screenshots/12_chat_probe_vm_restored.png`.
- Restored LaTeX-style rendering for TEVC teaching/probe text by converting bare circuit symbols such as `Vm`, `R_e`, `R_o`, `R_m`, and `V_c` before rich-text rendering, and by rendering probe results as rich text instead of plain text.
- Captured LaTeX-restored probe screenshot at `benchmark_02_tevc_equilibrium/screenshots/13_latex_probe_restored.png`.
- Created final live evidence report at `bmes_live_evidence_report.md`.
