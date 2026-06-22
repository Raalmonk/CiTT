# CiTT PaperOrchestra Experimental Log

## Evidence Source

Primary evidence directory:

```text
vericircuit-tutor/submission_assets/live_gui_evidence/
```

Release verification directory:

```text
vericircuit-tutor/release/
```

## Benchmark 1: Textbook RC Anti-Aliasing

Status: live evidence completed.

Task: ECG-style RC low-pass anti-aliasing filter before ADC sampling.

Evidence produced:

- Parsed problem evidence.
- Opened/generated Simscape model screenshot.
- Teaching page explaining cutoff-frequency reasoning.
- Signal-path highlight screenshot.
- Natural-language probe evidence.
- Live and annotated Bode plots.

Measured/derived values from evidence:

- `R = 39.8 kOhm`
- `C = 100 nF`
- `tau = 0.00398 s`
- `fc = 39.9887 Hz`
- `60 Hz attenuation = -5.1205 dB`
- `250 Hz attenuation = -16.0298 dB`
- Unit-mistake comparison: using `100 uF` instead of `100 nF` drops cutoff to about `0.03999 Hz` and strongly attenuates ECG frequencies.

LLM-only baseline: Gemini-only performed well on simple textbook arithmetic, but did not produce executable Simscape artifacts, focus maps, probe maps, GUI evidence, or exported evidence.

## Benchmark 2: Two-Electrode Voltage Clamp Equilibrium

Status: live evidence completed with symbolic-value caveat.

Task: TEVC equivalent circuit with command source, buffer path, finite-gain amplifier, membrane branch, electrode resistance, probes, reference, and solver configuration.

Evidence produced:

- Read/build/teach/probe screenshots.
- Arranged Simscape-first model screenshot.
- Feedback-loop teaching highlight.
- Probe screenshots for membrane voltage and clamp current.
- Generated `.slx` model.
- Focus map with 5 focus items.
- Probe map with 5 probe items.
- SATK model check reported healthy.

Caveat:

- `V_c` and `R_e` remain symbolic because numeric values were not supplied by the benchmark prompt.
- Numeric simulation/probe values require assigning those values first.

LLM-only baseline: Gemini-only gave plausible conceptual reasoning but mixed symbolic limitations and lacked executable model artifacts.

## Benchmark 3: Mixed-Signal Neural Clamp

Status: live evidence completed with educational scaled parameters.

Task: closed-loop mixed-signal neural clamp with command path, ADC/digital logic, feedback path, amplifier/current limit behavior, transient response, parameter sweep, and fault sensitivity.

Evidence produced:

- Generated/opened model screenshots.
- User-arranged model screenshot.
- Parameterized model after simulation.
- Command/ADC/feedback highlight screenshots.
- Teaching/probe UI evidence.
- Exported evidence pack.
- Simulation metrics JSON.
- Timeline, membrane voltage/current, amplifier saturation, ADC/digital logic, parameter sweep, and fault-injection plots.

Simulation metrics from live report:

- Settling time: not settled in the 60 ms window.
- Overshoot: `413.9 %`.
- Final tracking error: `186.2 mV`.
- Saturation duration: `60 ms`.
- Max clamp current: `5.099 nA`.
- Max amplifier output: `1 V`.
- Model warning: discontinuities in algebraic loops may prevent solver convergence.

Interpretation:

- The benchmark demonstrates limitation discovery under educational scaled parameters.
- Saturation/current-limit/non-settling behavior is a useful teaching signal, not a patient or biological validation claim.

LLM-only baseline: Gemini-only correctly admitted that exact transients, ADC code sequences, saturation intervals, settling time, and overshoot require executable simulation, but introduced unsupported assumptions and unit/model-assumption mistakes.

## Release Verification

Package artifacts:

- `release/CiTT_BMES_2026.mltbx`
- `release/CiTT_BMES_2026_Source.zip`
- `release/CiTT_Release_Notes.md`
- `release/CiTT_Reproducibility_Checklist.md`
- `release/install_and_smoke_test.md`
- `release/example_repro/verification_summary.md`
- `release/example_repro/installed_gui_smoke.png`

Installed toolbox verification:

- `.mltbx` installed.
- `which citt` resolved to the MATLAB Add-Ons path.
- `citt.checkSetup` ran.
- GUI launched and closed.
- Installed examples verification reproduced all three example workflows.

## Claims To Use Conservatively

- CiTT produced inspectable MATLAB/Simulink/Simscape artifacts in the live evidence pass.
- CiTT demonstrated focus/highlight teaching and natural-language probe evidence.
- CiTT complements LLM reasoning with model-grounded evidence rather than portraying LLMs as useless.
- CiTT is educational design-assistance software for coursework and design-competition review.

## Claims To Avoid

- Do not claim patient, diagnostic, therapeutic, or clinical use.
- Do not claim Benchmark 3 is a real biological or patient model.
- Do not claim full Lab Delta CSV comparison is complete.
- Do not claim LLM-only baselines are exhaustive.
- Do not claim the paper is ready for real CVPR submission.
