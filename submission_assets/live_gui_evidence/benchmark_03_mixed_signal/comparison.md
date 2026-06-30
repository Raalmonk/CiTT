# Comparison: Mixed-Signal Neural Clamp

Benchmark 3 is the strongest baseline contrast because the requested outputs depend on transient dynamics, saturation timing, ADC quantization, digital state transitions, parameter sweeps, and fault injection.

CiTT evidence includes an educational scaled parameter set and executable simulation outputs. The parameter set is explicitly not a clinically validated axon model; it is chosen to make device-performance and limitation behavior visible for teaching and product evaluation.

Key proof artifacts: `mixed_signal_full_timeline.png`, `amplifier_saturation.png`, `adc_codes_and_digital_logic.png`, `parameter_sweep_heatmap.png`, and `fault_injection_summary.png`.

## CiTT Live Result Summary

- The nominal timeline was run through Simulink/Simscape.
- The generated model produced a visible limitation case: it did not settle within `60 ms`, reached the amplifier rail, and hit the clamp-current limit.
- The live metrics record non-settling, overshoot, tracking error, saturation duration, clamp current, and amplifier output.
- This result is valuable precisely because it exposes dynamic behavior and failure modes that a text-only answer could smooth over or invent.

## Text-Only No-Tools Baseline

Baseline prompt saved in `llm_baseline_prompt.md`.

The text-only baseline correctly states that exact values require executable simulation:

- exact `Vm(t)`,
- clamp-current waveform,
- ADC code sequence,
- saturation intervals,
- settling time,
- overshoot.

This supports CiTT's core value: model-grounded evidence is necessary for complex mixed-signal cases.

## Text-Only Issues

The text-only response is useful, but it shows risks that should be called out:

- Unit slip: it writes the current limit as `nF` instead of `nA` in one version.
- Unsupported model assumption: it describes the nonlinear membrane current as exponential even though the prompt only specifies a maximum, threshold, and slope.
- Capacitance-scale error: it describes the `500 nF` fault as `500 uF` and a `1e6` scale change in one version, while the benchmark fault is `500e-9 F`, or `500 nF`, which is `1000x` nominal `500 pF`.
- Over-strong qualitative claim: it says low ADC rate will likely cause severe oscillations or limit cycles. A more careful no-tools statement is that lower sampling may reduce phase margin and can cause poor settling or oscillation depending on loop dynamics.

## Observed Difference

Text-only reasoning correctly recognizes the need for simulation but cannot produce executable proof. CiTT adds Simscape/Simulink artifacts, highlightable model paths, probe maps, simulation plots, metrics JSON, model warnings, and explicit limitation evidence.

CiTT Benchmark 3 should not be presented as a perfect design success. It is stronger as evidence that the workflow exposes non-settling, saturation, current limits, ADC/digital timing, and model warnings instead of hiding them.
