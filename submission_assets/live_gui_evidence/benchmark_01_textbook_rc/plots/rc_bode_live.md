# CiTT Bode Analysis

- JSON: submission_assets/live_gui_evidence/benchmark_01_textbook_rc/plots/rc_bode_live.json
- Plot: submission_assets/live_gui_evidence/benchmark_01_textbook_rc/plots/rc_bode_live.png
- Model: matlab/work/citt_generated_model.slx
- Spec: matlab/work/citt_last_circuit_spec.json

## Curves

| Curve | Source | Input | Output | Cutoff / Pole | Notes |
| --- | --- | --- | --- | --- | --- |
| LOWPASS RC estimate from R1 and C1 | analytic_spec | spec input | spec output | 39.9887 Hz | Computed from numeric R and C values in the circuit spec. This is an analytic first-order estimate, not a full Simscape linearization. |

## Messages

- No linearization I/O paths were provided. Pass InputPath and OutputPathBlock for full Simulink Bode.

## Next Action

- Use the analytic Bode as a sanity check, then add Simulink linearization I/O points for full model response.