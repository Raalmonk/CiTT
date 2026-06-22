# Benchmark 1 Run Notes

Status: Benchmark 1 live GUI screenshots refreshed after fixing Teach formula rendering and natural-language Probe measurement output.

Live CiTT/Simulink steps completed:
- CiTT opened in MATLAB.
- Benchmark 1 prompt was entered into the visible CiTT app session.
- Circuit read completed as `first_order_passive_rc_low_pass_ecg_adc_front_end`.
- Build brief was prepared.
- Build Model was started from CiTT and completed through Codex/SATK.
- Generated model was opened through CiTT.

Model path:
`matlab/work/citt_generated_model.slx`

Screenshots captured:
- `../../screenshots/00_app_open.png`
- `../../screenshots/01_read_page.png`
- `../../screenshots/02_build_page.png`
- `screenshots/03_simscape_model_open_pre_arrangement.png`
- `screenshots/03_simscape_model_arranged.png`
- `screenshots/04_teach_page.png`
- `screenshots/04_teach_cutoff_formula.png`
- `screenshots/05_highlight_signal_path.png`
- `screenshots/06_probe_page.png`

Plots:
- `plots/rc_bode_annotated.png`
- `plots/rc_bode_annotated.md`
- `plots/rc_bode_annotated.json`
- `plots/rc_bode_live.png`
- `plots/rc_bode_live.md`
- `plots/rc_bode_live.json`

Measured/derived values from CiTT Bode evidence:
- Nominal cutoff frequency: about 39.99 Hz.
- Magnitude at 5 Hz: about -0.067 dB.
- Magnitude at 60 Hz: about -5.12 dB.
- Magnitude at 250 Hz Nyquist: about -16.03 dB.
- 100 uF mistake cutoff frequency: about 0.03999 Hz.
- 100 uF mistake attenuation at 5 Hz: about -41.94 dB, which would nearly erase the ECG component.

Fix verification:
- Teach reveal now sends formula-bearing text through the HTML rich-text renderer. The cutoff step screenshot shows `fc = 1/(2*pi*R*C)` as a rendered fraction.
- Natural-language Probe now matches `probe_frequency_attenuation_checks`, reads the Simscape RC block parameters, and prints the measured/derived values directly in the learning/probe dialog.
- Verified Probe output in the refreshed screenshot: `R1 = 39.8 kOhm`, `C1 = 100 nF`, `tau = 0.00398 s`, `fc = 39.9887 Hz`, `60 Hz = -5.1205 dB`, `250 Hz = -16.0298 dB`.
