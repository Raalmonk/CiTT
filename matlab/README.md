# CiTT MATLAB Plugin

CiTT is a MATLAB-native plugin shell around a configurable LLM/agent backend, SATK/MCP-style model building, and Simulink/Simscape evidence.

Run it from MATLAB:

```matlab
addpath("matlab")
citt
```

## Current UI

The current app uses a Codex-style learning dialog rather than the older eight-tab layout.

Main flow:

- Start with a circuit prompt and optional image in the input composer.
- CiTT reads the circuit into a structured spec and records assumptions instead of hiding ambiguity.
- Build runs the external model-building agent and validates that the model, focus map, probe map, and report were produced.
- The generated Simulink/Simscape model is opened in MATLAB/Simulink for inspection and manual arrangement when needed.
- Teaching and probe happen in the same learning surface: the model screenshot stays above, and the student-facing dialog sits below it.
- Teaching steps are focus-map linked. Highlight actions should select the relevant part of the Simulink/Simscape model.
- Probe is natural-language driven. A student can type a measurement request, CiTT maps it to a probe target, and the result is printed back into the same dialog.
- Evidence export is available through the Evidence message/thread and writes an evidence pack such as `matlab/work/citt_evidence_pack.md`.

The old "Read, Build, Model, Teach, Probe, Verify, Plan, Export" tab description is obsolete. Some internal tooling still has page/action names for compatibility, but the release UI should be described as a model-centered learning dialog with chat-style teaching, probe, and evidence output.

## Modeling Behavior

The Read Circuit step shows a human-readable spec summary and next step. Use Open JSON only when you want the raw file.

Symbolic or omitted values such as `V_c` are kept as Simscape parameters. They do not block model drawing; they only need values before numeric simulation/checking.

Default release assumption:

- No custom Simscape libraries.
- No custom project-specific block libraries.
- Use built-in MATLAB, Simulink, Simscape, and Simscape Electrical blocks whenever possible.

## Required For The Real Flow

- Simulink
- Simscape, preferably Simscape Electrical
- Simulink Agentic Toolkit initialized with `satk_initialize`
- MATLAB MCP Server
- A configured LLM/agent backend for circuit interpretation and orchestration. This can be direct Gemini API credentials, a local Gemini-compatible CLI, a Codex-compatible CLI, or another configured agent route.
- A SATK-configured agent CLI via `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI for the model-building path.

For the release evidence path, the first circuit-interpretation step and the later Simulink/Simscape build step may both run through the same local CLI/agent workflow. Gemini remains one supported model provider, but the direct Gemini API is not the only parsing route.

If MATLAB was opened from the Dock and cannot see shell environment variables, create a local untracked file:

```text
matlab/.env
```

with:

```text
CITT_AGENT_COMMAND=your-agent-cli-command
# Optional if using direct Gemini API or a Gemini-backed local CLI:
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=your_model_here
```

## Agent Build

Build Model writes `matlab/work/citt_agent_task.md`, hands it to `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI, then validates that the agent produced:

- `matlab/work/citt_generated_model.slx`
- `matlab/work/citt_focus_map.json`
- `matlab/work/citt_probe_map.json`
- `matlab/work/citt_agent_report.md`

In the MATLAB UI, the external agent is launched asynchronously so MATLAB remains free for MCP/SATK tool calls. CiTT polls `matlab/work/citt_agent_stdout.log` and artifact freshness until the run finishes. If no agent CLI is available, CiTT opens the task markdown for manual-agent mode.

The deterministic local Simscape builder is available only as an explicit emergency/demo fallback with:

```text
CITT_USE_LOCAL_SIMSCAPE_FALLBACK=1
```

Do not enable the fallback for release testing unless the goal is explicitly to test that fallback path.

External agent runs retry transient service errors by default. Tune with `CITT_AGENT_MAX_ATTEMPTS` and `CITT_AGENT_RETRY_DELAY_SECONDS` if the selected agent endpoint is noisy.

## Evidence Boundaries

Natural-language Probe evidence can be claimed when the measurement appears back in the learning dialog.

Full Lab Delta CSV comparison should not be claimed as completed unless a real external lab CSV was supplied and captured in the live evidence run.

For Benchmark 3 style mixed-signal examples, poor settling is not a design success claim. It should be described as simulation-grounded limitation discovery: CiTT generated and analyzed a complex mixed-signal model, and the simulation exposed saturation, non-settling behavior, ADC/digital behavior, and parameter/fault sensitivity.
