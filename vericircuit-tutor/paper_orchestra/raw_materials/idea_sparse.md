# CiTT PaperOrchestra Idea File

## Working Title

CiTT: A Model-Grounded Agentic Tutor for Biomedical Circuit Learning with Gemini, Simulink Agentic Toolkit, and Simscape

## Short Title

CiTT: Simscape-Grounded Agentic Tutoring for Biomedical Circuits

## Core Idea

Biomedical engineering students need to learn circuits, signal conditioning, electrophysiology, instrumentation, filtering, ADCs, sensors, and feedback systems. Many curricula, including the author's BME coursework, require circuits and instrumentation because medical-device signal chains depend on electrical and computer engineering concepts.

Modern students increasingly use LLMs for tutoring. LLMs are useful language and attention models, but they are not rigorous engineering solvers by themselves. They can produce fluent explanations while hiding unit mistakes, sign errors, unsupported assumptions, missing nonideal behavior, or unexecuted simulation claims.

CiTT addresses this by grounding an AI tutor in executable MATLAB/Simulink/Simscape artifacts. The language model helps parse prompts or circuit images and support Socratic dialogue, but engineering authority is assigned to inspectable models, plots, simulation metrics, model checks, assumptions, limitations, focus maps, probe maps, and exported evidence.

## System Components

- Gemini-assisted prompt/image parsing into a structured circuit specification.
- Agentic Simulink/Simscape model generation through SATK/MCP-style tooling.
- Simscape/Simulink artifact checks and saved `.slx` models.
- Socratic teaching loop grounded in model focus maps.
- Model highlight/zoom and natural-language probe maps.
- Evidence export for course review and BMES/Medtronic-style design-competition documentation.

## Claimed Contributions

1. A MATLAB-native agentic tutor workflow for biomedical circuit learning.
2. A model-grounded authority structure that separates LLM communication from executable engineering evidence.
3. Live evidence across three benchmarks: RC anti-aliasing, two-electrode voltage clamp equilibrium, and mixed-signal neural clamp with educational scaled parameters.
4. A submission-oriented evidence export path linking prompts, assumptions, generated models, teaching/probe artifacts, plots, metrics, limitations, and release verification.

## Evidence Boundaries

- This is educational software, not patient-facing software.
- The current prototype does not diagnose, monitor, treat, or control patient care.
- Benchmark 3 uses educational scaled parameters and should not be described as a real biological or patient model.
- Full external Lab Delta CSV comparison remains pending because no external lab CSV was supplied.
- LLM-only baseline outputs are non-exhaustive no-tools comparisons, not a comprehensive benchmark of all LLM systems.
- The paper should be described as a CVPR-style systems draft for course/design-competition review, not a ready real CVPR submission.
