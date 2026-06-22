# BMES/Medtronic Application Answers Draft

This is a scaffold for future submission prose. Keep final answers concise, evidence-grounded, and within the listed word limits.

## Executive Summary (500 Words Max)

- Summarize CiTT as a MATLAB-native circuit tutor that turns biomedical circuit prompts into inspectable Simulink/Simscape models, model-linked teaching, natural-language probes, and reproducible evidence.
- Mention the three benchmark demonstrations without claiming clinical validation.
- Emphasize the difference between text-only reasoning and executable model grounding.

## Problem (125 Words Max)

- Students increasingly use AI for biomedical circuits, but fluent text can hide wrong units, signs, assumptions, and missing simulations.
- Biomedical circuit education needs a way to make AI help inspectable, teachable, and tied to executable models.

## Objective (125 Words Max)

- State the objective as a MATLAB-centered tutor that parses circuit inputs, generates Simscape-first model tasks, teaches from model focus maps, and supports probe/evidence workflows.
- Keep the objective educational and review-oriented, not clinical.

## Final Design Documentation (250 Words Max)

- Describe the MATLAB plugin entry point: `addpath("vericircuit-tutor/matlab"); citt`.
- Note the main components: parser, SATK/MCP agent task generation, Simulink/Simscape artifact checks, focus maps, probe maps, teaching/probe dialog, and evidence export.
- Reference `submission_assets/live_gui_evidence/` as the final evidence package.

## Functional Proof (250 Words Max)

- Benchmark 1: RC anti-aliasing model, cutoff/Bode/probe/unit-mistake evidence.
- Benchmark 2: TEVC equilibrium structure, feedback teaching, symbolic limitation handling, focus/probe evidence.
- Benchmark 3: educational scaled mixed-signal clamp model, simulation plots, saturation/non-settling evidence, ADC/digital behavior, and limitation reporting.
- State that Lab Delta CSV comparison is not claimed as complete without external CSV data.

## Prior Art / Patentability (250 Words Max)

- Compare against general LLM tutoring, static circuit calculators, and standalone Simulink modeling.
- Highlight the integrated workflow: model generation, focus-map teaching, natural-language probes, and evidence export inside MATLAB.
- Avoid overclaiming patentability; flag this as a section needing legal review.

## Regulatory Pathway (125 Words Max)

- Position the current prototype as educational software and model-based learning support.
- State that Benchmark 3 is not clinical validation and the prototype is not patient-specific decision support.
- Note that any medical-device pathway would require a separate quality, validation, cybersecurity, and risk-management program.

## Estimated Manufacturing Costs (250 Words Max)

- Software prototype costs are primarily MATLAB/Simulink/Simscape access, cloud/API usage, development time, and support.
- No hardware manufacturing is required for the current educational prototype.
- Include a future-cost note for deployment, maintenance, validation, and institutional licensing.

## Market And Impact (250 Words Max)

- Target biomedical engineering education, circuit labs, and model-based design instruction.
- Impact: helps students see when AI reasoning needs executable verification and helps instructors review assumptions, units, and model evidence.
- Cite the live GUI evidence as the current proof of feasibility.

## References / Acknowledgements

- MATLAB, Simulink, Simscape, Simscape Electrical.
- Simulink Agentic Toolkit / MATLAB MCP Server.
- Gemini API for configured parsing.
- BMES/Medtronic submission reviewers and course/lab context.
