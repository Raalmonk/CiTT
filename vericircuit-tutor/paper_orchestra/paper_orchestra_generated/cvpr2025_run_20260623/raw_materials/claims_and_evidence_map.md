# Claims And Evidence Map

| Claim | Evidence | Safe Language |
| --- | --- | --- |
| CiTT launches as a MATLAB plugin. | `matlab/citt.m`, `release/package_log.md`, `release/example_repro/installed_gui_smoke.png`. | "CiTT is a MATLAB-native plugin." |
| CiTT can package as a MATLAB toolbox. | `release/CiTT_BMES_2026.mltbx`, `release/package_log.md`. | "A reproducible `.mltbx` release candidate was created and smoke tested." |
| CiTT grounds tutoring in Simscape/Simulink artifacts. | Live evidence model screenshots and `.slx` artifacts for benchmarks 1-3. | "CiTT produced inspectable Simulink/Simscape artifacts in the live evidence pass." |
| CiTT supports focus/highlight teaching. | Focus maps and highlight screenshots in all benchmark evidence folders. | "Focus maps connect teaching steps to model regions." |
| CiTT supports natural-language probes. | Probe screenshots in Benchmark 1/2 and Benchmark 3 teach/probe evidence. | "Natural-language probe evidence is demonstrated in the learning dialog." |
| LLM-only can solve simple RC arithmetic. | Gemini-only baseline output for Benchmark 1 and report. | "Gemini-only performed well on the textbook RC arithmetic." |
| LLM-only lacks executable artifacts. | Baseline prompt constraints and no-tool outputs. | "The no-tools baseline did not produce MATLAB/Simscape artifacts." |
| Benchmark 3 exposes model limitations. | Metrics JSON and simulation report: non-settling, saturation, algebraic-loop warning. | "Benchmark 3 demonstrates limitation discovery under educational scaled parameters." |
| Lab Delta full CSV workflow is incomplete. | Evidence report Lab Delta status. | "Full Lab Delta CSV comparison remains pending without external CSV data." |

## Claims To Avoid

- Do not claim patient, diagnostic, therapeutic, or clinical use.
- Do not claim Benchmark 3 is a real biological or patient model.
- Do not claim Lab Delta CSV comparison is complete.
- Do not claim the Gemini-only baseline is exhaustive.
- Do not describe the paper as ready for a real CVPR submission.
