# Benchmark 1 Comparison Notes

Live CiTT evidence for Benchmark 1 has been captured.

CiTT has already produced an executable Simulink/Simscape model with physical RC components, voltage sensing, ADC sampling, and a 100 uF mistake comparison branch.

LLM-only baseline output is pending. Do not fabricate it.

Captured evidence:
- Manual arrangement screenshot shows the physical Simscape RC branches and ADC sampling path.
- Teach screenshots show model-grounded Socratic explanation with rendered formula output.
- Highlight screenshot shows the cutoff-frequency blocks in the opened model.
- Probe screenshot shows natural-language target selection, probe highlighting, and measured RC parameter/frequency-response values printed back into the learning/probe dialog.
- Annotated Bode plot gives numeric RC evidence: fc about 39.99 Hz, 60 Hz attenuation about -5.12 dB, and 250 Hz Nyquist attenuation about -16.03 dB.
- The same plot shows the 100 uF lab mistake explicitly: fc shifts to about 0.03999 Hz and the 5 Hz ECG component is attenuated by about -41.94 dB.

Limitations:
- LLM-only baseline output is still pending.
- Time-domain waveform probes still require numeric source amplitudes/phases, but the RC cutoff/attenuation probe now produces parameter-derived numeric evidence from the Simscape model.
