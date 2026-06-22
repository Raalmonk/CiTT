# CiTT Release Setup

This release is meant to be cloned, opened in MATLAB, and run through the MATLAB plugin:

```matlab
addpath("vericircuit-tutor/matlab")
citt
```

## MATLAB Version

Release target: MATLAB R2025a or newer.

Use the newest MATLAB release available to your lab if you are reproducing the SATK/MCP model-building workflow. The plugin checks for the required products and reports missing setup items in the UI.

## Required Toolboxes And Products

- MATLAB
- Simulink
- Simscape
- Simscape Electrical, recommended for the live electrical models
- Simulink Agentic Toolkit (SATK)
- MATLAB MCP Server
- Gemini API access
- A SATK/MCP-capable agent CLI, configured through `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

The release evidence assumes no custom Simscape libraries and no custom project-specific block libraries. Models should use built-in MATLAB, Simulink, Simscape, and Simscape Electrical blocks whenever possible.

## Gemini Key Setup

CiTT reads `GEMINI_API_KEY` from the MATLAB process environment or from an untracked local file.

Preferred shell setup before opening MATLAB:

```bash
export GEMINI_API_KEY="your_key_here"
```

If MATLAB is opened from the Dock or another launcher that does not inherit shell environment variables, create:

```text
vericircuit-tutor/matlab/.env
```

with:

```text
GEMINI_API_KEY=your_key_here
```

Optional:

```text
GEMINI_MODEL=gemini-3.5-flash
```

Do not commit `.env` files or API keys.

## SATK/MCP Setup

Install and configure the MathWorks agentic tooling for MATLAB/Simulink. If available in your MATLAB installation, run:

```matlab
setupAgenticToolkit("install")
satk_initialize
```

If SATK is already installed but not on the MATLAB path, add the installed toolkit path first, then run:

```matlab
satk_initialize
```

Configure an external agent command if auto-detection does not find one:

```bash
export CITT_AGENT_COMMAND="your-agent-cli-command"
```

The build step expects the agent to use SATK/MCP model tools and to produce these local work products:

```text
vericircuit-tutor/matlab/work/citt_generated_model.slx
vericircuit-tutor/matlab/work/citt_focus_map.json
vericircuit-tutor/matlab/work/citt_probe_map.json
vericircuit-tutor/matlab/work/citt_agent_report.md
```

`matlab/work/` is ignored by Git because it is a local work cache.

## Run CiTT

From the repository parent folder in MATLAB:

```matlab
addpath("vericircuit-tutor/matlab")
citt
```

If your MATLAB current folder is already `vericircuit-tutor`, use:

```matlab
addpath("matlab")
citt
```

## Run A Demo

1. Launch `citt`.
2. Enter a prompt or choose an input image.
3. Read/parse the circuit with Gemini.
4. Build the model through the SATK/MCP agent flow.
5. Inspect the generated Simulink/Simscape model.
6. Use the teaching dialog to step through model-linked explanations.
7. Use natural-language probe requests to ask for measurements.
8. Export evidence from the Evidence message/thread.

For a known demo script and evidence map, use [demo_live_gui_evidence.md](demo_live_gui_evidence.md).

## Common Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `GEMINI_API_KEY` missing | MATLAB did not inherit shell environment variables | Add `vericircuit-tutor/matlab/.env` locally or launch MATLAB from the configured shell |
| Gemini works in terminal but not MATLAB | Environment mismatch | Check `getenv("GEMINI_API_KEY")` inside MATLAB |
| SATK shown as missing | `satk_initialize` is not on the MATLAB path | Install/configure SATK, add the toolkit path, then run `satk_initialize` |
| MCP/model tools unavailable to the agent | Agent CLI is not configured for MATLAB MCP | Configure the agent with MATLAB MCP Server and SATK tools |
| Build finishes without `.slx` or maps | Agent failed or wrote to the wrong path | Check `matlab/work/citt_agent_stdout.log` and `matlab/work/citt_agent_report.md` |
| Simscape blocks missing | Required toolbox unavailable | Install/enable Simscape and Simscape Electrical |
| Benchmark 2 has symbolic values | The source problem omits `V_c` and `R_e` | Treat this as structural teaching evidence until numeric values are supplied |
| Benchmark 3 does not settle | Educational parameter set exposes rail/current limits | Report as limitation-discovery evidence, not as a successful clinical model |
| Old artifacts appear in the UI | Stale `matlab/work/` cache | Clear `vericircuit-tutor/matlab/work/` locally and rerun |

## Release Hygiene

Do not commit:

- `.env` files
- API keys
- `slprj/`
- `*.slxc`
- `vericircuit-tutor/matlab/work/`
- MATLAB work cache, unless a specific artifact is deliberately archived under `submission_assets/`

Final review evidence belongs in [submission_assets/live_gui_evidence](../submission_assets/live_gui_evidence/).

## Setup References

- [Google Gemini API key documentation](https://ai.google.dev/gemini-api/docs/api-key)
- [MathWorks Simulink Agentic Toolkit](https://www.mathworks.com/products/simulink-agentic-toolkit.html)
- [MathWorks MATLAB MCP Server](https://www.mathworks.com/products/matlab-mcp-server.html)
- [MathWorks Simscape documentation](https://www.mathworks.com/help/simscape/index.html)
- [MathWorks Simscape Electrical documentation](https://www.mathworks.com/help/sps/index.html)
