function config = loadConfig()
%LOADCONFIG Resolve local CiTT configuration from MATLAB path and env vars.

matlabRoot = fileparts(fileparts(mfilename("fullpath")));
workDir = resolveWorkDir(matlabRoot);
settingsPath = fullfile(workDir, "citt_settings.json");
taskHistoryPath = fullfile(workDir, "citt_task_history.json");

loadLocalEnv(matlabRoot);
applyAppSettings(settingsPath);
loadShellEnvIfMissing(["GEMINI_API_KEY", "GEMINI_MODEL", "CITT_PARSER_BACKEND", "CITT_CODEX_CLI", "CITT_AGENT_BACKEND", "CITT_AGENT_COMMAND", ...
    "CITT_AGENT_MAX_ATTEMPTS", "CITT_AGENT_RETRY_DELAY_SECONDS", ...
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
config.SettingsPath = string(settingsPath);
config.TaskHistoryPath = string(taskHistoryPath);
config.GeminiApiKey = apiKey;
config.GeminiApiKeyName = apiKeyName;
config.GeminiModel = getenvOrDefault("GEMINI_MODEL", "gemini-3.5-flash");
config.ParserBackend = normalizeParserBackend(getenvOrDefault("CITT_PARSER_BACKEND", "codex"));
config.AgentBackend = normalizeAgentBackend(getenvOrDefault("CITT_AGENT_BACKEND", "codex"));
config.AgentCommand = string(getenv("CITT_AGENT_COMMAND"));
config.AgentMaxAttempts = getenvPositiveInteger("CITT_AGENT_MAX_ATTEMPTS", 4);
config.AgentRetryDelaySeconds = getenvNonnegativeNumber("CITT_AGENT_RETRY_DELAY_SECONDS", 20);
config.LastSpecPath = string(fullfile(workDir, "citt_last_circuit_spec.json"));
config.AgentTaskPath = string(fullfile(workDir, "citt_agent_task.md"));
config.GeneratedBuildScriptPath = string(fullfile(workDir, "citt_build_simscape_model.m"));
config.GeneratedModelPath = string(fullfile(workDir, "citt_generated_model.slx"));
config.ModelSnapshotPath = string(fullfile(workDir, "citt_model_snapshot.png"));
config.FocusMapPath = string(fullfile(workDir, "citt_focus_map.json"));
config.ProbeMapPath = string(fullfile(workDir, "citt_probe_map.json"));
config.AgentReportPath = string(fullfile(workDir, "citt_agent_report.md"));
config.TeachingPlanPath = string(fullfile(workDir, "citt_teaching_plan.json"));
config.ModelCheckReportPath = string(fullfile(workDir, "citt_model_check_report.md"));
config.SimulationSummaryPath = string(fullfile(workDir, "citt_simulation_summary.json"));
config.ProbeActionPlanPath = string(fullfile(workDir, "citt_probe_action_plan.json"));
config.LabDeltaReportPath = string(fullfile(workDir, "citt_lab_delta_report.json"));
config.LabErrorMarkdownPath = string(fullfile(workDir, "citt_lab_error_report.md"));
config.BodeReportPath = string(fullfile(workDir, "citt_bode_report.json"));
config.BodeMarkdownPath = string(fullfile(workDir, "citt_bode_report.md"));
config.BodePlotPath = string(fullfile(workDir, "citt_bode_plot.png"));
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

function workDir = resolveWorkDir(matlabRoot)
repoWorkDir = fullfile(matlabRoot, "work");
if ensureWritableDir(repoWorkDir)
    workDir = repoWorkDir;
    return
end

fallbackRoot = fullfile(prefdir, "CiTT");
fallbackWorkDir = fullfile(fallbackRoot, "work");
if ensureWritableDir(fallbackWorkDir)
    workDir = fallbackWorkDir;
    return
end

error("CiTT:WorkDirUnavailable", ...
    "Could not create a writable CiTT work directory under '%s' or '%s'.", ...
    repoWorkDir, fallbackWorkDir);
end

function ok = ensureWritableDir(pathValue)
ok = false;
try
    if exist(pathValue, "dir") ~= 7
        mkdir(pathValue);
    end
    probePath = fullfile(pathValue, ".citt_write_probe");
    fid = fopen(probePath, "w");
    if fid < 0
        return
    end
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, "ok\n");
    clear cleaner
    if exist(probePath, "file") == 2
        delete(probePath);
    end
    ok = true;
catch
    ok = false;
end
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

function applyAppSettings(path)
if exist(path, "file") ~= 2
    return
end

try
    settings = jsondecode(fileread(path));
catch
    return
end

setEnvFromField(settings, "gemini_api_key", "GEMINI_API_KEY");
setEnvFromField(settings, "gemini_model", "GEMINI_MODEL");
setEnvFromField(settings, "parser_backend", "CITT_PARSER_BACKEND");
setEnvFromField(settings, "agent_backend", "CITT_AGENT_BACKEND");
setEnvFromField(settings, "agent_command", "CITT_AGENT_COMMAND");
setEnvFromField(settings, "agent_max_attempts", "CITT_AGENT_MAX_ATTEMPTS");
setEnvFromField(settings, "agent_retry_delay_seconds", "CITT_AGENT_RETRY_DELAY_SECONDS");
end

function setEnvFromField(settings, fieldName, envName)
if ~isstruct(settings) || ~isfield(settings, fieldName)
    return
end

value = string(settings.(fieldName));
if strlength(strtrim(value)) == 0
    return
end
setenv(envName, char(value));
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

function backend = normalizeParserBackend(value)
backend = lower(strtrim(string(value)));
if backend == "cli"
    backend = "codex";
elseif backend == "deterministic"
    backend = "local";
end
if ~ismember(backend, ["codex", "gemini", "local"])
    backend = "codex";
end
end

function backend = normalizeAgentBackend(value)
backend = lower(strtrim(string(value)));
if backend == "cli"
    backend = "codex";
end
if ~ismember(backend, ["codex", "gemini"])
    backend = "codex";
end
end

function value = getenvPositiveInteger(name, defaultValue)
value = defaultValue;
rawValue = strtrim(string(getenv(name)));
if strlength(rawValue) == 0
    return
end

parsedValue = str2double(rawValue);
if isfinite(parsedValue) && parsedValue >= 1
    value = max(1, round(parsedValue));
end
end

function value = getenvNonnegativeNumber(name, defaultValue)
value = defaultValue;
rawValue = strtrim(string(getenv(name)));
if strlength(rawValue) == 0
    return
end

parsedValue = str2double(rawValue);
if isfinite(parsedValue) && parsedValue >= 0
    value = parsedValue;
end
end
