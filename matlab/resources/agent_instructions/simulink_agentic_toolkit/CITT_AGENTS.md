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

- Do not require the student to cross-reference hidden parameters. Put key values in component labels, focus-map explanations, or probe-map instructions.
- Prefer concise labels that fit in the learning UI.
- The model should remain readable when shown above the learning prompt on a 14-inch laptop screen.
