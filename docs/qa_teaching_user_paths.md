# CiTT Teaching UI QA User Paths

Use these paths as real student simulations, not helper-only tests. Check a 14-inch-class viewport before accepting UI or model-preview changes.

## 1. RC Electrical Sensing

Student prompt:

Build a 1 kOhm and 1 uF RC low-pass lesson. Show Vout across the capacitor and ask why the capacitor voltage changes slowly.

Expected user path:

- Submit from the composer with one visible action.
- Confirm model evidence appears above the question.
- Confirm facts include R, C, units, output node, and measured/simulated Vout evidence.
- Open `+` only for secondary actions such as model tests or evidence export.

## 2. PK Input Boundary

Student prompt:

Build a teaching model where a drug bolus input drives a first-order plasma concentration block, then ask what the time constant means.

Expected user path:

- Submit natural text; do not require the student to choose a model type button.
- Confirm any PK simplification is named as an explicit signal-level boundary.
- Confirm the teaching card shows dose, rate/clearance assumption, concentration unit, and current focus.

## 3. Mass Transfer

Student prompt:

Build a two-compartment membrane mass-transfer lesson with source concentration, membrane resistance, and measured receiving-side concentration.

Expected user path:

- Confirm the model preview focuses on the local transfer path rather than a tiny full diagram.
- Confirm facts expose concentration units and transfer assumptions.
- Ask: measure receiving concentration. Confirm the result appears in the learning surface, not a separate hidden artifact.

## 4. Mixed-Signal ADC

Student prompt:

Build an ECG anti-aliasing and ADC conversion lesson with RC filter output, sampler, quantizer, and digital code output.

Expected user path:

- Confirm the first teaching question is about one local focus, not the whole system.
- Confirm the visible controls in the teaching step are no more than `+`, Hint, and Next step.
- Use `/scenarios` or `+` > Simulation scenarios only after the model exists.

## 5. Bad LaTeX

Student input during teaching:

I think $V_out = \frac{1}{RC because the capacitor stores charge and \badcommand{z}

Expected user path:

- The answer preview and teaching response degrade to readable plain text.
- No broken markup, overlapped text, or blocked next action appears.

## 6. Missing Model Scenario Guard

User command:

/scenarios

Expected user path when no model exists:

- Scenario report is not successful.
- Summary has `NOT_RUN > 0`.
- UI says scenarios are incomplete and points to NOT_RUN or FAIL rows.

## 2026-06-30 MATLAB R2026b 14-Inch UI Run

Viewport: `1440 x 900`, launched with `/Applications/MATLAB_R2026b.app/bin/matlab`.

Screenshots:

- `matlab/work/ui_qa_student_paths/00_restored_pk_teach_1440x900.png`
- `matlab/work/ui_qa_student_paths/01_pk_teach_step1_1440x900.png`
- `matlab/work/ui_qa_student_paths/02_bad_latex_answer_1440x900.png`
- `matlab/work/ui_qa_student_paths/03_reveal_feedback_1440x900.png`
- `matlab/work/ui_qa_student_paths/04_pk_teach_step2_1440x900.png`
- `matlab/work/ui_qa_student_paths/05_probe_measure_1440x900.png`

Student-simulated path:

- Restore the saved PK biosensor task.
- Select the same task from task history through `TestHooks.selectTask`.
- Enter malformed LaTeX in the teaching answer.
- Reveal the answer to force the teaching surface into the concrete focus step.
- Advance to the mass-transfer step.
- Try a natural-language measurement: `measure concentration signal`.

Observed result:

- Bad LaTeX degraded to plain text and did not break the teaching UI.
- Concrete teaching facts appeared after reveal: components, nodes, known values, model values, and measured outputs.
- The teaching surface kept the primary visible controls small: `+`, `Hint`, and `Next step`.
- Task restore and task selection did not immediately restore the concrete teaching plan; the first visible state showed a generic teaching question until Reveal/Start Teaching rebuilt or reloaded the plan.
- The model evidence failed the screenshot test in the restored state: the preview was mostly blank canvas with only a clipped block corner visible.
- Step 1 model evidence was readable enough to identify the PK source path, but the right-side block was clipped.
- Step 2 model evidence was too tightly cropped and did not show enough local context or readable labels for the mass-transfer question.
- The measurement attempt jumped out of the learning surface into the build/thread view with `Command failed. Try a more direct phrase.`, leaving the student in a confusing state.
- Interrupting the long measurement run crashed MATLAB R2026b prerelease and wrote `/Users/Raalm/matlab_crash_dump.12513-1`; treat measurement-path hangs as a QA failure, not a pass.

Current acceptance status:

- Bad LaTeX: pass.
- Primary teaching controls: pass.
- 14-inch layout fit: pass for restored PK Step 1 and mass-transfer Step 2 after the 2026-06-30 fix.
- Model evidence readability: pass for PK Step 1 and mass-transfer Step 2 after increasing crop context and ignoring sparse-line crop anchors. Left/right edge labels can still be trimmed slightly, but the current focus and facts are readable.
- Saved-task teaching restore: pass after preventing active-task reselection from overwriting saved artifacts and restoring matching plans for saved teach/probe/evidence tasks.
- Natural-language measurement from the learning surface: pass after switching the teaching-path measure command to preview-only probe matching. The result remains inside the learning surface and says that no simulation or model changes were made.

Fix verification screenshots:

- `matlab/work/ui_qa_student_paths/10_fix_restore_1440x900.png`
- `matlab/work/ui_qa_student_paths/11_fix_select_same_1440x900.png`
- `matlab/work/ui_qa_student_paths/15_fix_step2_row_threshold_1440x900.png`
- `matlab/work/ui_qa_student_paths/16_fix_measure_learning_surface_1440x900.png`

## 2026-06-30 20-Example Universal Probe Run

Command:

`/Applications/MATLAB_R2026b.app/bin/matlab -batch "cd('/Users/Raalm/Documents/GitHub/CiTT'); addpath('matlab/tests'); results = run_simulink_local();"`

Result:

- `test_probe_preview_examples_20`: pass.
- `run_simulink_local`: `4 passed, 0 skipped, 0 failed`.
- The first run failed on `测量 输入 电压`, which incorrectly matched the TIA output probe. The fix was universal: keep `输入` as `input` only, and only map `放大` or `跨阻` to `amplifier`.
- The same fix also made `输出` domain-neutral instead of coupling it to ECG/recovered-output semantics.

Student examples:

| # | Student phrase | Expected probe |
|---|---|---|
| 1 | `measure concentration signal` | `PR_CONCENTRATION` |
| 2 | `probe analyte concentration C(t)` | `PR_CONCENTRATION` |
| 3 | `测量 浓度` | `PR_CONCENTRATION` |
| 4 | `scope lagged concentration after membrane` | `PR_LAGGED_CONCENTRATION` |
| 5 | `measure membrane lag concentration` | `PR_LAGGED_CONCENTRATION` |
| 6 | `测量 膜 后 滞后 浓度` | `PR_LAGGED_CONCENTRATION` |
| 7 | `measure sensor current` | `PR_SENSOR_CURRENT` |
| 8 | `probe faradaic current output` | `PR_SENSOR_CURRENT` |
| 9 | `测量 传感器 电流` | `PR_SENSOR_CURRENT` |
| 10 | `measure TIA output voltage` | `PR_TIA_OUTPUT` |
| 11 | `probe transimpedance amplifier output` | `PR_TIA_OUTPUT` |
| 12 | `测量 跨阻 放大 输出 电压` | `PR_TIA_OUTPUT` |
| 13 | `measure ADC code` | `PR_ADC_CODE` |
| 14 | `probe digital converter code` | `PR_ADC_CODE` |
| 15 | `测量 ADC 数字 代码` | `PR_ADC_CODE` |
| 16 | `measure settling error` | `PR_SETTLING_ERROR` |
| 17 | `probe final settling error voltage` | `PR_SETTLING_ERROR` |
| 18 | `测量 稳定 误差` | `PR_SETTLING_ERROR` |
| 19 | `measure source voltage` | `PR_SOURCE_VOLTAGE` |
| 20 | `测量 输入 电压` | `PR_SOURCE_VOLTAGE` |

Final verification:

- `run_all`: `18 passed, 0 skipped, 0 failed`.
- `run_release_smoke`: `1 passed, 0 skipped, 0 failed`.

CV/pixel screenshot audit:

- Audited screenshots: `10_fix_restore_1440x900.png`, `11_fix_select_same_1440x900.png`, `15_fix_step2_row_threshold_1440x900.png`, `16_fix_measure_learning_surface_1440x900.png`.
- Checks: exact `1440 x 900` size, nonblank model evidence region, model-region edge density, edge bounding-box coverage, nonblank learning-card region, learning-card edge density, and visible green primary control region.
- Result: all 4 screenshots passed. The 20 example command test is separate from this CV audit; it verifies natural-language probe routing and preview-only measurement behavior.

## 2026-06-30 20-Example UI Computer-Use Flow

Command:

`/Applications/MATLAB_R2026b.app/bin/matlab -batch "cd('/Users/Raalm/Documents/GitHub/CiTT'); addpath('matlab/tests'); report = run_ui_examples_20_computer_use(); disp(report.summary);"`

Flow per example:

- Open the real CiTT MATLAB HTML app at `1440 x 900`.
- Restore the saved mixed-signal PK/electrochemical biosensor teaching task.
- Navigate to the relevant teaching step.
- Simulate a student answer and reveal the answer.
- Submit the student's measurement phrase through the composer.
- Confirm the matched probe ID, preview-only measurement, model evidence screenshot, teaching card, and visible controls.
- Save two screenshots per example: `*_reveal.png` and `*_measure.png`.

First failure run:

- `观察 PK concentration C(t)` and `scope lagged concentration after membrane` stayed in teaching-answer routing instead of measurement routing.
- `probe transimpedance amplifier output` matched `PR_C_PK` instead of `PR_V_TIA_OUT`.
- `probe digital converter code` matched `PR_I_SENSOR` because `converter` was over-weighted by PS-Simulink converter evidence.
- Reveal screenshots passed model/learning-content checks but failed a too-narrow primary-button crop.

Universal fixes:

- Composer measurement routing now accepts `scope` and `观察`.
- Natural-language probe matching now maps `TIA/transimpedance/跨阻` to TIA voltage evidence.
- Natural-language probe matching now maps `digital/converter/quantizer/数字/代码/模数` toward ADC code and quantizer evidence.
- CV control detection now covers the bottom control band used by both reveal and measurement states.

Final result:

- Report: `matlab/work/ui_qa_student_paths/computer_use_20_20260630_212035/report.md`.
- Screenshots: `matlab/work/ui_qa_student_paths/computer_use_20_20260630_212035/`.
- `20 passed, 0 failed, 40 screenshots`.
- Every row has `CV true/true` and `Preview true`.
- `run_all`: `18 passed, 0 skipped, 0 failed`.
- `run_release_smoke`: `1 passed, 0 skipped, 0 failed`.

## 2026-06-30 Model Zoom QA

Change:

- The Simulink preview and learning model evidence both support zoom in, zoom out, fit view, mouse-wheel zoom, double-click zoom, and drag-to-pan when zoomed.
- In the learning surface, the zoom controls live on the teaching card step row so they remain visible after reveal, measurement, and model snapshot refreshes.
- The default view still fits the model evidence above the teaching question.

Verification:

- Smoke screenshot with zoomed measurement state: `matlab/work/ui_qa_student_paths/zoom_measure_stepbar_smoke.png`.
- Final full-flow report: `matlab/work/ui_qa_student_paths/computer_use_20_20260701_022050/report.md`.
- Screenshots: `matlab/work/ui_qa_student_paths/computer_use_20_20260701_022050/`.
- The 20-example UI runner zoomed the learning model to `1.35x` before each reveal and measure screenshot.
- Result: `20 passed, 0 failed, 40 screenshots`, with `CV true/true` and `Preview true` on every row.
- `run_all`: `18 passed, 0 skipped, 0 failed`.
- `run_release_smoke`: `1 passed, 0 skipped, 0 failed`.
