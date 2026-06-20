# MATLAB/Simscape Playground

CiTT now presents a concrete MATLAB/Simscape playground direction while keeping the existing web UI, FastAPI layer, reasoning coach, lesson packets, BME context, visual focus, probe/KCL work, variants, Lab Delta logic, and internal solver pipeline.

CiTT is a graphical tutor layer for BME circuits and signal-conditioning labs. Students choose a lab, review the overview, follow guided teaching, probe local signals, and compare hand calculation, generated simulation evidence, and lab data. MATLAB, Simulink, and Simscape are the engineering playground behind GUI buttons; students are not asked to hand-write setup code.

## Four Modes

- `Overview`: lab purpose, inputs/outputs, assumptions, idealizations, BME boundary, MATLAB/Simscape role, and CiTT hand-check role.
- `Teach`: guided lesson steps, coach-before-reveal flow, and focus-map targets that can correspond to SVG, Simulink, or Simscape regions.
- `Probe`: deterministic voltage/current/signal probe plans, expected units, logging variable names, and one student-facing question.
- `Lab Delta`: deterministic comparison of hand values, simulation values, and measured lab values with likely causes and a recommended next probe.

## Implemented Files

- Backend models: `backend/app/models/matlab_playground.py`
- Backend service: `backend/app/services/matlab_playground.py`
- API routes: `/matlab_playground/manifest`, `/labs`, `/labs/{lab_id}`, `/artifacts`, `/focus_map`, `/probe_plans`, and `/lab_delta`
- MATLAB popup skeleton: `matlab/citt.m`
- MATLAB helpers: `matlab/+citt/openTutor.m`, `buildPlayground.m`, `highlightFocus.m`, `runLabDelta.m`, and `loadManifest.m`
- Web panel: React right-side `MATLAB` tab

The previous `/matlab_plugin` endpoints remain available as compatibility routes for earlier generated bundles and tests.

## Included Labs

- `rc_antialias_adc`: complete demo path for an ECG-like signal, 60 Hz interference, RC cutoff hand check, sampling, focus map, probe plans, and Lab Delta seed.
- `instrumentation_amplifier_feedback`: compact ECG instrumentation front-end path with differential input, common-mode input, gain-setting resistor, feedback-loop highlight, op-amp output, and output probe.

## Focus And Highlighting

Focus-map entries name conceptual and model targets such as `rc_filter`, `capacitor_output_node`, `sampling_stage`, and `feedback_loop`. The MATLAB helper `citt.highlightFocus(modelName, focusMap, focusId)` opens a model when possible, clears previous highlights, finds the selected focus entry, and calls `hilite_system` for mapped targets. Missing model paths or unavailable blocks produce warnings instead of hard failures.

## Lab Delta

Lab Delta computes absolute and percent error against the hand check when available. It detects common educational causes including rad/s vs Hz, missing `2*pi`, capacitor/resistor prefix mistakes, R/C tolerance, source/load impedance, Nyquist issues, ADC quantization, op-amp saturation, unsettled transients, and measurement noise. The tone is deliberately educational rather than overconfident.

## Demo Without MATLAB

Run the FastAPI backend and React web app. Open the `MATLAB` panel to fetch the manifest, generate artifacts, inspect focus maps, review probe plans, and show a Lab Delta preview. Python tests validate the generated MATLAB text statically, so MATLAB is not required in CI.

## Demo With MATLAB/Simscape

Add `vericircuit-tutor/matlab` to the MATLAB path and run:

```matlab
citt.openTutor("rc_antialias_adc")
```

or:

```matlab
citt.openTutor("instrumentation_amplifier_feedback")
```

The popup can load API data if the backend is running. If the backend or Simscape is unavailable, it uses built-in manifest data and hand-check fallbacks.
