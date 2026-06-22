# Benchmark Scorecard

Scores are for the current live evidence package. LLM-only baselines are kept as `live-not-run` because no verified pure no-tool baseline invocation was rerun during this evidence pass. Do not fabricate those scores.

| Benchmark | System | Status | Topology | Numerical | Units | Executable | Teaching | Limits | Total |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| benchmark_01_textbook_rc | LLM-only | live-not-run |  |  |  |  |  |  |  |
| benchmark_01_textbook_rc | CiTT live GUI | live-complete | 3 | 3 | 3 | 3 | 3 | 3 | 18 |
| benchmark_02_tevc_equilibrium | LLM-only | live-not-run |  |  |  |  |  |  |  |
| benchmark_02_tevc_equilibrium | CiTT live GUI | live-structural-teaching-complete-symbolic-numeric-limited | 3 | 1 | 2 | 3 | 3 | 3 | 15 |
| benchmark_03_mixed_signal_simscape | LLM-only | live-not-run |  |  |  |  |  |  |  |
| benchmark_03_mixed_signal_simscape | CiTT live GUI | live-parameterized-simulation-complete-educational | 3 | 2 | 2 | 3 | 2 | 3 | 15 |

## Notes

- Benchmark 1 includes live model evidence, teaching evidence, natural-language probe output, and Bode plots.
- Benchmark 2 includes live model evidence, focus/probe maps, teaching evidence, and chat-style natural-language probe output. Numeric simulation remains limited because the prompt leaves `V_c` and `R_e` symbolic.
- Benchmark 3 includes live model evidence, user-arranged Simulink/Simscape screenshot, command/ADC/feedback highlights, evidence export, nominal Simulink/Simscape timeline simulation, and educational sweep/fault plots. It is explicitly not clinical validation.
- Full Lab Delta CSV comparison is not scored as completed because no real external lab CSV was supplied.
