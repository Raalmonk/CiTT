# CiTT

CiTT, also known as VeriCircuit Tutor, is a MATLAB plugin for model-grounded biomedical circuit learning. It turns a circuit prompt or image into an agent-assisted circuit specification, builds a Simulink/Simscape model through a configured agent workflow, and supports teaching, highlighting, probing, and evidence export from the MATLAB UI.

This branch is the clean BMES 2026 submission branch: `bmes-2026-submission`.

## Install The MATLAB Plugin

Option A: install the packaged toolbox from MATLAB.

```matlab
matlab.addons.toolbox.installToolbox("release/CiTT_BMES_2026.mltbx")
citt.checkSetup
citt
```

Option B: run directly from this repository.

```matlab
addpath("matlab")
citt.checkSetup
citt
```

Option C: use the source fallback package.

```matlab
unzip("release/CiTT_BMES_2026_Source.zip")
addpath("CiTT_BMES_2026_Source/matlab")
citt.checkSetup
citt
```

## Configure Your Agent CLI

CiTT needs a configured LLM/agent backend for the full read/build workflow. The simplest path is to point CiTT at your own CLI with `CITT_AGENT_COMMAND`.

If your CLI accepts a task file path:

```matlab
setenv("CITT_AGENT_COMMAND", "your-agent-cli --task {taskPath}")
```

If your CLI reads the task from standard input:

```matlab
setenv("CITT_AGENT_COMMAND", "cat {taskPath} | your-agent-cli -")
```

Then verify setup and launch:

```matlab
citt.checkSetup
citt
```

`{taskPath}` is replaced with the generated CiTT agent task. `{task}` works as an equivalent placeholder. If no placeholder is present, CiTT appends the task path to the end of the command.

## Codex Or Gemini CLI

CiTT can also auto-select a supported CLI backend.

For Codex CLI:

```matlab
setenv("CITT_AGENT_BACKEND", "codex")
citt.checkSetup
```

For Gemini CLI:

```matlab
setenv("CITT_AGENT_BACKEND", "gemini")
setenv("GEMINI_MODEL", "gemini-3.5-flash")
citt.checkSetup
```

For direct Gemini API parsing, also provide:

```matlab
setenv("GEMINI_API_KEY", "your_key_here")
```

Gemini is one supported provider, but CiTT does not require Gemini specifically; the requirement is a configured LLM/agent backend.

## Make Configuration Persistent

If MATLAB does not inherit shell environment variables, create a local `matlab/.env` file:

```text
CITT_AGENT_COMMAND="your-agent-cli --task {taskPath}"
```

For auto-selected Codex or Gemini CLI, use backend variables instead of `CITT_AGENT_COMMAND`:

```text
CITT_AGENT_BACKEND=codex
```

or:

```text
CITT_AGENT_BACKEND=gemini
GEMINI_MODEL=your_gemini_model
GEMINI_API_KEY=your_key_here
```

Only include the variables you need. `CITT_AGENT_COMMAND` takes priority when it is set. You can also configure the agent command from the CiTT UI settings panel.

## Required MATLAB Components

- MATLAB
- Simulink
- Simscape
- Simscape Electrical, recommended for the live model-building flow
- Simulink Agentic Toolkit / SATK-compatible flow
- MATLAB MCP Server for agent-controlled model building

Run `citt.checkSetup` after installation to see which products, paths, agent settings, and optional providers are visible to MATLAB.

## Reviewer Materials

- Prototype upload images: [release/prototype_upload_images/](release/prototype_upload_images/)
- Primary upload image: [01_workflow_llm_vs_citt.png](release/prototype_upload_images/01_workflow_llm_vs_citt.png)
- Optional contact sheet: [00_contact_sheet_optional.png](release/prototype_upload_images/00_contact_sheet_optional.png)
- Upload checklist: [release/BMES_Submission_Upload_Checklist.md](release/BMES_Submission_Upload_Checklist.md)
- Setup details: [docs/release_setup.md](docs/release_setup.md)
- Live GUI evidence map: [docs/demo_live_gui_evidence.md](docs/demo_live_gui_evidence.md)
- Live evidence folder: [submission_assets/live_gui_evidence/](submission_assets/live_gui_evidence/)
- BMES application draft: [paper_orchestra/bmes_application/application_answers_draft.md](paper_orchestra/bmes_application/application_answers_draft.md)

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
  prototype_upload_images/
submission_assets/
  live_gui_evidence/
    prototype_upload_images/
paper_orchestra/
  bmes_application/
    application_answers_draft.md
    application_answers_word_counts.md
```

## Scope

CiTT is an educational MATLAB/Simscape tutoring demo. It provides model-linked teaching evidence for benchmark circuits and is not a patient-facing device.
