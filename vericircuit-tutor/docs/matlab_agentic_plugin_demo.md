# MATLAB Agentic Plugin Demo

CiTT is demoed from MATLAB, not the web app.

1. Install Simulink Agentic Toolkit.
2. In MATLAB, run `setupAgenticToolkit("install")` if that helper is available, then run `satk_initialize`.
3. Set `GEMINI_API_KEY` in the environment or in `vericircuit-tutor/matlab/.env`.
4. Configure an SATK-enabled agent CLI: set `CITT_AGENT_COMMAND`, install Gemini CLI, or install Codex CLI.
5. Add the plugin folder to the MATLAB path:

   ```matlab
   addpath("vericircuit-tutor/matlab")
   ```

6. Launch CiTT:

   ```matlab
   citt
   ```

7. In the Read Circuit tab, drag in a circuit image or browse for one, then optionally enter a short circuit prompt.
8. Click Read with Gemini. CiTT writes `matlab/work/citt_last_circuit_spec.json` and shows a readable summary plus the next step.
9. In Build Model, click Prepare Build. CiTT writes `matlab/work/citt_agent_task.md`.
10. Click Build Model. CiTT passes `matlab/work/citt_agent_task.md` to the configured agent CLI. The agent uses SATK/MCP tools to build/check the Simscape model, save `matlab/work/citt_generated_model.slx`, and open it in Simulink.
11. The agent also writes focus and probe maps plus `matlab/work/citt_agent_report.md`. If no CLI is available, CiTT opens the task for manual-agent mode; the local Simscape fallback is opt-in only with `CITT_USE_LOCAL_SIMSCAPE_FALLBACK=1`.
12. In Model Lab, open/check/simulate the generated model.
13. In Teach, start Socratic teaching, then highlight or zoom the current focus point.
14. In Probe & Compare, add a guided probe and compare a lab CSV against hand/simulation values.

Live model generation depends on MATLAB, Simulink, Simscape, SATK, and MATLAB MCP. Symbolic or missing values are kept as model parameters, so drawing can proceed for teaching diagrams where values are intentionally omitted. CiTT validates required outputs and fails if the expected model artifacts do not exist.
