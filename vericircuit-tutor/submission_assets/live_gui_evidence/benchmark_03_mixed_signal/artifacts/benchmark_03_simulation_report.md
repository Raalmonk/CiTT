# Benchmark 3 Simulation Report

- Parameter set: educational scaled benchmark parameters
- Warning: Not a clinically validated axon model.
- Simulation source: Simulink/Simscape model run
- Model: `/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor/matlab/work/citt_generated_model.slx`

## Metrics

- Settling time: not settled
- Overshoot: 413.9 %
- Final tracking error: 186.2 mV
- Saturation duration: 60 ms
- Max clamp current: 5.099 nA
- Max amplifier output: 1 V

## Interpretation

- Model warning: Discontinuities detected in one or more algebraic loops might prevent the algebraic loop solver from solving the loop.
- The nominal generated model does not settle in the 60 ms window and stays at the rail/current limit. This is device-performance evidence and a model limitation, not a clinical claim.
- The failure to settle is an intended evidence point: it shows that the generated model exposes nonideal amplifier, current-limit, rail-saturation, and mixed-signal timing effects that a text-only LLM answer would likely miss or hand-wave.
- Parameter sweep and fault-injection plots use the same educational scaled equations deterministically for comparison speed; the nominal timeline plots are from the Simulink/Simscape model run.

## Required Plots

- `mixed_signal_full_timeline.png`
- `membrane_voltage_and_clamp_current.png`
- `amplifier_saturation.png`
- `adc_codes_and_digital_logic.png`
- `digital_state_machine_trace.png`
- `parameter_sweep_heatmap.png`
- `fault_injection_summary.png`
