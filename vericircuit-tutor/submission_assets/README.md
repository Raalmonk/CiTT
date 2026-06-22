# CiTT BMES/Medtronic Submission Assets

This directory contains both legacy offline draft assets and the final live GUI evidence package for CiTT, a model-grounded AI tutor for biomedical circuit simulation.

Use this as the final submission evidence entry point:

- `live_gui_evidence/bmes_live_evidence_report.md`
- `live_gui_evidence/README.md`
- `live_gui_evidence/screenshots/`
- `live_gui_evidence/benchmark_01_textbook_rc/`
- `live_gui_evidence/benchmark_02_tevc_equilibrium/`
- `live_gui_evidence/benchmark_03_mixed_signal/`

Do not use older offline draft reports, offline screenshots, or generated placeholder panels as final proof unless they are explicitly labeled as draft/background material.

## Final Live Evidence Status

- Benchmark 1 RC anti-aliasing: live model, teaching, highlight, natural-language probe, and Bode evidence are complete.
- Benchmark 2 TEVC equilibrium: live Simscape-first structure, feedback teaching, highlight, symbolic caveat, and natural-language probe evidence are complete.
- Benchmark 3 mixed-signal neural clamp: live generated model, user-arranged model screenshot, educational scaled parameter set, nominal Simulink/Simscape timeline simulation, command/ADC/feedback highlights, plots, metrics, and evidence pack are complete.

Benchmark 3 is **educational scaled benchmark evidence, not a clinically validated axon model**. Its value is that simulation exposes non-settling, rail saturation, current-limit behavior, ADC/digital timing, and parameter/fault sensitivity that text-only LLM output should not be trusted to infer.

## Legacy Draft Assets

The following root-level or source benchmark folders are useful for provenance, but are not the final evidence package:

- `bmes_evidence_report_OFFLINE_DRAFT.md` and `.pdf`
- `benchmark_run_log.md`
- `figures/`
- `screenshots/`
- `benchmark_01_textbook_rc/`
- `benchmark_02_tevc_equilibrium/`
- `benchmark_03_mixed_signal_simscape/`
- `scripts/generate_offline_assets.py`

These older assets may mention offline panels, illustrative surrogate plots, or pending live Simscape evidence. Those statements describe the earlier draft package, not the current live evidence pass.

## Scorecard

`benchmark_scorecard.md` and `benchmark_scorecard.csv` are internal evidence rubrics. They are useful for tracking which proof items exist, but should not be presented as an objective external score.

LLM-only baselines are marked `live-not-run` because no verified pure no-tool baseline invocation was rerun during this evidence pass. No baseline output or score is fabricated.

## Reproduction Notes

Full live reproduction requires:

- MATLAB
- Simulink
- Simscape
- Simscape Electrical
- Simulink Agentic Toolkit / SATK-compatible model build flow
- MATLAB MCP Server
- Gemini API key for circuit parsing, where configured
- SATK-configured agent CLI via `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

The old offline generator can still regenerate draft assets:

```bash
python3 vericircuit-tutor/submission_assets/scripts/generate_offline_assets.py --mode all
```

Do not run the offline generator as final submission proof. Use `live_gui_evidence/` for the final evidence story.
