# Textbook-Inspired Plot Teaching Plan

## Why CiTT Should Teach With More Plots

The Webster medical instrumentation textbook rarely treats a circuit answer as a lonely number. It repeatedly teaches by moving through a chain:

1. Identify the physiological or physical measurand.
2. Choose the transducer or electrode interface.
3. Write the equivalent circuit or transfer model.
4. Check static levels, dynamic response, interference, noise, and safety limits.
5. Connect the result back to clinical or laboratory interpretation.

CiTT should mirror that method. A verified answer should open a visual lab, not just a derivation. The student should see what the circuit is doing across nodes, components, time, frequency, and biomedical constraints.

## Implemented Teaching Plot Types

- DC node voltage map: shows static levels relative to ground so students can see where the measurand lives.
- DC component current flow: shows signed currents using each component reference direction.
- DC power balance: makes source/load behavior and verification visible.
- AC magnitude response: shows Bode-style attenuation or gain across a sweep.
- AC phase response: makes timing distortion visible, not hidden behind magnitude-only answers.
- AC phasor magnitude and phase bars: gives single-frequency problems a compact visual comparison.
- RC transient voltage over time: connects initial condition, final value, and time response.
- Normalized RC settling plot: converts time into `t/tau`, matching the textbook's first-order-instrument teaching style.
- Differential vs common-mode input plot: emphasizes why biopotential amplifiers need high CMRR.
- Sampling and filter landmarks: shows cutoff, sampling rate, and Nyquist together for anti-aliasing discussion.
- Noise-budget bars: turns resistor, photodiode, and op-amp noise observations into visible design tradeoffs.
- CMRR mismatch what-if: shows how resistor mismatch can leak common-mode voltage into output.

## Product Behavior

The backend now emits a generic `teaching_plots` list on `SolutionPacket`. Each plot declares:

- title and subtitle
- plot type: `line` or `bar`
- source: DC, AC, transient, biomedical context, or verification
- axes and scaling
- series points
- optional markers such as cutoff frequency or one time constant
- a short insight explaining the teaching purpose

The frontend Lab panel renders these plots first. Older packets still fall back to the legacy sweep, transient, and phasor cards.

## Next Plot Ideas

- Tolerance sweeps for resistor/capacitor sensitivity.
- Electrode impedance versus frequency for biopotential recordings.
- Driven-right-leg common-mode reduction before/after plot.
- ADC quantization stair-step plot for low-amplitude biosignals.
- Op-amp output swing and slew-rate headroom plots.
- Bridge balance plot showing output versus small sensor resistance changes.
- KCL node-current stacked bars.
- Thermal, shot, and op-amp noise RSS contribution percentage plot.

## Teaching Rule

Every new plot should answer one student question:

- Where is the signal?
- What path does current take?
- What changes with frequency?
- What changes with time?
- What corrupts the measurement?
- What proves the result is safe or verified?

If a plot does not answer one of those questions, it should not be added to the default Lab view.
