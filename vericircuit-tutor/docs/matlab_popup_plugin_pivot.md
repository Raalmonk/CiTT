# CiTT MATLAB Popup Plugin Pivot

CiTT is evolving into a MATLAB-native popup tutor for BME circuits and signal-conditioning labs. It keeps the guided graphical teaching experience while using MATLAB/Simulink artifacts as the learning playground. The LLM is not the numerical authority; tutoring is grounded in explicit models, hand checks, generated artifacts, simulation evidence, and student-visible reasoning steps.

This is an additive product pivot. The current API, web MVP, Circuit IR, validation layer, internal solver, verifier, guided steps, lesson packet, reasoning coach, BME context, scope boundary, probe/KCL ideas, variants, and answer provenance remain valuable product assets. The internal solver becomes the hand-check, fallback, and simple verifier behind a broader MATLAB/Simulink learning workflow.

## Why Pivot

Biomedical circuits courses often teach signal-conditioning concepts inside MATLAB, Simulink, or Simscape labs. Students need to connect circuit calculations, simulation behavior, and lab measurements, but many resist workflows that require them to hand-write setup code before they understand the model.

The target experience is graphical and low-friction:

```text
In MATLAB:
    citt

A CiTT popup opens with four tabs:
    Overview
    Teach
    Probe
    Lab Delta
```

Students click through labs, inspect highlighted model regions, add probes, run simulations, and compare simulation with measured data. They should not have to write MATLAB setup code to get started.

## What Stays

- The FastAPI layer remains the shared contract for the web preview, future MATLAB App Designer popup, future local toolbox, and future agent/MCP bridge.
- The web MVP remains useful for previewing lesson packets, focus targets, reasoning-coach flows, and generated artifacts.
- Circuit IR, validation, internal solver/checker, verification badges, calculation trace, and answer provenance remain available.
- Guided explanation, step-synchronized diagram focus, hint ladders, reasoning coach before reveal, BME context, scope boundaries, probe/KCL panels, current-path labels, what-if variants, and lab-deviation thinking remain central.
- Unsupported or ambiguous requests should still be reported honestly.

## What Changes

The main playground shifts from a web-only internal solver surface to generated MATLAB/Simulink-compatible artifacts:

```text
Prompt / lab selection / Circuit IR
    -> Learning Lab IR or Plugin Manifest
    -> MATLAB artifact generator
    -> MATLAB script / Simulink build plan / focus map / probe plan / lab delta plan
    -> API response
    -> future MATLAB popup plugin consumes the API
```

The internal solver is reframed as a hand-check/fallback/simple verifier. It is not deleted and it is not the entire future product story.

## Why The API Remains Essential But Optional

The MATLAB popup should not require a local server. The default MATLAB path is offline-first: a `.mltbx` toolbox can bundle JSON plans and generated artifacts so `citt` opens a popup from local files. Keeping the API layer still lets CiTT serve:

- The existing React/Vite web preview.
- A future MATLAB App Designer popup when it wants optional artifact refresh.
- A future `.mltbx` toolbox that bundles generated artifacts and may optionally fetch updates.
- A future local adapter for MATLAB execution.
- A future MCP/agent bridge hidden behind GUI buttons, not exposed as a student coding requirement.
- CI tests that inspect manifests, plans, and generated text without MATLAB installed.

## Why The GUI Remains Essential

CiTT is not trying to turn students into prompt engineers or MATLAB-code authors. The tutor should present a simple input/output interface with explicit tabs, buttons, probes, highlights, and comparison tables. Generated scripts and build plans are implementation artifacts that can be inspected by instructors and advanced users, but the student path should be guided and visual.

## Four Tabs

### Overview

The Overview tab gives the student a cognitive map before entering the model:

- Lab title and learning objective.
- Inputs and outputs.
- Key parameters.
- Assumptions and idealizations.
- BME safety boundary.
- MATLAB/Simulink/Simscape artifact to be generated.
- Evidence the tutor will collect.

### Teach

The Teach tab keeps the existing guided lesson idea:

- Lesson steps.
- Student prompt before reveal.
- Focus targets.
- Model highlight plans.
- Verified or simulated values where appropriate.
- Conceptual explanation.
- Common mistakes.

Current web focus targets point at SVG diagram elements. In the MATLAB plugin they become Simulink highlight targets such as blocks, lines, ports, annotations, or conceptual paths. The bridge is a typed focus map.

### Probe

The Probe tab helps students inspect a local model region:

- Suggested voltage, current, or signal probes.
- Suggested signal logging.
- Suggested sensor insertion.
- Expected quantity and unit.
- Student question.
- Measurement explanation.
- Future MATLAB plugin steps.

The MVP generates deterministic probe plans and MATLAB script comments. It does not mutate Simulink models in CI.

### Lab Delta

The Lab Delta tab compares hand calculation, simulation, and lab data:

- Hand value.
- Simulation value.
- Measured value.
- Absolute difference.
- Percent difference.
- Likely causes.
- Next check.
- Reflection question.

The response should be educational and calibrated, not overconfident. It should suggest causes such as rad/s vs Hz confusion, missing `2*pi`, nF/uF mistakes, resistor or capacitor tolerance, source/load impedance, transients not settled, sample-rate/Nyquist issues, ADC quantization, solver settings, and measurement noise.

## MATLAB/Simulink Playground Strategy

The near-term generator produces offline artifacts first:

- MATLAB script text.
- Simulink build-script plan text.
- Live Script plan text.
- App Designer layout plan.
- Toolbox manifest plan.
- Focus map JSON.
- Probe plan JSON.
- Lab Delta comparison JSON.
- Four-tab lab plan JSON for the popup.
- MATLAB agent adapter plan JSON with dry-run/refusal rules.
- Offline bundle JSON for future `.mltbx` package builders.

Future adapters may optionally call the API, execute MATLAB, call `hilite_system`, build Simulink models, insert logging, and package `.mltbx` toolboxes. Those adapters should remain optional and should not be required for Python CI or for the basic offline MATLAB popup.

## MVP Vertical Slice

The first vertical slice is `rc_antialias_adc`:

- RC anti-aliasing before an ADC.
- `fs = 500 Hz`.
- Target cutoff near `40 Hz`.
- Input is an ECG-like low-frequency signal plus 60 Hz interference.
- Output is a filtered and sampled waveform.
- Hand check uses `fc = 1/(2*pi*R*C)` and `nyquist = fs/2`.
- Focus map includes input path, RC filter, sampling stage, output signal, and lab-delta measurement point.
- Probe plans include logging input/output, measuring RC output voltage, and comparing the 60 Hz component before and after the filter.

## Future Vertical Slices

- Instrumentation amplifier intro.
- ECG front end.
- EMG band-pass.
- Photodiode transimpedance amplifier.
- Thermistor divider.

These should reuse the same four-tab contract, focus-map schema, probe plan schema, and Lab Delta comparison logic.

## Future Popup App

The future MATLAB-native surface can be delivered as:

- A MATLAB App Designer popup launched with `citt`.
- A `.mltbx` toolbox containing `+citt/`, templates, examples, docs, and app files.
- Optional API-backed artifact refresh.
- Optional MCP/agent bridge behind GUI buttons for instructors or advanced workflows.

The student-facing experience should remain guided, graphical, and low-friction.

## CI Boundary

Python tests should inspect generated strings, manifests, plans, and JSON payloads. MATLAB should not be required in CI. Live MATLAB execution, Simulink model mutation, and toolbox packaging are future adapter responsibilities.
