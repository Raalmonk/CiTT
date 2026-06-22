# CiTT BMES/Medtronic Submission Evidence Package

This directory contains a benchmark evidence package for CiTT: a model-grounded AI tutor for biomedical circuit simulation.

Contents:
- `figures/`: architecture, workflow, score, and BMES-alignment visuals.
- `screenshots/`: offline CiTT app evidence panels. Replace with live MATLAB app screenshots before final submission when possible.
- `benchmark_01_textbook_rc/`: textbook RC anti-aliasing benchmark.
- `benchmark_02_tevc_equilibrium/`: simplified TEVC equilibrium feedback benchmark.
- `benchmark_03_mixed_signal_simscape/`: mixed physical/digital neural clamp benchmark.
- `benchmark_scorecard.csv` and `.md`: honest current scoring.
- `bmes_evidence_report.md` and `.pdf`: submission-facing report.
- `scripts/`: MATLAB wrappers plus the offline generator used in this environment.

Required live environment for the full CiTT evidence run:
- MATLAB
- Simulink
- Simscape
- Simscape Electrical preferred
- Simulink Agentic Toolkit initialized with SATK policy/library gates
- MATLAB MCP Server
- Gemini API key for circuit parsing
- SATK-configured agent CLI via `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

Reproduce offline package:

```bash
python3 vericircuit-tutor/submission_assets/scripts/generate_offline_assets.py --mode all
```

Reproduce from MATLAB:

```matlab
run("vericircuit-tutor/submission_assets/scripts/run_all_benchmarks.m")
```

Manual Simscape arrangement pause:
After live model generation, the MATLAB workflow must open the model and pause with the required `PAUSE FOR MANUAL SIMSCAPE ARRANGEMENT` message. The user should drag and clean up the diagram, save it, then press Enter. Screenshots should be captured only after that pause.

Provenance in this run:
- RC and TEVC plots are analytical/offline.
- Mixed-signal plots are illustrative surrogate data and explicitly labeled.
- App/model screenshot PNGs are offline panels, not live MATLAB screenshots.
- LLM baseline prompts are prepared, but baseline outputs are manual-pending because no pure no-tool baseline invocation was executed.
