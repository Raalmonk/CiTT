# Textbook RC Anti-Aliasing Filter Before an ADC

An ECG acquisition front end uses a first-order RC low-pass filter before a 500 Hz ADC. The circuit uses R = 39.8 kOhm and C = 100 nF. The input contains a 5 Hz ECG-like component, 60 Hz interference, and optional high-frequency noise.

Tasks:
1. Compute the cutoff frequency.
2. Compute attenuation at 60 Hz.
3. Compute attenuation at the Nyquist frequency.
4. Explain whether a single-pole RC filter is sufficient for anti-aliasing.
5. Identify where the output voltage should be probed in a Simscape/Simulink model.
6. Diagnose a lab mistake where the student accidentally used 100 uF instead of 100 nF.

Expected concepts: fc = 1/(2*pi*R*C) is about 40 Hz. Nyquist is 250 Hz. A single-pole RC filter helps, but does not prove alias-free sampling.


Live correction-pass instruction: build a Simscape-first model with SATK/Codex, open it visibly, then stop before screenshots so a human can manually arrange and save the Simulink diagram.