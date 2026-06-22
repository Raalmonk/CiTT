# CiTT BMES Submission Branch

CiTT, also known as VeriCircuit Tutor, is a MATLAB-centered tutor for model-grounded biomedical circuit learning. The clean BMES submission branch is:

```text
bmes-2026-submission
```

## Main Demo Surface

The main demo surface is the MATLAB plugin.

Run from MATLAB after cloning this repository:

```matlab
addpath("matlab")
citt
```

CiTT uses agent-assisted circuit interpretation for a circuit prompt or image, produces a structured circuit specification, uses a SATK/MCP-enabled agent flow to build a Simulink/Simscape model, and then teaches through a model-centered dialog with focus-map highlights, natural-language probes, and evidence export.

The backend and frontend development workspaces are intentionally not included on this submission branch.

## Requirements

- MATLAB
- Simulink
- Simscape
- Simscape Electrical, recommended for the live model-building flow
- Simulink Agentic Toolkit (SATK) and MATLAB MCP Server
- Configured LLM/agent backend for circuit interpretation and orchestration. This can be direct Gemini API credentials or a local Gemini/Codex-compatible CLI backend.
- SATK-configured agent CLI, such as `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

Local secrets and generated work products are intentionally not part of the release:

- Do not commit `.env` files.
- Do not commit API keys.
- Do not commit `slprj/`.
- Do not commit `*.slxc`.
- Do not commit `matlab/work/` unless a specific artifact is deliberately archived under `submission_assets/`.

## Release Docs

- [Release setup](docs/release_setup.md)
- [Live GUI evidence demo](docs/demo_live_gui_evidence.md)
- [BMES application answers](paper_orchestra/bmes_application/application_answers_draft.md)
- [MATLAB plugin details](matlab/README.md)

## Submission Evidence

Use the live GUI evidence package as the final evidence entry point:

- [submission_assets/live_gui_evidence/](submission_assets/live_gui_evidence/)
- [live evidence report](submission_assets/live_gui_evidence/bmes_live_evidence_report.md)

This clean submission branch excludes older offline draft reports, placeholder panels, source benchmark folders, and generated draft screenshots. Reviewer-facing evidence is limited to the live GUI evidence package and release artifacts listed here.

## Repository Map

```text
README.md
matlab/
  citt.m
  +citt/
  resources/
  README.md
docs/
  release_setup.md
  demo_live_gui_evidence.md
release/
submission_assets/
  live_gui_evidence/
paper_orchestra/
  bmes_application/
    application_answers_draft.md
    application_answers_word_counts.md
```

## Evidence Boundary

CiTT separates LLM/agent help from numerical and model evidence. A configured model provider or local CLI runtime may perform agent-assisted circuit interpretation into a structured specification, and the tutor may explain the result, but final claims should be grounded in the generated Simulink/Simscape model, focus/probe artifacts, exported evidence, and explicit limitations recorded in `submission_assets/live_gui_evidence/`.
