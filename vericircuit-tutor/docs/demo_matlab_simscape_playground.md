# Demo: MATLAB/Simscape Playground

1. Start the current web app and backend.
2. Open the `MATLAB` panel in the right workspace.
3. Select `RC anti-aliasing filter before ADC`.
4. Show `Overview`: BME context, assumptions, default `fs = 500 Hz`, target `fc = 40 Hz`, R/C values, and the MATLAB/Simscape role.
5. Show `Teach`: four modes and focus-map entries such as `input_path`, `rc_filter`, `sampling_stage`, and `output_signal`.
6. Click `Generate MATLAB/Simscape Artifact` and preview `citt_rc_antialias_adc.m` plus the Simscape-first build script.
7. Show `Probe plan`: input signal, filter output voltage, sampled output, and cutoff/attenuation check.
8. Show `Lab Delta`: the seed example compares 40 Hz hand cutoff with about 251.3 Hz measured, triggering rad/s vs Hz and missing `2*pi`.
9. Switch to `instrumentation_amplifier_feedback` and show the `feedback_loop`, `gain_setting_resistor`, and `op_amp_output` focus entries.
10. Open MATLAB, add `vericircuit-tutor/matlab` to the path, and run `citt.openTutor("rc_antialias_adc")` to show the four-tab popup skeleton using the same API contract.

Presenter line:

> CiTT keeps its web/API teaching stack and internal solver hand checks, but the engineering playground direction is now MATLAB, Simulink, and Simscape behind a graphical tutor UI.
