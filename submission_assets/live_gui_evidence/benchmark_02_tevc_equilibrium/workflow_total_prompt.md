You are working on Raalmonk/CiTT.

Important correction: this workflow uses Computer Use to directly control the user’s desktop, MATLAB, Simulink, and the CiTT plugin. Do NOT treat this as a headless CLI artifact-generation task. Do NOT wait for a background agent to magically write .slx files. Your job is to operate the actual MATLAB GUI like a human assistant.

The goal is to create BMES submission evidence by visually running CiTT and capturing screenshots.

================================================================================
CORE PRINCIPLE
================================================================================

Use Computer Use / GUI control.

You must:
- open MATLAB,
- run the CiTT MATLAB plugin,
- click through the CiTT UI,
- open generated Simulink/Simscape models,
- let the user manually arrange the diagrams,
- capture screenshots after arrangement,
- save screenshots and notes into submission_assets.

Do not rely only on command-line scripts.
Do not rely only on artifact freshness checks.
Do not generate offline-only evidence.
Do not call the package complete unless the screenshots came from the actual GUI/model workflow.

================================================================================
WHY THIS MATTERS
================================================================================

The BMES/Medtronic submission asks for prototype graphical representations and proof that the design is functional. The evidence package should therefore contain real screenshots of:
- CiTT MATLAB plugin,
- circuit parsing,
- Simulink/Simscape model,
- highlight/zoom,
- probe/Lab Delta,
- evidence/export page.

================================================================================
OUTPUT FOLDER
================================================================================

Use:

submission_assets/live_gui_evidence/

Create:

README.md
run_log.md
screenshots/
    01_read_page.png
    02_build_page.png
    03_simscape_model_arranged.png
    04_teach_page.png
    05_highlight_feedback_or_signal_path.png
    06_probe_page.png
    07_evidence_page.png
benchmark_01_textbook_rc/
benchmark_02_tevc_equilibrium/
benchmark_03_mixed_signal/

For each benchmark folder, save:
- problem_statement.md
- llm_baseline_prompt.md
- run_notes.md
- screenshots/
- plots/ if generated
- comparison.md

================================================================================
DO NOT DO
================================================================================

Do not run the offline generator as the final evidence.
Do not mark screenshots as real if they are synthetic.
Do not fabricate LLM baseline outputs.
Do not continue past a manual arrangement checkpoint without the user.
Do not fixate on stale artifact timestamps if the visible GUI workflow is working.
Do not create final bmes_evidence_report until live screenshots are captured.

================================================================================
FIRST TASK: OPEN THE ACTUAL APP
================================================================================

1. Open MATLAB using Computer Use.
2. In MATLAB Command Window, run:

   addpath("matlab")
   citt

3. Confirm the CiTT plugin window opens.
4. Take a screenshot of the initial app and save it to:

   submission_assets/live_gui_evidence/screenshots/00_app_open.png

If MATLAB or CiTT fails to open, debug that first. Fix practical code bugs if needed.

================================================================================
BENCHMARK 1: TEXTBOOK RC ANTI-ALIASING
================================================================================

Problem:
An ECG acquisition front end uses a first-order RC low-pass filter before a 500 Hz ADC. R = 39.8 kOhm, C = 100 nF. Input contains a 5 Hz ECG-like component and 60 Hz interference. Compute cutoff, attenuation at 60 Hz and Nyquist, identify probe location, and diagnose a 100 nF vs 100 uF mistake.

Workflow using GUI:
1. In CiTT Read page, enter or load the RC problem.
2. Click Read with Gemini if appropriate, or load a prepared sample image/spec if available.
3. Capture Read page screenshot after parsing.
4. Go to Build.
5. Prepare/build/open model through the UI.
6. When the Simulink/Simscape model opens, STOP for manual arrangement.

Print this and wait:
“Please manually arrange the RC Simscape/Simulink model now. Make the input, R, C, ground/reference, solver configuration, output probe, and ADC/sampling path visible. Save the model, then tell me: continue benchmark 1.”

Do not continue until user says continue benchmark 1.

After user continues:
1. Capture arranged model screenshot.
2. Use CiTT Teach to show formula/explanation with LaTeX if available.
3. Capture Teach screenshot.
4. Use Highlight/Zoom if available.
5. Capture highlight screenshot.
6. Use Probe/Lab Delta.
7. Capture Probe screenshot.
8. Save all screenshots to benchmark_01_textbook_rc/screenshots.

================================================================================
BENCHMARK 2: TEVC EQUILIBRIUM
================================================================================

Problem:
Simplified two-electrode voltage clamp circuit with command voltage Vc, ideal buffer, finite-gain differential amplifier A = 100, Rm = 10 ohm, Ro = 10 ohm, Re, requested Vm. Equilibrium DC. Omitted ion channels and membrane capacitance are assumptions, not blockers.

Workflow:
1. Use CiTT Read page to parse/load TEVC problem.
2. Confirm UI shows biological simplification as assumptions, not build blockers.
3. Capture Read screenshot.
4. Build/open Simscape/Simulink model.
5. STOP for manual arrangement.

Print and wait:
“Please manually arrange the TEVC model now. Make Vc, buffer path, amplifier, Vm node, output electrode resistance, membrane resistance, feedback loop, and current/voltage probes visible. Save the model, then tell me: continue benchmark 2.”

After user continues:
1. Capture arranged model screenshot.
2. Highlight feedback loop or signal path.
3. Capture highlight screenshot.
4. Show Socratic Teach page asking about feedback path.
5. Capture Teach screenshot.
6. Show Probe page for Vm/amplifier output/clamp current.
7. Capture Probe screenshot.

================================================================================
BENCHMARK 3: COMPLEX MIXED-SIGNAL SIMSCAPE/SIMULINK
================================================================================

Problem:
Closed-loop neural clamp with membrane capacitance, leakage resistance, electrode resistance, finite-gain amplifier, rail saturation/current limit, ADC sampling/quantization, comparator/digital state logic, command step, outputs Vm(t), clamp current, amplifier output, ADC code, digital state, saturation flags.

Goal:
This is the “LLM cannot reliably solve this without simulation” demo.

Workflow:
1. Use CiTT or a prepared benchmark spec to build/open the mixed-signal Simscape/Simulink model.
2. Make sure it includes physical analog subsystem and digital/ADC logic subsystem.
3. STOP for manual arrangement.

Print and wait:
“Please manually arrange the mixed-signal model now. Make the physical membrane subsystem, amplifier/saturation subsystem, sensors/probes, ADC sampling/quantization, digital comparator/state logic, feedback/control path, and output scopes visible. Save the model, then tell me: continue benchmark 3.”

After user continues:
1. Capture arranged model screenshot.
2. Highlight command path / feedback loop / ADC sampling path.
3. Capture highlight screenshot.
4. Run simulation if possible.
5. Capture plots:
   - Vm and clamp current,
   - amplifier saturation,
   - ADC codes and digital state,
   - parameter sweep or fault summary if already available.
6. Capture Evidence page screenshot.

================================================================================
SCREENSHOT RULES
================================================================================

Screenshots must be real GUI/model screenshots.

Use any available method:
- MATLAB exportapp,
- screen capture through Computer Use,
- Simulink screenshot/export,
- macOS screenshot if necessary.

Name files clearly.

If a screenshot fails, fix practical bugs or use a visible desktop screenshot. Do not silently skip.

================================================================================
BUG FIXING RULES
================================================================================

If there are bugs in CiTT UI or MATLAB code, fix them and continue:
- missing HTML resources,
- buttons not wired,
- LaTeX preview not rendering,
- image input not accepted,
- malformed spec display,
- highlight/zoom crash,
- screenshot save issue,
- layout issue preventing visible evidence.

Log every fix in:

submission_assets/live_gui_evidence/run_log.md

Do not spend time rewriting architecture.

================================================================================
LLM BASELINE
================================================================================

For each benchmark, write a baseline prompt file.

If an LLM baseline can be run easily, run it and save raw output.
If not, mark as pending.

Do not fabricate baseline output.

================================================================================
FINAL REPORT
================================================================================

Only after screenshots for at least benchmarks 1 and 2 are captured, create:

submission_assets/live_gui_evidence/bmes_live_evidence_report.md

Include:
- what was run,
- screenshots,
- what CiTT did that LLM-only cannot,
- limitations,
- what depends on MATLAB/Simscape/SATK/Gemini,
- how evidence maps to BMES criteria:
  product need,
  novelty,
  technical feasibility,
  economic plan,
  clarity.

If benchmark 3 is incomplete, label it as optional complex demo, not completed evidence.

================================================================================
STOPPING RULE
================================================================================

For this run, do only:
1. open MATLAB,
2. open CiTT,
3. run or prepare Benchmark 1 until model is open,
4. STOP for manual arrangement.

Do not continue to Benchmark 2.
Do not create final report.
Do not generate fake offline package.

Final response should say:
- CiTT opened or failed,
- Benchmark 1 model opened or failed,
- screenshot path if captured,
- manual arrangement instructions,
- exact phrase user should send next:
  continue benchmark 1