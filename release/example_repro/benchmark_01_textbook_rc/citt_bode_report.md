# CiTT Bode Analysis

- JSON: release/example_repro/benchmark_01_textbook_rc/citt_bode_report.json
- Plot: release/example_repro/benchmark_01_textbook_rc/citt_bode_plot.png
- Model: release/example_repro/benchmark_01_textbook_rc/rc_reproduced_model.slx
- Spec: release/example_repro/benchmark_01_textbook_rc/citt_spec_reproduced.json

## Curves

| Curve | Source | Input | Output | Cutoff / Pole | Notes |
| --- | --- | --- | --- | --- | --- |
| LOWPASS RC estimate from R1 and C1 | analytic_spec | spec input | spec output | 39.9887 Hz | Computed from numeric R and C values in the circuit spec. This is an analytic first-order estimate, not a full Simscape linearization. |

## Messages

- No linearization I/O paths were provided. Pass InputPath and OutputPathBlock for full Simulink Bode.

## Next Action

- Use the analytic Bode as a sanity check, then add Simulink linearization I/O points for full model response.