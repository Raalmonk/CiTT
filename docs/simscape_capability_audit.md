# CiTT Simscape Capability Audit

Date: 2026-06-29

This audit asks whether CiTT is using Simscape as a physical modeling environment, not merely as a diagram renderer.

## Current Answer

CiTT is using several important Simscape advantages already: SATK/MCP model construction, Simscape-first build prompts, physical component requirements, model checks, focus/probe maps, sensor-based measurements, and simulation-backed teaching. It is not yet using those advantages as a complete, testable contract. The gaps are mostly in verification and agent guidance: we need to assert physical-network structure, units, solver/reference infrastructure, sensor logging, and student-safe text output every time.

## Capability Checklist

| Capability | Why Simscape Helps | Current Use | Gap | Optimization |
| --- | --- | --- | --- | --- |
| Physical network topology | Conserves energy/charge and exposes node/reference mistakes. | Agent task asks for Simscape-first physical connections. | No automatic audit that generated models actually contain physical/Simscape blocks. | Add model-check Simscape artifact audit for physical blocks, solver config, reference blocks, sensors, converters, and logging. |
| Solver Configuration and references | Simscape models require explicit physical-network infrastructure. | Agent prompt requires Electrical Reference and Solver Configuration. | Missing infrastructure can slip through as a generic update/check failure. | Report dedicated audit warnings for missing Solver Configuration and Electrical Reference. |
| SATK model tools | `model_edit`, `model_read`, `model_query_params`, and `model_resolve_params` keep edits grounded in the model. | Build tasks name the tools and forbid local builders. | Local SATK guidance was not fully vendored into the repo/task. | Clone SATK agent instructions locally and embed the repo-local instructions in every build task. |
| Units and parameter resolution | Simscape parameters carry engineering units and symbolic workspace values. | Teaching plan now lists component values and generated defaults. | Build agent was not explicitly required to verify unresolved symbols with query/resolve tools. | Add explicit query/resolve requirement to build task and agent addendum. |
| Sensor and probe logging | Simscape Voltage/Current Sensors plus PS-Simulink converters produce falsifiable evidence. | Probe map and `addProbe` support sensor logging chains. | Model checks did not score whether requested outputs are logged. | Audit sensors, PS-Simulink converters, To Workspace blocks, scopes, and outports. |
| Simulation and Simscape logging | Simscape simulation can expose settling, saturation, and unit mistakes. | `runSimulation` executes the generated model and records output variables. | Simscape logging was not explicitly enabled or reported. | Try to enable Simscape logging when the model supports it, and record status in the simulation summary. |
| Cross-domain biomedical modeling | Simscape can combine electrical, controlled sources, transport lags, and mixed-signal wrappers. | Build readiness now allows PK/mass-transfer/ADC teaching simplifications. | Agent prompt needs to distinguish physical path from acceptable educational abstractions. | Add CiTT-specific SATK instructions for physical path first, with controlled Simulink wrappers only at explicit boundaries. |
| Student-facing teachability and LaTeX safety | Simscape evidence should be readable and model-linked; bad formulas must not break UI. | Learning facts include values; LaTeX renderer now has guards. | Agent/focus-map text could still emit malformed LaTeX. | Add agent instruction: prefer plain text in focus/probe maps; only simple balanced LaTeX if necessary. |

## Implementation Status

- Added repo-local SATK instruction bundle under `matlab/resources/agent_instructions/simulink_agentic_toolkit/`.
- Added CiTT-specific agent addendum with Simscape-first, no external skill reads, no alternate CLI, and LaTeX-safe text rules.
- Updated agent task generation to embed repo-local SATK and CiTT instructions.
- Added Simscape artifact audit to model check output.
- Added best-effort Simscape logging enablement to simulation output.
- Kept LaTeX preview guarded: malformed or too-complex LaTeX degrades to plain text.

## Verification

1. Regenerated an agent task and asserted the local SATK/CiTT instructions, Simscape utilization contract, parameter-query tools, converter requirements, and LaTeX-safe text rules are embedded.
2. Ran model-check tests and verified `simscape_audit` exists even for non-Simscape toy models, with an explicit warning when no physical path is present.
3. Ran the current generated mixed-domain model check/simulation. The audit found 12 Simscape-like blocks, 1 Solver Configuration block, 1 reference block, 6 sensor blocks, 2 PS-Simulink converters, 1 Simulink-PS converter, and 10 logging/output blocks with no warnings.
4. Verified simulation summary records Simscape logging status and captured `simlog`.
5. Verified malformed or overly nested LaTeX degrades to plain text in both the learning UI and the standalone preview UI.
6. Real MATLAB UI example testing still needs an accessible MATLAB UI window before continuing; automated checks do not replace the user-visible UI run.
