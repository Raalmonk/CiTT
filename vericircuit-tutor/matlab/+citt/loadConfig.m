function config = loadConfig()
%LOADCONFIG Resolve local CiTT configuration from MATLAB path and env vars.

matlabRoot = fileparts(fileparts(mfilename("fullpath")));
workDir = fullfile(matlabRoot, "work");
if exist(workDir, "dir") ~= 7
    mkdir(workDir);
end

loadLocalEnv(matlabRoot);
loadShellEnvIfMissing(["GEMINI_API_KEY", "GEMINI_MODEL", "CITT_AGENT_COMMAND", ...
    "CITT_USE_LOCAL_SIMSCAPE_FALLBACK", "CITT_LOCAL_SIMSCAPE_FALLBACK"]);
agenticToolkit = discoverAgenticToolkit();

apiKey = string(getenv("GEMINI_API_KEY"));
apiKeyName = "GEMINI_API_KEY";

config = struct();
config.MatlabRoot = string(matlabRoot);
config.WorkDir = string(workDir);
config.AgenticToolkitRoot = agenticToolkit.root;
config.SatkInstallPath = agenticToolkit.simulink_path;
config.MatlabAgenticToolkitPath = agenticToolkit.matlab_path;
config.MatlabMcpServerPath = agenticToolkit.mcp_server_path;
config.GeminiApiKey = apiKey;
config.GeminiApiKeyName = apiKeyName;
config.GeminiModel = getenvOrDefault("GEMINI_MODEL", "gemini-3.1-pro-preview");
config.AgentCommand = string(getenv("CITT_AGENT_COMMAND"));
config.LastSpecPath = string(fullfile(workDir, "citt_last_circuit_spec.json"));
config.AgentTaskPath = string(fullfile(workDir, "citt_agent_task.md"));
config.GeneratedBuildScriptPath = string(fullfile(workDir, "citt_build_simscape_model.m"));
config.GeneratedModelPath = string(fullfile(workDir, "citt_generated_model.slx"));
config.FocusMapPath = string(fullfile(workDir, "citt_focus_map.json"));
config.ProbeMapPath = string(fullfile(workDir, "citt_probe_map.json"));
config.AgentReportPath = string(fullfile(workDir, "citt_agent_report.md"));
config.TeachingPlanPath = string(fullfile(workDir, "citt_teaching_plan.json"));
config.ModelCheckReportPath = string(fullfile(workDir, "citt_model_check_report.md"));
config.SimulationSummaryPath = string(fullfile(workDir, "citt_simulation_summary.json"));
config.ProbeActionPlanPath = string(fullfile(workDir, "citt_probe_action_plan.json"));
config.LabDeltaReportPath = string(fullfile(workDir, "citt_lab_delta_report.json"));
config.EvidencePackPath = string(fullfile(workDir, "citt_evidence_pack.md"));
config.RequirementReportPath = string(fullfile(workDir, "citt_requirement_report.json"));
config.RequirementReportMarkdownPath = string(fullfile(workDir, "citt_requirement_report.md"));
config.ParameterSweepReportPath = string(fullfile(workDir, "citt_parameter_sweep_report.json"));
config.ParameterSweepMarkdownPath = string(fullfile(workDir, "citt_parameter_sweep_report.md"));
config.FaultInjectionReportPath = string(fullfile(workDir, "citt_fault_injection_report.json"));
config.FaultInjectionMarkdownPath = string(fullfile(workDir, "citt_fault_injection_report.md"));
config.ExplainabilityMapPath = string(fullfile(workDir, "citt_explainability_map.json"));
config.ExplainabilityMarkdownPath = string(fullfile(workDir, "citt_explainability_map.md"));
config.AssessmentReportPath = string(fullfile(workDir, "citt_learning_assessment_report.json"));
config.AssessmentMarkdownPath = string(fullfile(workDir, "citt_learning_assessment_report.md"));
config.EconomicsPlanPath = string(fullfile(workDir, "citt_economics_plan.json"));
config.EconomicsMarkdownPath = string(fullfile(workDir, "citt_economics_plan.md"));
config.ScopeGuardrailPath = string(fullfile(workDir, "citt_scope_guardrail.json"));
config.ScopeGuardrailMarkdownPath = string(fullfile(workDir, "citt_scope_guardrail.md"));
end

function toolkit = discoverAgenticToolkit()
homeDir = string(getenv("HOME"));
toolkit = struct();
toolkit.root = "";
toolkit.simulink_path = "";
toolkit.matlab_path = "";
toolkit.mcp_server_path = "";

if strlength(homeDir) == 0
    return
end

root = string(fullfile(homeDir, ".matlab", "agentic-toolkits"));
simulinkPath = string(fullfile(root, "simulink"));
matlabPath = string(fullfile(root, "matlab"));
mcpServerPath = string(fullfile(root, "bin", "matlab-mcp-server"));

if exist(root, "dir") == 7
    toolkit.root = root;
end
if exist(simulinkPath, "dir") == 7
    toolkit.simulink_path = simulinkPath;
    addPathIfNeeded(simulinkPath);
end
if exist(matlabPath, "dir") == 7
    toolkit.matlab_path = matlabPath;
    addPathIfNeeded(matlabPath);
end
if exist(mcpServerPath, "file") == 2
    toolkit.mcp_server_path = mcpServerPath;
end
try
    rehash;
catch
end
end

function addPathIfNeeded(pathValue)
if strlength(string(pathValue)) == 0
    return
end
currentPath = string(path);
parts = split(currentPath, pathsep);
if ~any(parts == string(pathValue))
    addpath(char(pathValue), "-end");
end
end

function loadShellEnvIfMissing(names)
for i = 1:numel(names)
    name = string(names(i));
    if strlength(string(getenv(char(name)))) > 0
        continue
    end

    value = shellGetenv(name);
    if strlength(value) == 0
        value = launchctlGetenv(name);
    end
    if strlength(value) > 0
        setenv(char(name), char(value));
    end
end
end

function value = shellGetenv(name)
value = "";
if ~ismac() && ~isunix()
    return
end
command = sprintf('/bin/zsh -lc ''printf %%s "$%s"''', char(name));
try
    [status, output] = system(command);
    if status == 0
        value = strtrim(string(output));
    end
catch
    value = "";
end
end

function value = launchctlGetenv(name)
value = "";
if ~ismac()
    return
end
command = sprintf('launchctl getenv %s', char(name));
try
    [status, output] = system(command);
    if status == 0
        value = strtrim(string(output));
    end
catch
    value = "";
end
end

function loadLocalEnv(matlabRoot)
repoRoot = fileparts(matlabRoot);
candidatePaths = [
    string(fullfile(matlabRoot, ".env"))
    string(fullfile(repoRoot, ".env"))
    string(fullfile(pwd, ".env"))
];

homeDir = string(getenv("HOME"));
if strlength(homeDir) > 0
    candidatePaths(end + 1) = string(fullfile(homeDir, ".citt.env"));
end

for i = 1:numel(candidatePaths)
    path = candidatePaths(i);
    if exist(path, "file") == 2
        applyEnvFile(path);
    end
end
end

function applyEnvFile(path)
try
    lines = splitlines(string(fileread(path)));
catch
    return
end

for i = 1:numel(lines)
    line = strtrim(lines(i));
    if strlength(line) == 0 || startsWith(line, "#")
        continue
    end
    if startsWith(line, "export ")
        line = strtrim(extractAfter(line, strlength("export ")));
    end

    rawLine = char(line);
    equalsIndex = strfind(rawLine, "=");
    if isempty(equalsIndex)
        continue
    end
    equalsIndex = equalsIndex(1);

    name = strtrim(string(rawLine(1:equalsIndex - 1)));
    value = stripQuotes(strtrim(string(rawLine(equalsIndex + 1:end))));
    if strlength(name) == 0
        continue
    end

    if strlength(string(getenv(char(name)))) == 0
        setenv(char(name), char(value));
    end
end
end

function value = stripQuotes(value)
rawValue = char(value);
if numel(rawValue) >= 2
    firstChar = rawValue(1);
    lastChar = rawValue(end);
    if (firstChar == '"' && lastChar == '"') || (firstChar == '''' && lastChar == '''')
        value = string(rawValue(2:end - 1));
    end
end
end

function value = getenvOrDefault(name, defaultValue)
value = string(getenv(name));
if strlength(value) == 0
    value = string(defaultValue);
end
end
