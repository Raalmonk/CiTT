# Benchmark 1: Textbook RC Anti-Aliasing

An ECG acquisition front end uses a first-order RC low-pass filter before a 500 Hz ADC.

R = 39.8 kOhm and C = 100 nF. The input contains a 5 Hz ECG-like component and 60 Hz interference.

Tasks:
- Compute the cutoff frequency.
- Compute attenuation at 60 Hz.
- Compute attenuation at the Nyquist frequency.
- Identify where the output voltage should be probed in a Simscape/Simulink model.
- Diagnose a lab mistake where the student accidentally used 100 uF instead of 100 nF.
