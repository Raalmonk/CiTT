# Comparison: Mixed-Signal Neural Clamp

LLM-only text is not enough for this benchmark. The requested outputs depend on transient dynamics, saturation timing, ADC quantization, digital state transitions, parameter sweeps, and fault injection.

CiTT evidence now includes an educational scaled parameter set and executable simulation outputs. The parameter set is explicitly not a clinically validated axon model; it is chosen to make device-performance and limitation behavior visible for teaching and product evaluation.

Key proof artifacts: `mixed_signal_full_timeline.png`, `amplifier_saturation.png`, `adc_codes_and_digital_logic.png`, `parameter_sweep_heatmap.png`, and `fault_injection_summary.png`.

Live result summary:

- The nominal timeline was run through Simulink/Simscape.
- The generated model produced a visible limitation case: it did not settle within 60 ms, reached the amplifier rail, and hit the clamp-current limit.
- This result is valuable precisely because it exposes dynamic behavior and failure modes that a text-only LLM answer would likely smooth over or invent.

Baseline status:

- The LLM-only prompt is saved in `llm_baseline_prompt.md`.
- `llm_baseline_output.md` explicitly records that a verified no-tool baseline was not run in this environment.
- No LLM-only numeric result is claimed here.
