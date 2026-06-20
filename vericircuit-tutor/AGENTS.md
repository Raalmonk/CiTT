# VeriCircuit Tutor Agent Instructions

## Product Direction

- CiTT is now a MATLAB-native plugin shell around Gemini and Simulink Agentic Toolkit.
- The main runnable entry point is `vericircuit-tutor/matlab/citt.m`; users should add `vericircuit-tutor/matlab` to the MATLAB path and run `citt`.
- Do not continue expanding the old web-first MATLAB playground, fake artifact APIs, or static generated lab examples.
- Keep existing backend/web code working when needed for tests, but do not make it the center of new work.

## Runtime Flow

- Student input starts inside MATLAB: circuit image and/or short prompt.
- Gemini is required for real image/prompt to structured circuit parsing.
- `GEMINI_API_KEY` may come from the MATLAB process environment or local untracked `.env` files.
- Default Gemini model is `gemini-3.5-flash`.
- Never commit real API keys. `vericircuit-tutor/matlab/.env` is local-only; use `.env.example` for placeholders.
- Gemini parses the circuit spec only. It is not the numerical or engineering authority.
- The generated SATK agent task must be Simscape-first and should request Simulink Agentic Toolkit tools such as `model_overview`, `model_read`, `model_edit`, `model_check`, `model_query_params`, and `model_resolve_params`.
- Build Model must also generate runnable MATLAB build code at `matlab/work/citt_build_simscape_model.m`, execute it in the current MATLAB session, save `matlab/work/citt_generated_model.slx`, and open the model.
- Do not block model drawing just because a value is symbolic, omitted, or irrelevant to the requested loop. Preserve it as a named Simscape parameter such as `V_c` or `CITT_R1_value`, and report that simulation/checking will need numeric values.
- If SATK, MATLAB MCP, Simulink, or Simscape is missing, do not fake success. Fail fast. External agent CLIs are optional extensions, not the only model-drawing path.

## MATLAB Implementation Rules

- MATLAB package directories must use `+` prefixes, including nested packages such as `+citt/+util`.
- Because the launcher is named `citt.m` and the package is `+citt`, prefer `feval('citt.functionName', ...)` and `feval('citt.util.functionName', ...)` from package internals when needed to avoid MATLAB dot-indexing conflicts.
- Keep UI code in `+citt/openApp.m` and behavior in focused package functions.
- Long UI actions must update the header stage bar and use a MATLAB progress dialog when they can take noticeable time.
- User-facing panes should show concise summaries, artifact paths, issues, and next steps. Raw JSON should stay available through files or explicit open/view actions, not as the default primary feedback.
- The Read Circuit tab supports drag/drop through `uihtml`; dropped images are saved under the local ignored MATLAB work directory.
- Required plugin functions include setup checks, Gemini parsing, agent task generation/running, model open/check/simulation, teaching plan, Socratic turn, highlight/zoom, probe, and Lab Delta.
- Highlight and zoom must use generated focus maps. Missing or stale model paths should fail visibly.
- Probe insertion must reference the actual generated model/probe map.

## Numerical And Teaching Boundaries

- Be explicit and conservative.
- Do not fake solver results, Simulink results, model checks, SATK execution, or successful model generation.
- Do not let an LLM generate final numerical answers directly.
- Numerical answers must come from verified calculations, solver/verifier evidence, or the generated MATLAB/Simulink/Simscape model.
- Any explanation should cite model/spec/check/simulation evidence where available.
- If a requested circuit feature is unsupported or ambiguous, report that clearly instead of pretending to solve it.
- Socratic teaching should ask a local question first and reveal one hint at a time.

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

## Style

- Prefer small, readable modules over clever abstractions.
- Keep docs concise and demo-oriented.
- Do not add large canned example packs unless a test or demo explicitly needs a tiny fixture.
