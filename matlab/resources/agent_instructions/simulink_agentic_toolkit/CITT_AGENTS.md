# CiTT-specific SATK agent addendum

These instructions specialize the repo-local Simulink Agentic Toolkit guidance for CiTT model-building tasks.

## Non-negotiable execution boundary

- Use the user-selected CLI command that launched the task. Do not switch providers or invoke an alternate CLI.
- Do not read external skill directories such as `/Users/Raalm/.agents/skills`, `/Users/Raalm/.codex/skills`, or provider-specific global config folders.
- Do not invoke subagents, shell tools, or local CiTT deterministic builders.
- Build through SATK/MCP model tools. If `model_edit` cannot create or edit the model, write an agent report explaining the SATK/MCP failure instead of producing substitute artifacts.

## Simscape-first modeling contract

- Build the physical path with Simscape/Simscape Electrical blocks whenever a physical component or node is present.
- Use physical `portName <-> portName` connections for electrical/physical networks.
- Include Solver Configuration and domain reference blocks for each physical network.
- Use controlled Simulink blocks only at explicit educational boundaries, such as PK input generation, ADC code calculation, or a documented wrapper around a physical sensor path.
- Keep omitted or symbolic component values as named model parameters; do not invent hidden numbers.
- Use `model_query_params` and `model_resolve_params` to inspect or resolve parameters before making numeric claims.
- Add voltage/current sensors and PS-Simulink Converter blocks for every requested measurable electrical output.
- Add logging blocks or outports so CiTT can measure outputs without visually inspecting the diagram.

## Focus and probe map contract

- Focus map entries must point to real model/block paths that can be highlighted.
- Probe map entries must identify the physical sensor/logging path, quantity, unit, and student-safe measurement instruction.
- Teaching questions should be plain text by default.
- If LaTeX is necessary, keep it short, balanced, and simple: inline `$...$` only, no custom commands, no environments, no raw HTML.
- Never emit malformed LaTeX in focus/probe maps. Prefer `Rf = 1 MOhm` over fragile formula markup.

## 14-inch UI and student usability

- CiTT is a teaching tool first. Keep the learning experience simple, clear, and focused on the current concept.
- The student should see the relevant model evidence, the current question, the key facts needed to answer it, and one obvious next action.
- Do not design focus/probe content that requires the student to inspect hidden files or cross-reference separate artifacts.
- Do not require the student to cross-reference hidden parameters. Put key values in component labels, focus-map explanations, or probe-map instructions.
- Prefer concise labels that fit in the learning UI.
- The model should remain readable when shown above the learning prompt on a 14-inch laptop screen.
- Teaching steps should support local model crops. Put the most relevant block paths first, and keep focus entries small enough that a cropped snapshot is readable.
- Avoid long block names and labels when a concise engineering label with units is enough.

## QA and visual acceptance requirements

- A command passing is not enough for UI work. Verify rendered screenshots or computer-vision output when changing model previews, LaTeX, teaching cards, or layout.
- Reject model preview snapshots that are mostly blank canvas, shifted into a corner, clipped, or too zoomed out to read labels.
- Check the actual current teaching focus, not only the whole model. If the full diagram is too wide, the teaching surface should show a relevant local region.
- Keep the teaching action surface small: no more than three visible primary controls; secondary actions belong behind a `+` menu.
- Bad or overly complex LaTeX must degrade to plain text. Prefer plain text in focus/probe maps unless short inline math materially improves the lesson.
- Treat user screenshots as QA evidence. If the screenshot is not readable on a 14-inch-class screen, the change is not done.
