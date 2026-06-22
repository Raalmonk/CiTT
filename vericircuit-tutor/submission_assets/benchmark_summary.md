# Benchmark Summary

This package contains three benchmark cases intended to show why CiTT should be judged as a model-grounded biomedical circuit tutor rather than an LLM-only answer generator.

Final evidence lives under `live_gui_evidence/`.

## Benchmarks

1. RC anti-aliasing: proves basic numerical correctness, model-grounded teaching, natural-language probe output, and Bode evidence for a textbook biomedical signal-conditioning circuit.
2. TEVC equilibrium feedback: proves BME relevance, feedback-loop explainability, symbolic assumption handling, and Simscape-first model structure for a simplified biological-equivalent circuit.
3. Mixed-signal neural clamp: stress-tests CiTT on transient behavior, finite-gain amplifier limits, ADC quantization, digital state logic, saturation, parameter sweeps, and fault injection.

## Current Live Evidence Status

- Benchmark 1 live evidence is complete.
- Benchmark 2 live structural/teaching/probe evidence is complete; numeric simulation remains intentionally limited because `V_c` and `R_e` are symbolic in the prompt.
- Benchmark 3 live evidence is complete as an educational scaled benchmark: the nominal timeline was run through Simulink/Simscape, and sweep/fault plots were generated as deterministic educational comparisons.
- LLM-only baseline prompts are saved, but verified no-tool baseline outputs were not rerun in this pass.

## Submission Story

Use the three benchmarks as:

- Main correctness evidence: Benchmark 1.
- Main BME feedback/modeling evidence: Benchmark 2.
- Stress-test and limitation evidence: Benchmark 3.

Benchmark 3 should be described carefully: CiTT did not prove a high-performing neural clamp design. It generated and analyzed a complex mixed-signal model, revealing non-settling, rail saturation, current-limit behavior, ADC/digital timing, and parameter/fault sensitivity. That is the product value: executable Simscape/Simulink evidence catches dynamics a text-only LLM answer would likely miss or hand-wave.
