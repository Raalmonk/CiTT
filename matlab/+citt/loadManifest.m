function manifest = loadManifest()
%LOADMANIFEST Compatibility manifest for older MATLAB helper calls.
% New CiTT demos should use the MATLAB launcher and generated SATK artifacts.

config = feval('citt.loadConfig');
manifest = struct();
manifest.product_name = "CiTT MATLAB Plugin";
manifest.version = "2.0.0";
manifest.positioning = "MATLAB shell around Gemini, SATK-enabled external agents, Simscape, and Simulink Agentic Toolkit.";
manifest.main_entrypoint = "citt";
manifest.tabs = ["Read Circuit", "Build Model", "Model Lab", "Teach", "Probe & Compare"];
manifest.work_dir = config.WorkDir;
manifest.required_runtime = [
    "GEMINI_API_KEY"
    "Simulink"
    "Simscape"
    "Simulink Agentic Toolkit"
    "MATLAB MCP Server"
    "CITT_AGENT_COMMAND or Gemini/Codex CLI"
];
manifest.generated_outputs = struct( ...
    "circuit_spec", config.LastSpecPath, ...
    "agent_task", config.AgentTaskPath, ...
    "build_script", config.GeneratedBuildScriptPath, ...
    "model", config.GeneratedModelPath, ...
    "focus_map", config.FocusMapPath, ...
    "probe_map", config.ProbeMapPath ...
);
end
