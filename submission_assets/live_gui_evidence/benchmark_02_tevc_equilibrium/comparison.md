# Benchmark 02 Comparison

## CiTT / Simscape Workflow

CiTT parsed the TEVC equilibrium problem, treated omitted biological dynamics as modeling assumptions rather than blockers, and generated a Simscape-first physical electrical model.

Evidence captured:

- `screenshots/01_read_page.png`: parse result.
- `screenshots/03_simscape_model_arranged.png`: arranged Simulink/Simscape model after manual adjustment.
- `screenshots/06_teach_step2_vm.png`: teaching state with highlighted `Vm` probe region.
- `screenshots/10_probe_measure_probe_vm_explicit.png`: natural-language probe result printed in the dialog.

The generated model includes explicit physical components for command source, buffer path, finite-gain amplifier, `Ro`, `Rm`, symbolic `Re`, `VM_PROBE`, amplifier-output probe, clamp-current probe, electrical reference, and solver configuration.

## Text-Only No-Tools Baseline

Baseline prompt saved in `llm_baseline_prompt.md`.

Text-only reasoning can give a reasonable TEVC explanation:

- It recognizes negative feedback driving `Vm` toward `Vc`.
- It explains that the ideal buffer makes the voltage-sensing path high impedance.
- It recognizes that finite gain creates tracking error.
- It does not treat omitted membrane capacitance or ion-channel dynamics as a fatal blocker for the simplified DC problem.

However, it has two issues worth preserving in the comparison:

- It first says a numerical `Vm` cannot be computed because both `Vc` and `Re` are missing, but later correctly says `Re` has zero DC effect under the ideal-buffer assumption. More precisely: absolute numerical `Vm` cannot be computed because `Vc` is missing; `Re` is missing but irrelevant under the ideal-buffer DC assumption.
- Its formula formatting is easy to misread. The clean tracking relation is:

```text
Vm / Vc = (A * Rm) / (Ro + (A + 1) * Rm)
```

With `A = 100`, `Rm = 10 ohm`, and `Ro = 10 ohm`:

```text
Vm / Vc = 1000 / 1020 ~= 0.9804
```

## Observed Difference

Text-only reasoning can explain the TEVC concept and produce a plausible symbolic ratio. CiTT adds an inspectable Simscape-first model, decoded focus map, decoded probe map, model-check evidence, and GUI-backed teaching/highlight/probe evidence.

The core difference is auditability: text derivation can be right but hard to inspect; CiTT connects the explanation to model paths and probe points.

## Limitation

The benchmark leaves `Vc` and `Re` symbolic. CiTT correctly preserves them as symbolic parameters. Numeric simulation/probe values require assigning numeric values first.
