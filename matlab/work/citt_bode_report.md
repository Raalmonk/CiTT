# CiTT Bode Analysis

- JSON: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_bode_report.json
- Plot: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_bode_plot.png
- Model: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_generated_model.slx
- Spec: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_last_circuit_spec.json

## Curves

| Curve | Source | Input | Output | Cutoff / Pole | Notes |
| --- | --- | --- | --- | --- | --- |
| LOWPASS RC estimate from RF and CF | analytic_spec | spec input | spec output | 15.9155 Hz | Computed from numeric R and C values in the circuit spec. This is an analytic first-order estimate, not a full Simscape linearization. |

## Messages

- No linearization I/O paths were provided. Pass InputPath and OutputPathBlock for full Simulink Bode.

## Next Action

- Use the analytic Bode as a sanity check, then add Simulink linearization I/O points for full model response.