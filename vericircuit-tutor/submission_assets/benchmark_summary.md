# Benchmark Summary

This package contains three benchmark cases intended to show why CiTT should be judged as a model-grounded biomedical circuit tutor rather than an LLM-only answer generator.

1. RC anti-aliasing: shows a textbook calculation with cutoff, attenuation, Nyquist warning, probe location, and Lab Delta for a capacitor unit mistake.
2. TEVC equilibrium feedback: shows BME relevance, feedback-loop explainability, probes, and explicit treatment of biological simplifications as assumptions.
3. Mixed-signal neural clamp: shows why transient behavior, amplifier saturation, ADC quantization, digital state logic, parameter sweeps, and fault injection require simulation.

Current run status:
- Analytical/offline plots were generated for benchmarks 1 and 2.
- Illustrative surrogate plots were generated for benchmark 3 and labeled accordingly.
- Live Simscape/SATK model screenshots and simulations remain pending.
- LLM-only baselines remain manual-pending.
