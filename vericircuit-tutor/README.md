# CiTT Release Candidate

CiTT, also known as VeriCircuit Tutor, is a MATLAB-centered tutor for model-grounded biomedical circuit learning. The release candidate branch is:

```text
bmes-2026-release-candidate
```

## Main Demo Surface

The main demo surface is the MATLAB plugin.

Run from MATLAB after cloning this repository:

```matlab
addpath("vericircuit-tutor/matlab")
citt
```

CiTT reads a circuit prompt or image through a configured LLM/agent backend, produces a structured circuit specification, uses a SATK/MCP-enabled agent flow to build a Simulink/Simscape model, and then teaches through a model-centered dialog with focus-map highlights, natural-language probes, and evidence export.

The backend and frontend workspaces are legacy/supporting development surfaces. They are not the release demo path.

## Requirements

- MATLAB
- Simulink
- Simscape
- Simscape Electrical, recommended for the live model-building flow
- Simulink Agentic Toolkit (SATK) and MATLAB MCP Server
- Configured LLM/agent provider for circuit interpretation and orchestration. This can be direct Gemini API credentials or a local Gemini/Codex-compatible CLI backend.
- SATK-configured agent CLI, such as `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

Local secrets and generated work products are intentionally not part of the release:

- Do not commit `.env` files.
- Do not commit API keys.
- Do not commit `slprj/`.
- Do not commit `*.slxc`.
- Do not commit `vericircuit-tutor/matlab/work/` unless a specific artifact is deliberately archived under `submission_assets/`.

## Release Docs

- [Release setup](docs/release_setup.md)
- [Live GUI evidence demo](docs/demo_live_gui_evidence.md)
- [BMES application answers](docs/bmes_application_answers.md)
- [MATLAB plugin details](matlab/README.md)

## Submission Evidence

Use the live GUI evidence package as the final evidence entry point:

- [submission_assets/live_gui_evidence/](submission_assets/live_gui_evidence/)
- [live evidence report](submission_assets/live_gui_evidence/bmes_live_evidence_report.md)

The older offline draft reports, placeholder panels, source benchmark folders, and generated draft screenshots under `submission_assets/` are retained only for provenance. They are not final submission proof.

## Repository Map

```text
vericircuit-tutor/
  README.md
  matlab/
    citt.m
    +citt/
    resources/
    README.md
  docs/
    release_setup.md
    demo_live_gui_evidence.md
    bmes_application_answers.md
  submission_assets/
    live_gui_evidence/
```

## Evidence Boundary

CiTT separates LLM/agent help from numerical and model evidence. A configured model provider or local CLI runtime may interpret a prompt or image into a structured specification, and the tutor may explain the result, but final claims should be grounded in the generated Simulink/Simscape model, focus/probe artifacts, exported evidence, and explicit limitations recorded in `submission_assets/live_gui_evidence/`.
