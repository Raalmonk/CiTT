# CiTT Agent Instructions

CiTT is a teaching tool first. Every code, model, and UI change should preserve a simple, clear learning experience for a student who is trying to understand a model, not operate a complicated engineering cockpit.

## Product Principle

- Keep the learning UI simple and clear. The student should see the model evidence, the current question, the facts needed to answer it, and one obvious next action.
- Do not add visible UI explanation text that teaches the UI itself. The UI should be understandable through layout, labels, and familiar controls.
- Keep primary action surfaces small. In a teaching step, show no more than three primary controls; put secondary actions such as measure, reveal, highlight, refresh, or open model behind a `+` menu.
- Prefer vertical composition for learning: model evidence above, question/input below. Do not place the model and answer panel side by side when that makes the model unreadable on a 14-inch laptop.
- Do not require the student to cross-reference hidden artifacts. Key component values, units, assumptions, and measured quantities must appear in the model labels, teaching facts, focus/probe maps, or current teaching card.

## QA Method

- Test the real user path, not only helper functions. For MATLAB UI work, open CiTT through the MATLAB UI and interact with the actual teaching surface when an accessible MATLAB window is available.
- Verify with computer vision or screenshots whenever the change affects layout, readability, model previews, LaTeX rendering, or teaching flow. A passing command is not enough if the screenshot is hard to read.
- Check a 14-inch-class viewport. The model preview, question, facts, input, and controls must fit without overlapping, tiny text, excessive scrolling, or large empty regions.
- Inspect the rendered model image itself. Reject screenshots where the model is mostly blank canvas, shifted into a corner, clipped, or too zoomed out to read labels.
- Check the current focus, not only the whole model. Teaching steps should show a local, relevant model region when the full diagram is too wide.
- Run at least one real generated example after UI/model-preview changes and save or inspect the resulting snapshot. Include mixed-domain examples such as PK input, mass transfer, Simscape electrical sensing, and ADC conversion when those areas are touched.
- Test malformed and overly complex LaTeX. Bad LaTeX must degrade to plain text instead of breaking the teaching UI or preview UI.
- Treat user screenshots as ground truth. If a screenshot looks unreadable, the QA failed even if automated tests passed.

## MATLAB Launch Method

- On this machine, MATLAB is installed as `/Applications/MATLAB_R2026b.app`. Do not conclude MATLAB is unavailable only because `matlab` is not on the shell `PATH`.
- To open MATLAB interactively, use:
  `open -a /Applications/MATLAB_R2026b.app`
- To run MATLAB commands from shell, use the app executable directly:
  `/Applications/MATLAB_R2026b.app/bin/matlab -batch "addpath('/Users/Raalm/Documents/GitHub/CiTT/matlab'); cd('/Users/Raalm/Documents/GitHub/CiTT/matlab/tests'); results = run_all"`
- For real UI QA, launch MATLAB R2026b, run:
  `addpath('/Users/Raalm/Documents/GitHub/CiTT/matlab'); app = citt;`
  Then interact with the visible CiTT teaching surface as a student would.
- If MATLAB is already open and MCP attach fails, prefer the direct app executable above before reporting MATLAB as unavailable.

## Model And Simscape Requirements

- Use Simscape/SATK paths for physical model construction. Do not replace physical circuits with pure Simulink signal-flow substitutes unless the boundary is explicit and educational.
- Model checks should report physical evidence: Simscape-like blocks, Solver Configuration, reference blocks, sensors, PS-Simulink converters, Simulink-PS converters, and logging/output blocks.
- Simulation summaries should record whether Simscape logging was attempted and whether a log such as `simlog` was captured.
- Focus and probe maps must point to real block paths that can be highlighted, cropped, measured, and explained.

## Agent Boundary

- Use the user-selected CLI command and configured SATK/MCP tools. Do not switch providers, use alternate execution paths, or create local substitute model builders.
- Do not introduce substitute routes for parsing, model generation, or teaching turns. If the selected path cannot run, report the blockage clearly.
- Keep generated teaching text plain by default. If math is necessary, use short balanced inline LaTeX only.
