# CiTT Release Setup

This release is the MATLAB-native CiTT plugin package for BMES/Medtronic review. The main launch path remains:

```matlab
addpath("matlab")
citt
```

After installing the MATLAB toolbox package, `citt` should also resolve directly from the MATLAB path.

## Install From Toolbox

From MATLAB, install the packaged release:

```matlab
matlab.addons.toolbox.installToolbox("release/CiTT_BMES_2026.mltbx")
citt.checkSetup
citt
```

You can also double-click `release/CiTT_BMES_2026.mltbx` in MATLAB or the file browser.

## Install From Source Zip

If toolbox installation is unavailable, unzip the fallback source package:

```text
release/CiTT_BMES_2026_Source.zip
```

Then add the plugin folder to the MATLAB path:

```matlab
addpath("CiTT_BMES_2026_Source/matlab")
citt.checkSetup
citt
```

If you are running from the repository rather than the zip, use:

```matlab
addpath("matlab")
citt.checkSetup
citt
```

## Required Products And Services

Minimum release target:

- MATLAB
- Simulink
- Simscape
- Simscape Electrical preferred
- Simulink Agentic Toolkit / SATK-compatible flow
- MATLAB MCP Server
- Configured LLM/agent backend for agent-assisted circuit interpretation and orchestration
- Backend route such as direct Gemini API credentials, Gemini CLI, Codex-compatible CLI, or another configured agent path
- Configured agent CLI for SATK/MCP model building

The release evidence assumes no custom Simscape libraries and no custom project-specific block libraries. CiTT should prefer built-in MATLAB, Simulink, Simscape, and Simscape Electrical blocks.

## Environment Variables

Required for the full agent-assisted flow: a configured LLM/agent backend. Gemini API credentials are one supported route; the release evidence path may also use a local CLI/agent route for both circuit interpretation and model-building.

```bash
export CITT_AGENT_COMMAND="your-agent-cli-command"
```

Optional for direct Gemini API or a Gemini-backed local CLI:

```bash
export GEMINI_API_KEY="your_key_here"
export GEMINI_MODEL="gemini-3.5-flash"
```

If MATLAB is opened from the Dock or another launcher that does not inherit shell environment variables, create a local untracked file:

```text
matlab/.env
```

with:

```text
CITT_AGENT_COMMAND=your-agent-cli-command
# Optional if using direct Gemini API or a Gemini-backed local CLI:
GEMINI_API_KEY=your_key_here
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

The build step expects the agent to use SATK/MCP model tools and to produce local work products under `matlab/work/`:

```text
citt_generated_model.slx
citt_focus_map.json
citt_probe_map.json
citt_agent_report.md
```

`matlab/work/` is ignored by Git and is not included in the release package.

When CiTT is installed from `.mltbx` and the Add-Ons install folder is read-only, CiTT falls back to MATLAB's writable `prefdir/CiTT/work` folder for settings and generated work products.

## Run A Demo

1. Launch `citt`.
2. Enter a prompt or select a circuit image.
3. Read/interpret the circuit with the configured LLM/agent backend.
4. Build the model through the SATK/MCP agent flow.
5. Inspect the generated Simulink/Simscape model.
6. Use the teaching dialog to step through model-linked explanations.
7. Use natural-language probe requests to ask for measurements.
8. Export evidence from the Evidence message/thread.

For the final BMES evidence map, see [demo_live_gui_evidence.md](demo_live_gui_evidence.md).

## Common Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| AI-backed read step unavailable | No configured LLM/agent backend is visible to MATLAB | Set `CITT_AGENT_COMMAND`, configure a supported CLI, or provide direct provider credentials such as `GEMINI_API_KEY` |
| Gemini works in terminal but not MATLAB | Environment mismatch | Check `getenv("GEMINI_API_KEY")` inside MATLAB or use a local CLI route through `CITT_AGENT_COMMAND` |
| Simscape blocks missing | Simscape or Simscape Electrical is unavailable | Install/enable Simscape and Simscape Electrical |
| SATK shown as missing | `satk_initialize` is not on the MATLAB path | Install/configure SATK, add the toolkit path, then run `satk_initialize` |
| MATLAB MCP unavailable | Agent CLI cannot reach MATLAB model tools | Configure MATLAB MCP Server for the agent workflow |
| Agent CLI unavailable | No `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI found | Set `CITT_AGENT_COMMAND` or install/configure a supported CLI |
| Build finishes without `.slx` or maps | Agent failed or wrote to the wrong path | Check `matlab/work/citt_agent_stdout.log` and `matlab/work/citt_agent_report.md` |
| Benchmark 2 has symbolic values | The source problem omits `V_c` and `R_e` | Treat this as structural teaching evidence until numeric values are supplied |
| Benchmark 3 does not settle | Educational parameter set exposes rail/current limits | Report as limitation-discovery evidence, not as a medical-use validation claim |
| Lab Delta CSV cannot run | No external lab CSV was supplied | Leave Lab Delta marked incomplete rather than fabricating a comparison |
| Old artifacts appear in the UI | Stale `matlab/work/` cache | Clear `matlab/work/` locally and rerun |

## Release Hygiene

Do not package or commit:

- `.env` files
- API keys
- `slprj/`
- `*.slxc`
- `matlab/work/`
- MATLAB caches or generated work folders
- old offline draft evidence as final proof

Final review evidence belongs in [submission_assets/live_gui_evidence](../submission_assets/live_gui_evidence/).

## Setup References

- [Google Gemini API key documentation](https://ai.google.dev/gemini-api/docs/api-key)
- [MathWorks Simulink Agentic Toolkit](https://www.mathworks.com/products/simulink-agentic-toolkit.html)
- [MathWorks MATLAB MCP Server](https://www.mathworks.com/products/matlab-mcp-server.html)
- [MathWorks Simscape documentation](https://www.mathworks.com/help/simscape/index.html)
- [MathWorks Simscape Electrical documentation](https://www.mathworks.com/help/sps/index.html)
