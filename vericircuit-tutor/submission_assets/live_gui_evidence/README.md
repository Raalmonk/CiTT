# CiTT Live GUI Evidence

This folder is for real MATLAB/CiTT/Simulink GUI evidence only.

Offline draft assets remain outside this folder and are not final submission proof. Screenshots here should come from the visible MATLAB app, CiTT UI, opened Simulink/Simscape models, or generated plots tied to the live benchmark run.

Current checkpoint:

- Benchmark 1 RC anti-aliasing has been generated, opened, arranged, taught, highlighted, probed, plotted, and captured.
- Benchmark 2 TEVC equilibrium has been generated, opened, manually arranged by the user, taught, highlighted, probed in the chat-style dialog, and captured.
- Benchmark 3 mixed-signal neural clamp has been generated, opened, manually arranged by the user, parameterized with educational scaled benchmark parameters, simulated for the nominal Simulink/Simscape timeline, highlighted for command/ADC/feedback paths, plotted, and exported as an evidence pack.
- Probe evidence is captured in the Codex-style learning dialog, especially `benchmark_02_tevc_equilibrium/screenshots/12_chat_probe_vm_restored.png`, `benchmark_02_tevc_equilibrium/screenshots/13_latex_probe_restored.png`, and `benchmark_03_mixed_signal/screenshots/08_citt_teach_probe_after_benchmark3_simulation.png`.
- Benchmark 3 evidence export is captured at `benchmark_03_mixed_signal/screenshots/15_evidence_thread_exported.png`, with the exported pack at `benchmark_03_mixed_signal/artifacts/benchmark_03_evidence_pack.md`.
- Final live evidence report is `bmes_live_evidence_report.md`.

Important honesty notes:

- Benchmark 3 uses educational scaled benchmark parameters, not a clinically validated axon model.
- Benchmark 3 nominal timeline plots are from a Simulink/Simscape model run; parameter-sweep and fault-injection comparison plots are deterministic educational comparisons.
- LLM-only baseline prompts are saved, but the live pass did not rerun verified no-tool baseline outputs. Do not treat legacy source-folder baseline outputs as live evidence.
- Full Lab Delta CSV comparison is not completed in this live pass because no real external lab CSV was supplied.
