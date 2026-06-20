function result = runAgentTask(taskPath, options)
%RUNAGENTTASK Run the generated MATLAB/Simscape build for a prepared task.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(taskPath)
    taskPath = config.AgentTaskPath;
end
if nargin < 2 || isempty(options)
    options = struct();
end

taskPath = string(taskPath);
if exist(taskPath, "file") ~= 2
    error("CiTT:AgentTaskMissing", "Agent task file does not exist: %s", taskPath);
end

requireRealRunSetup();

specPath = config.LastSpecPath;
if isfield(options, "SpecPath")
    specPath = string(options.SpecPath);
end

buildResult = feval('citt.buildSimscapeModelFromSpec', specPath, struct( ...
    "ModelPath", config.GeneratedModelPath, ...
    "ScriptPath", config.GeneratedBuildScriptPath, ...
    "FocusMapPath", config.FocusMapPath, ...
    "ProbeMapPath", config.ProbeMapPath, ...
    "ReportPath", config.AgentReportPath, ...
    "WriteGeneratedScript", true, ...
    "RunGeneratedScript", true, ...
    "OpenModel", true));

result = baseResult("run " + config.GeneratedBuildScriptPath, config);
result.success = true;
result.exit_status = 0;
result.stdout = strjoin([
    buildResult.summary
    "Generated code: " + buildResult.generated_code_path
    "Model: " + buildResult.model_path
], newline);
result.produced_model_path = existingPath(buildResult.model_path);
result.produced_focus_map_path = existingPath(buildResult.focus_map_path);
result.produced_probe_map_path = existingPath(buildResult.probe_map_path);
result.generated_code_path = buildResult.generated_code_path;
result.agent_report_path = buildResult.agent_report_path;
result.build_result = buildResult;
end

function requireRealRunSetup()
setup = feval('citt.checkSetup');
missing = strings(0, 1);
if ~setup.simulink_available || ~setup.simulink_license
    missing(end + 1) = "Simulink";
end
if ~setup.simscape_available || ~setup.simscape_license
    missing(end + 1) = "Simscape";
end
if ~setup.satk_initialize_available
    missing(end + 1) = "Simulink Agentic Toolkit";
end
if ~setup.matlab_mcp_available
    missing(end + 1) = "MATLAB MCP Server";
end
if ~isempty(missing)
    error("CiTT:RealRunSetupMissing", ...
        "CiTT real-run mode requires: %s", strjoin(missing, ", "));
end
end

function result = baseResult(commandText, config)
result = struct();
result.success = false;
result.command = string(commandText);
result.exit_status = [];
result.stdout = "";
result.stderr = "";
result.produced_model_path = "";
result.produced_focus_map_path = "";
result.produced_probe_map_path = "";
result.expected_model_path = config.GeneratedModelPath;
result.expected_focus_map_path = config.FocusMapPath;
result.expected_probe_map_path = config.ProbeMapPath;
end

function path = existingPath(pathCandidate)
pathCandidate = string(pathCandidate);
if exist(pathCandidate, "file") == 2
    path = pathCandidate;
else
    path = "";
end
end
