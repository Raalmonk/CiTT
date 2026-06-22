# Benchmark 1 Comparison Notes

Live CiTT evidence for Benchmark 1 has been captured.

## CiTT / Simscape Workflow

CiTT produced an executable Simulink/Simscape model with physical RC components, voltage sensing, ADC sampling, and a `100 uF` mistake comparison branch.

Captured evidence:

- Manual arrangement screenshot shows the physical Simscape RC branches and ADC sampling path.
- Teach screenshots show model-grounded Socratic explanation with rendered formula output.
- Highlight screenshot shows the cutoff-frequency blocks in the opened model.
- Probe screenshot shows natural-language target selection, probe highlighting, and measured RC parameter/frequency-response values printed back into the learning/probe dialog.
- Annotated Bode plot gives numeric RC evidence: `fc` about `39.99 Hz`, `60 Hz` attenuation about `-5.12 dB`, and `250 Hz` Nyquist attenuation about `-16.03 dB`.
- The same plot shows the `100 uF` lab mistake explicitly: `fc` shifts to about `0.03999 Hz` and the `5 Hz` ECG component is attenuated by about `-41.94 dB`.

## Gemini-Only No-Tools Baseline

Baseline prompt saved in `llm_baseline_prompt.md`.

Gemini-only no-tools output saved in `llm_baseline_output_gemini_no_tools.md`.

The Gemini-only baseline performs well on this textbook RC calculation:

- `fc ~= 40 Hz`
- `5 Hz ~= -0.07 dB`
- `60 Hz ~= -5.1 dB`
- `250 Hz ~= -16.0 dB`
- `100 uF` mistake gives `fc ~= 0.04 Hz` and about `-42 dB` at `5 Hz`

These match the live CiTT evidence closely. This benchmark should not be described as Gemini-only failing.

## Observed Difference

Gemini-only can solve the textbook RC calculation, but CiTT adds executable model grounding: a generated Simscape/Simulink model, visible output-probe placement, focus-map teaching, natural-language probe output, Lab Delta/unit-mistake diagnosis, and annotated Bode evidence.

The point of this benchmark is that CiTT is not weaker than a simple hand-calculation baseline, and it provides additional model, probe, plot, and evidence artifacts.

## Limitations

Time-domain waveform probes still require numeric source amplitudes/phases. The RC cutoff/attenuation probe now produces parameter-derived numeric evidence from the Simscape model, but full ADC front-end nonidealities such as input impedance, quantization, and sample-and-hold behavior are outside this simple first-order proof.
