# Benchmark 02 Live GUI Evidence Notes

## Example

Two-Electrode Voltage Clamp Equivalent Circuit.

Workflow prompt:
- `workflow_total_prompt.md`

Input prompt and schematic:
- `problem_statement.md`
- `input_schematic.png`

## Result

Status: pass with symbolic-parameter caveat.

CiTT parsed the benchmark, prepared an external Codex build task, built a Simscape-first physical electrical model with built-in MATLAB/Simulink/Simscape/Simscape Electrical blocks, and loaded the generated model into the teaching/probe UI.

The external build preserved `V_c` and `R_e` as symbolic parameters because the benchmark problem did not provide numeric values. Structural verification passed, but numerical simulation and numeric probe summaries require assigning those two values first.

## Build Artifacts

Archived artifacts:
- `artifacts/citt_generated_model_tevc.slx`
- `artifacts/citt_focus_map.json`
- `artifacts/citt_probe_map.json`
- `artifacts/citt_agent_report.md`
- `artifacts/citt_agent_task.md`
- `artifacts/citt_agent_stdout.log`
- `artifacts/citt_agent_stderr.log`

Agent verification:
- SATK `model_check(root, all)` reported healthy.
- Focus map decoded with 5 focus items.
- Probe map decoded with 5 probe items.

## UI Evidence

Screenshots:
- `screenshots/00_input_ready.png`: prompt and schematic loaded.
- `screenshots/01_read_page.png`: circuit parsed as TEVC equilibrium model.
- `screenshots/02_build_page.png`: build brief ready.
- `screenshots/03_build_running.png`: external Codex build running.
- `screenshots/03_simscape_model_arranged.png`: Simulink/Simscape model after user manual arrangement/drag checkpoint.
- `screenshots/03_build_completed_loaded.png`: generated model loaded in the teaching UI.
- `screenshots/04_teach_student_answer.png`: student answer entered.
- `screenshots/05_teach_reveal_feedback_loop.png`: reveal feedback for Step 1.
- `screenshots/06_teach_step2_vm.png`: Step 2 advanced and highlighted Vm probe region.
- `screenshots/09_probe_measure_clamp_current.png`: natural-language clamp-current probe printed in the dialog.
- `screenshots/10_probe_measure_probe_vm_explicit.png`: natural-language Vm probe printed in the dialog.
- `screenshots/11_after_manual_drag_citt_window.png`: CiTT window state after the user manually dragged the view.
- `screenshots/12_chat_probe_vm_restored.png`: restored Codex-style model plus teaching/probe dialog after removing the tool-panel overcorrection.
- `screenshots/13_latex_probe_restored.png`: restored subscript/LaTeX-style symbol rendering in the teaching concept and probe result.

## Interaction Caveat

Manual model-image dragging/panning was not verified as working. The current HTML UI exposes file drag/drop and wheel routing, but there is no dedicated pointer-drag pan handler for the Simulink snapshot area. The tested interaction path relies on the full-size snapshot plus highlight refreshes when teaching/probe targets change.

After the user manually adjusted the visible model/view, new screenshots were captured for the arranged Simulink model and the CiTT window.

## Probe Behavior

Tested command: `measure probe_vm voltage`.

Observed behavior:
- Preview-only probe flow stayed non-mutating.
- `VM_PROBE` was highlighted.
- Dialog output identified the measured quantity as `Vm (V)`.
- Dialog output explained that the timeseries can be read from `Vm_Log` after numeric `V_c` and `R_e` values are supplied.
- Numeric measurement summary reported unavailable because those symbolic parameters were unresolved.

Tested command: `measure clamp current`.

Observed behavior:
- Probe output printed in the dialog.
- Dialog identified clamp current through `R_o` in amperes.
- Dialog included the current direction instruction from `I_CLAMP_PROBE.p` to `I_CLAMP_PROBE.n`, from amplifier output toward `R_o` and `n_vm`.

## Teaching Behavior

The app automatically reached the teaching view after build completion. The model snapshot stayed as the dominant upper visual region, and the teaching card showed:
- Step number, focus id, and question.
- A student answer field.
- Reveal and next-step controls.
- The natural-language measurement input below the teaching card.

Step 1 reveal used the generated focus-map concept and expected reasoning. Step 2 automatically changed the focus to the Vm probe region.

## Caveat

The benchmark is an equilibrium symbolic problem. For a numeric plot or numeric probe values, define concrete values for `V_c` and `R_e`, then rerun simulation/probe.
