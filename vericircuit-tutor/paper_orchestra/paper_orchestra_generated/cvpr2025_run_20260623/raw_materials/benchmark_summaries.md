# Benchmark Summaries

## Benchmark 1: Textbook RC Anti-Aliasing

Task: an ECG-style first-order RC low-pass filter before a 500 Hz ADC, with R = 39.8 kOhm and C = 100 nF. The benchmark asks for cutoff frequency, attenuation at 60 Hz and Nyquist, probe placement, and a 100 uF versus 100 nF unit-mistake diagnosis.

CiTT evidence:

- Simscape model screenshot.
- Teaching screenshot explaining cutoff.
- Signal-path highlight.
- Natural-language probe screenshot.
- Live and annotated Bode plots.
- Derived values in report: tau = 0.00398 s, fc = 39.9887 Hz, 60 Hz attenuation = -5.1205 dB, 250 Hz attenuation = -16.0298 dB.

LLM-only baseline: performed well on hand calculation, but had no executable model, focus map, probe map, screenshots, or Simscape evidence.

## Benchmark 2: Two-Electrode Voltage Clamp Equilibrium

Task: simplified TEVC equivalent circuit with command source, ideal buffer, finite-gain amplifier A = 100, membrane/output resistances, symbolic electrode resistance, and membrane-voltage/clamp-current probes.

CiTT evidence:

- Generated Simscape-first model using built-in MATLAB/Simulink/Simscape/Simscape Electrical blocks.
- Arranged model screenshot.
- Feedback teaching and Vm teaching screenshots.
- Chat-style natural-language probe screenshots with LaTeX-style symbol rendering.
- Focus map with 5 focus items and probe map with 5 probe items.
- Structural model check reported healthy.

Caveat: V_c and R_e remain symbolic because the benchmark does not provide numeric values. Numeric simulation/probe values require assigning them.

LLM-only baseline: gave plausible conceptual reasoning but mixed the V_c and R_e limitation and lacked executable artifacts.

## Benchmark 3: Mixed-Signal Neural Clamp

Task: closed-loop mixed-signal neural clamp with membrane dynamics, electrode series resistance, finite-gain/nonideal amplifier, rail and current limits, ADC sampling/quantization, digital control state, saturation flags, settling time, overshoot, parameter sweep, and fault cases.

CiTT evidence:

- Generated/opened model and user-arranged model screenshot.
- Educational parameterized model screenshot after simulation.
- Command/ADC/feedback highlight screenshots.
- Teaching/probe UI evidence.
- Exported evidence pack.
- Timeline, membrane/clamp-current, amplifier saturation, ADC/digital, digital state, parameter-sweep, and fault-injection plots.
- Metrics: not settled in 60 ms, overshoot 413.9%, final tracking error 186.2 mV, saturation duration 60 ms, max clamp current 5.099 nA, max amplifier output 1 V.

Interpretation: the nominal model exposes limitations such as rail/current limit behavior and non-settling. This is useful educational limitation evidence, not a patient or biological validation.

LLM-only baseline: correctly said simulation was required, but introduced unit/model-assumption risks and produced no executable artifacts.
