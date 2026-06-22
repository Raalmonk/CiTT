OFFLINE DRAFT — NOT FINAL SUBMISSION EVIDENCE.
This draft was generated without live manual Simscape arrangement and should not be treated as final functional proof.

# CiTT: Model-Grounded AI Tutor for Biomedical Circuit Simulation

CiTT turns a circuit diagram or prompt into a structured circuit spec, prepares a Simulink/Simscape build task, and teaches on top of the model using Socratic reasoning, highlight/zoom, probes, Lab Delta, requirement checks, sweeps, fault injection, and exported evidence.

## Why LLM-only tutoring is insufficient

LLM-only circuit tutoring can hallucinate signs, units, topologies, and transient behavior. It does not produce an executable model, cannot prove probe/highlight evidence, and is especially fragile on simulation-only systems with saturation, sampled ADC behavior, and digital state logic.

## What CiTT does

CiTT connects circuit image or prompt input to a Gemini structured spec, SATK/Simscape model generation, Socratic teaching, highlight/zoom actions, probes, Lab Delta comparison, requirement checks, and evidence export.

## Benchmark overview

Benchmark 1 is a textbook RC anti-aliasing filter before a 500 Hz ADC. It demonstrates correct cutoff and attenuation reasoning, probe placement, and a 100 nF versus 100 uF Lab Delta.

Benchmark 2 is a simplified two-electrode voltage clamp equilibrium feedback circuit. It demonstrates BME relevance, feedback-loop explainability, and honest scope control for omitted biological dynamics.

Benchmark 3 is a closed-loop neural clamp with physical membrane/electrode behavior, nonideal amplifier limits, ADC quantization, and digital state control. It is intentionally beyond reliable closed-form LLM-only solving.

## Scorecard

The current scorecard is honest for this offline package. LLM-only baselines are pending. CiTT scores are partial because live Simscape/SATK model screenshots and simulations still need to be regenerated.

See `benchmark_scorecard.md` and `benchmark_scorecard.csv`.

## What Simscape contributes

Simscape contributes physical component modeling, executable simulation, mixed physical/digital co-simulation, transient behavior, parameter sweeps, fault injection, and model-grounded probe/highlight evidence. This is the core difference between CiTT and a text-only tutor.

## Technical feasibility

This run created the full evidence package structure, structured specs, agent tasks, analytical/offline plots, illustrative mixed-signal plots, scorecards, run notes, and a report. Full technical proof still depends on local MATLAB, Simulink, Simscape, Simscape Electrical, Simulink Agentic Toolkit, MATLAB MCP Server, Gemini, and a configured agent CLI.

## Limitations

CiTT requires MATLAB/Simulink/Simscape/SATK/Gemini for the live workflow. Image parsing can be ambiguous. The package is educational evidence, not clinical verification. Complex Simscape diagrams may require human layout cleanup. Live agent reliability depends on local setup. In this run, screenshots are offline panels and mixed-signal traces are illustrative surrogate data.

## Mapping to BMES judging criteria

Product need and market potential: biomedical circuit learning and debugging need model-grounded tutoring.

Device utility and novelty: CiTT links circuit parsing, executable modeling, Socratic teaching, probes, Lab Delta, and exportable evidence.

Technical feasibility: the package defines reproducible scripts and benchmark artifacts, with clear dependency limits for the live model run.

Budget/economic plan: the report identifies required software/services and dependency constraints.

Writing and presentation clarity: each benchmark includes problem statements, specs, prompts, comparisons, plots, run notes, and a scorecard.

Device performance: benchmark artifacts target correctness, model evidence, teaching usefulness, and limitations.

Limitations: external tools, image ambiguity, educational scope, and manual layout cleanup are explicitly documented.

## Prototype files list

- `figures/overview_architecture.png`
- `figures/llm_vs_citt_workflow.png`
- `figures/comparison_score_bars.png`
- `figures/comparison_score_radar.png`
- `figures/bmes_judging_alignment.png`
- `screenshots/app_read.png`
- `screenshots/app_build.png`
- `screenshots/app_teach.png`
- `screenshots/app_probe.png`
- `screenshots/app_evidence.png`
- benchmark folders with problem statements, specs, agent tasks, plots, comparison notes, focus maps, and probe maps.
