# CiTT MATLAB Plugin

CiTT is now a MATLAB-native plugin shell around Gemini and Simulink Agentic Toolkit.

Run it from MATLAB:

```matlab
addpath("vericircuit-tutor/matlab")
citt
```

The app opens eight concise tabs and shows a persistent stage bar in the header while longer steps also open a MATLAB progress dialog:

- Read: drag in or browse for a circuit image, optionally add a prompt, then parse with Gemini.
- Build: prepare the SATK task, run a SATK-enabled external agent, and open the produced Simulink/Simscape model.
- Model: open, check, and simulate the generated Simulink/Simscape model.
- Teach: build a Socratic plan from the circuit spec and focus map, then highlight or zoom focus points.
- Probe: add guided probes and compare hand, simulation, and lab CSV values.
- Verify: export requirement checks, RC tolerance sweeps, educational fault scenarios, and explainability action maps.
- Plan: export learning-gain evidence, deployment cost assumptions, and regulatory/scope guardrails.
- Export: export `matlab/work/citt_evidence_pack.md` with source input, structured spec, model/check/simulation evidence, requirement status, focus/probe maps, Lab Delta, limitations, risks, and a BMES functional-proof draft.

The Read Circuit tab shows a human-readable spec summary and next step. Use Open JSON only when you want the raw file.
Symbolic or omitted values such as `V_c` are kept as Simscape parameters. They do not block model drawing; they only need values before simulation/checking.

Required for the real flow:

- `GEMINI_API_KEY`
- Gemini model `gemini-3.5-flash` unless `GEMINI_MODEL` is explicitly set
- Simulink
- Simscape, preferably Simscape Electrical
- Simulink Agentic Toolkit initialized with `satk_initialize`
- MATLAB MCP Server
- A SATK-configured agent CLI via `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

If MATLAB was opened from the Dock and cannot see shell environment variables, create a local untracked file:

```text
vericircuit-tutor/matlab/.env
```

with:

```text
GEMINI_API_KEY=your_key_here
```

Build Model writes `matlab/work/citt_agent_task.md`, hands it to `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI, then validates that the agent produced `matlab/work/citt_generated_model.slx`, focus map, probe map, and report. In the MATLAB UI, the external agent is launched asynchronously so MATLAB remains free for MCP/SATK tool calls; CiTT polls `matlab/work/citt_agent_stdout.log` and artifact freshness until the run finishes. If no agent CLI is available, CiTT opens the task markdown for manual-agent mode. The deterministic local Simscape builder is available only as an explicit emergency/demo fallback with `CITT_USE_LOCAL_SIMSCAPE_FALLBACK=1`.

External agent runs retry transient API failures such as `503 Service Unavailable` by default. Tune with `CITT_AGENT_MAX_ATTEMPTS` and `CITT_AGENT_RETRY_DELAY_SECONDS` if the selected agent endpoint is noisy.
