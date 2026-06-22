# Benchmark Scorecard

Scores are an internal benchmark rubric for submission evidence. Gemini-only was run without MATLAB, Simulink, Simscape, SATK, Python, calculators, or executable tools. The scores should not be presented as a formal clinical validation result.

| Benchmark | System | Status | Topology | Numerical | Units | Executable | Teaching | Limits | Total |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| benchmark_01_textbook_rc | Gemini-only no-tools | completed | 3 | 4 | 3 | 0 | 2 | 2 | 14 |
| benchmark_01_textbook_rc | CiTT live GUI | live-complete | 3 | 3 | 3 | 3 | 3 | 3 | 18 |
| benchmark_02_tevc_equilibrium | Gemini-only no-tools | completed | 3 | 2 | 2 | 0 | 2 | 2 | 11 |
| benchmark_02_tevc_equilibrium | CiTT live GUI | live-structural-teaching-complete-symbolic-numeric-limited | 3 | 1 | 2 | 3 | 3 | 3 | 15 |
| benchmark_03_mixed_signal_simscape | Gemini-only no-tools | completed | 3 | 1 | 1 | 0 | 2 | 2 | 9 |
| benchmark_03_mixed_signal_simscape | CiTT live GUI | live-parameterized-simulation-complete-educational | 3 | 2 | 2 | 3 | 2 | 3 | 15 |

## Notes

- Benchmark 1 Gemini-only calculates the RC values well, so numerical score is high. It still receives `0` for executable evidence because it has no model, screenshots, focus map, probe map, or simulation artifacts.
- Benchmark 1 CiTT live GUI adds model grounding, visible probe placement, focus-map teaching, natural-language probe output, Lab Delta/unit-mistake diagnosis, and annotated Bode evidence.
- Benchmark 2 Gemini-only explains the TEVC feedback concept well, but it mixes the `Vc` and `Re` limitation and its formula formatting is easy to misread.
- Benchmark 2 CiTT live GUI includes model evidence, focus/probe maps, teaching evidence, and chat-style natural-language probe output. Numeric simulation remains limited because `V_c` and `R_e` are symbolic in the source benchmark.
- Benchmark 3 Gemini-only correctly says executable simulation is needed, but it shows unit/model-assumption risks on complex mixed-signal reasoning.
- Benchmark 3 CiTT live GUI is not scored as perfect because the generated model shows non-settling, saturation, and an algebraic-loop warning. It scores high for executable evidence because those limitations are captured as model artifacts, plots, metrics, and screenshots.
- Full Lab Delta CSV comparison is not scored as completed because no real external lab CSV was supplied.
