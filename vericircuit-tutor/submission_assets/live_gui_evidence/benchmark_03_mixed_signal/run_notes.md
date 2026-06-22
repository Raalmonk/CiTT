# CiTT Run Notes: Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic

manual_arrangement: completed-by-user
simulation_source: Simulink/Simscape model run
parameter_set: educational scaled benchmark parameters, not a validated axon or patient model
timestamp: 2026-06-22 13:18:33 *

Functional evidence now includes transient plots, ADC/digital logic plots, parameter sweep, and fault injection summary.
If the Simulink/Simscape model cannot execute in the local MATLAB install, the deterministic educational fallback is explicitly labeled in the report and plots are not represented as medical-use validation.

Live evidence status:

- User manually arranged the model before the final screenshots.
- Nominal timeline source: Simulink/Simscape model run.
- Parameter sweep and fault injection source: deterministic educational comparison equations using the same benchmark parameter set.
- Evidence pack: `artifacts/benchmark_03_evidence_pack.md`.
- Metrics: `artifacts/benchmark_03_simulation_metrics.json`.
- Simulation report: `artifacts/benchmark_03_simulation_report.md`.

Required highlights captured:

- Command path: `screenshots/09_highlight_command_path.png`
- ADC sampling path: `screenshots/10_highlight_adc_sampling_path.png`
- Feedback loop/path: `screenshots/11_highlight_feedback_path.png`

Evidence/export screenshot:

- `screenshots/15_evidence_thread_exported.png`

Key result:

- The nominal model does not settle within 60 ms and hits the voltage/current limits. This is presented as educational device-performance and limitation evidence, not medical-use validation.
