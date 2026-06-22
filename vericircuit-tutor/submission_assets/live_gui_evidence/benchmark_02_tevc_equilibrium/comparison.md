# Benchmark 02 Comparison

## CiTT / Simscape Workflow

CiTT parsed the TEVC equilibrium problem, treated omitted biological dynamics as modeling assumptions rather than blockers, and generated a Simscape-first physical electrical model.

Evidence captured:
- `screenshots/01_read_page.png`: parse result.
- `screenshots/03_simscape_model_arranged.png`: arranged Simulink/Simscape model after manual adjustment.
- `screenshots/06_teach_step2_vm.png`: teaching state with highlighted Vm probe region.
- `screenshots/10_probe_measure_probe_vm_explicit.png`: natural-language probe result printed in the dialog.

The generated model includes explicit physical components for command source, buffer path, finite-gain amplifier, `Ro`, `Rm`, symbolic `Re`, `VM_PROBE`, amplifier-output probe, clamp-current probe, electrical reference, and solver configuration.

## LLM-Only Baseline

Baseline prompt saved in `llm_baseline_prompt.md`.

Raw LLM baseline output: pending. No baseline answer has been fabricated.

## Observed Difference

The CiTT workflow produced inspectable Simulink/Simscape artifacts and GUI evidence. The current LLM-only baseline prompt can explain the circuit conceptually, but without running a tool it cannot produce a verified Simscape block diagram, clickable focus map, probe map, or GUI-backed measurement/highlight evidence.

## Limitation

The benchmark leaves `Vc` and `Re` symbolic. CiTT correctly preserves them as symbolic parameters. Numeric simulation/probe values require assigning numeric values first.
