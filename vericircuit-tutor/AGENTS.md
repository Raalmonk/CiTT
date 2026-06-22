# VeriCircuit Tutor Agent Instructions

## Product Direction

- CiTT is now a MATLAB-native plugin shell around Gemini and Simulink Agentic Toolkit.
- The main runnable entry point is `vericircuit-tutor/matlab/citt.m`; users should add `vericircuit-tutor/matlab` to the MATLAB path and run `citt`.
- Do not continue expanding the old web-first MATLAB playground, fake artifact APIs, or static generated lab examples.
- Keep existing backend/web code working when needed for tests, but do not make it the center of new work.
- The product north star is a Codex-style tutor conversation inside MATLAB: the generated Simulink/Simscape model stays visually dominant above, and teaching/probe interaction happens in the dialog below it.
- Do not turn the primary experience into a utility/tool-panel dashboard. Tool sections can exist as secondary/internal controls, but screenshots and user workflows should show the model-plus-dialog teaching surface.

## Current UI Contract

- The main learning screen is: large Simulink/Simscape snapshot on top, Socratic teaching card and natural-language probe input below.
- Probe is chat-invoked. A student should type or ask in plain language, for example `measure probe_vm voltage`, and the result must print back into the same learning/probe dialog.
- Do not expose probe as the main workflow through a separate tool form, sidebar panel, or evidence dashboard. If a hidden tool panel is needed for debugging, it must not replace the conversation surface.
- Probe actions during teaching are preview-only by default. They may highlight/select existing probe targets and summarize existing logs or model parameters, but they must not add blocks, logging chains, lines, or save model changes unless the user explicitly asks.
- Teaching and probe text must keep LaTeX-style symbol rendering. Circuit symbols such as `V_m`, `V_c`, `R_e`, `R_o`, `R_m`, transfer functions, fractions, and time constants should render with subscripts/fractions in the HTML app, including inside probe results.
- Highlight should follow the current teaching/probe target and update the model snapshot without shrinking the model into a decorative card.
- Do not add or restore split dashboard layouts, marketing-style panels, or nested cards around the primary learning flow.
- The right-side context should remain minimal; do not reintroduce a large persistent inspector column as the main interaction surface.
- If navigation to an "evidence" or "probe" state is needed, preserve the model-plus-dialog form. Do not hide the learning surface just to show tool buttons.

## Runtime Flow

- Student input starts inside MATLAB: circuit image and/or short prompt.
- Gemini is required for real image/prompt to structured circuit parsing.
- `GEMINI_API_KEY` may come from the MATLAB process environment or local untracked `.env` files.
- Default Gemini model is `gemini-3.5-flash`.
- Never commit real API keys. `vericircuit-tutor/matlab/.env` is local-only; use `.env.example` for placeholders.
- Gemini parses the circuit spec only. It is not the numerical or engineering authority.
- The generated SATK agent task must be Simscape-first and should request Simulink Agentic Toolkit tools such as `model_overview`, `model_read`, `model_edit`, `model_check`, `model_query_params`, and `model_resolve_params`.
- Build Model must invoke a SATK-compatible external agent CLI with `matlab/work/citt_agent_task.md`. The agent is responsible for using SATK/MCP tools to save `matlab/work/citt_generated_model.slx`, focus/probe maps, and the agent report.
- The local Simscape builder is only an explicit emergency/demo fallback (`citt.buildLocalSimscapeFallback`), never the default Build Model path.
- Do not block model drawing just because a value is symbolic, omitted, or irrelevant to the requested loop. Preserve it as a named Simscape parameter such as `V_c` or `CITT_R1_value`, and report that simulation/checking will need numeric values.
- If SATK, MATLAB MCP, Simulink, or Simscape is missing, do not fake success. Fail fast. If no external agent CLI is configured, enter manual-agent mode or use the explicit local fallback only when requested.
- Unless the user explicitly declares custom libraries, assume no custom Simscape or project-specific block libraries. Prefer built-in MATLAB, Simulink, Simscape, and Simscape Electrical blocks.
- Do not silently fall back to another model-building path when the user is trying to test a specific path. Fallbacks hide failures and make tests meaningless.

## MATLAB Implementation Rules

- MATLAB package directories must use `+` prefixes, including nested packages such as `+citt/+util`.
- Because the launcher is named `citt.m` and the package is `+citt`, prefer `feval('citt.functionName', ...)` and `feval('citt.util.functionName', ...)` from package internals when needed to avoid MATLAB dot-indexing conflicts.
- Keep HTML app UI code in `resources/ui/citt_app.html` and MATLAB bridge/controller behavior in focused package functions such as `+citt/openHtmlApp.m`. Older `+citt/openApp.m` code is not the current product center unless a task explicitly targets it.
- Long UI actions must update the header stage bar and use a MATLAB progress dialog when they can take noticeable time.
- User-facing panes should show concise summaries, artifact paths, issues, and next steps. Raw JSON should stay available through files or explicit open/view actions, not as the default primary feedback.
- The Read Circuit tab supports drag/drop through `uihtml`; dropped images are saved under the local ignored MATLAB work directory.
- Required plugin functions include setup checks, Gemini parsing, agent task generation/running, model open/check/simulation, teaching plan, Socratic turn, highlight/zoom, probe, and Lab Delta.
- Highlight and zoom must use generated focus maps. Missing or stale model paths should fail visibly.
- Probe insertion must reference the actual generated model/probe map.
- Avoid adding app flows that require the user to know what button comes next after build. After Read/Build/Check are complete, the app should move naturally into teaching/probe readiness.
- When fixing the UI, test at realistic window sizes and verify no horizontal scrollbar appears in the left project list or main learning area.

## Numerical And Teaching Boundaries

- Be explicit and conservative.
- Do not fake solver results, Simulink results, model checks, SATK execution, or successful model generation.
- Do not let an LLM generate final numerical answers directly.
- Numerical answers must come from verified calculations, solver/verifier evidence, or the generated MATLAB/Simulink/Simscape model.
- Any explanation should cite model/spec/check/simulation evidence where available.
- If a requested circuit feature is unsupported or ambiguous, report that clearly instead of pretending to solve it.
- Socratic teaching should ask a local question first and reveal one hint at a time.
- Teaching should tell the student where they are, e.g. Step `i / n`, current focus id, current question, and what model region is highlighted.
- If a numeric result is unavailable because a model parameter remains symbolic, state that in the probe dialog rather than inventing a value.

## Live Evidence Workflow

- BMES/submission evidence must come from the actual visible MATLAB/CiTT/Simulink workflow, not from offline-only artifact generation.
- Use the actual MATLAB GUI when evidence is requested: open CiTT, run the visible app, open generated Simulink/Simscape models, let the user manually arrange diagrams when requested, then capture screenshots after arrangement.
- Do not continue past a manual arrangement checkpoint until the user confirms they are done.
- For each benchmark, keep prompt/problem, baseline prompt, screenshots, notes, plots if any, and comparison files under `submission_assets/live_gui_evidence/<benchmark_name>/`.
- Do not fabricate LLM baseline outputs. If the baseline was not run, mark it pending.
- For Benchmark 1/2 evidence, the important screenshots are parse/read, build, arranged Simscape model, teaching, highlight, and chat-style probe result. The chat-style probe screenshot is more important than an exposed tool-panel screenshot.
- Benchmark 3 is optional complex-demo evidence. Do not claim it is complete unless it has the same live GUI/model/simulation evidence standard.

## Testing

- Always run tests after meaningful changes when the environment supports them.
- If MATLAB is available, run:

```matlab
addpath("vericircuit-tutor/matlab")
cd("vericircuit-tutor/matlab/tests")
run_all
```

- If MATLAB is not available, run static checks:
  - `git diff --check`
  - JSON validation for `matlab/resources/schemas/*.json`
  - Required MATLAB file/resource existence checks
  - Grep that no new web endpoints were added for the MATLAB flow
- For UI changes, also visually verify with screenshots from the MATLAB app. At minimum verify: model snapshot visible, teaching card visible, natural-language probe result visible in the dialog, and LaTeX/subscript rendering present where expected.

## Style

- Prefer small, readable modules over clever abstractions.
- Keep docs concise and demo-oriented.
- Do not add large canned example packs unless a test or demo explicitly needs a tiny fixture.
- When in doubt, preserve the tutor conversation feel. The student should feel like they are talking to CiTT about the model, not operating a form-heavy engineering control panel.
