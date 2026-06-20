function result = runAgentTask(taskPath, options)
%RUNAGENTTASK Run a prepared SATK task with an external agent CLI.

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

setup = requireRealRunSetup();
runner = selectAgentRunner(config, setup, taskPath, options);

switch runner.mode
    case "external_agent"
        if asyncEnabled(options)
            result = startExternalAgent(runner, config);
        else
            result = runExternalAgent(runner, config);
        end
    case "manual_agent"
        result = manualAgentResult(taskPath, config);
    case "local_fallback"
        result = runLocalFallback(config, options, runner.reason);
    otherwise
        error("CiTT:UnknownAgentMode", "Unknown agent runner mode: %s", runner.mode);
end
end

function result = startExternalAgent(runner, config)
artifactSnapshot = expectedArtifactSnapshot(config);
runtime = agentRuntimePaths(config);
clearAgentRuntimeFiles(runtime);
clearExternalGeneratedCode(config);
writeAgentRunScript(runtime, runner.command, config);

launchCommand = "/bin/zsh " + shellQuote(runtime.script_path) + " >/dev/null 2>&1 & echo $!";
launchResult = feval('citt.util.safeSystem', launchCommand);

result = baseResult(runner.command, config);
result.mode = "external_agent_pending";
result.agent_name = runner.name;
result.exit_status = [];
result.agent_attempts = 0;
result.agent_pid = strtrim(string(launchResult.stdout));
result.agent_stdout_path = runtime.stdout_path;
result.agent_stderr_path = runtime.stderr_path;
result.agent_status_path = runtime.status_path;
result.agent_exit_status_path = runtime.exit_status_path;
result.agent_attempt_path = runtime.attempt_path;
result.agent_script_path = runtime.script_path;
result.artifact_snapshot = artifactSnapshot;
result.summary = "External SATK agent started asynchronously. MATLAB is free for MCP/SATK tool calls.";
result.stdout = strjoin([
    result.summary
    "PID: " + emptyString(result.agent_pid, "unknown")
    "Stdout log: " + runtime.stdout_path
    "Stderr log: " + runtime.stderr_path
], newline);

if launchResult.status ~= 0 || strlength(result.agent_pid) == 0
    result.mode = "external_agent";
    result.success = false;
    result.exit_status = launchResult.status;
    result.stderr = appendLine(launchResult.stderr, "Could not launch external agent asynchronously.");
end
end

function result = runExternalAgent(runner, config)
artifactSnapshot = expectedArtifactSnapshot(config);
clearExternalGeneratedCode(config);
systemResult = runAgentCommandWithRetries(runner.command, config);

result = baseResult(runner.command, config);
result.mode = "external_agent";
result.agent_name = runner.name;
result.exit_status = systemResult.status;
result.stdout = systemResult.stdout;
result.stderr = systemResult.stderr;
result.agent_attempts = systemResult.attempts;

[result, missingArtifacts] = collectArtifacts(result, config, artifactSnapshot);
bypassedLocalFallback = localFallbackBypassDetected(result, config);
if result.exit_status == 0 && isempty(missingArtifacts) && ~bypassedLocalFallback
    result.success = true;
    result.summary = "External SATK agent completed and produced CiTT model artifacts.";
    result = openProducedModel(result);
else
    result.success = false;
    result.summary = "External SATK agent did not complete the CiTT build contract.";
    if result.exit_status ~= 0
        result.stderr = appendLine(result.stderr, "Agent CLI exited with status " + string(result.exit_status) + ".");
    end
    if ~isempty(missingArtifacts)
        result.stderr = appendLine(result.stderr, "Missing or stale required artifacts: " + strjoin(missingArtifacts, ", ") + ".");
    end
    if bypassedLocalFallback
        result.stderr = appendLine(result.stderr, "Agent bypassed SATK/model_edit by invoking or writing the CiTT local Simscape fallback.");
    end
end
end

function runtime = agentRuntimePaths(config)
runtime = struct();
runtime.stdout_path = string(fullfile(config.WorkDir, "citt_agent_stdout.log"));
runtime.stderr_path = string(fullfile(config.WorkDir, "citt_agent_stderr.log"));
runtime.status_path = string(fullfile(config.WorkDir, "citt_agent_status.txt"));
runtime.exit_status_path = string(fullfile(config.WorkDir, "citt_agent_exit_status.txt"));
runtime.attempt_path = string(fullfile(config.WorkDir, "citt_agent_attempt.txt"));
runtime.script_path = string(fullfile(config.WorkDir, "citt_run_agent.sh"));
end

function clearAgentRuntimeFiles(runtime)
fields = ["stdout_path", "stderr_path", "status_path", "exit_status_path", "attempt_path"];
for i = 1:numel(fields)
    path = runtime.(fields(i));
    if exist(path, "file") == 2
        delete(char(path));
    end
end
end

function clearExternalGeneratedCode(config)
if exist(config.GeneratedBuildScriptPath, "file") == 2
    delete(char(config.GeneratedBuildScriptPath));
end
end

function writeAgentRunScript(runtime, commandText, config)
lines = [
    "#!/bin/zsh"
    "stdout=" + shellQuote(runtime.stdout_path)
    "stderr=" + shellQuote(runtime.stderr_path)
    "status_file=" + shellQuote(runtime.status_path)
    "exit_file=" + shellQuote(runtime.exit_status_path)
    "attempt_file=" + shellQuote(runtime.attempt_path)
    "max_attempts=" + string(max(1, config.AgentMaxAttempts))
    "delay_seconds=" + string(max(0, config.AgentRetryDelaySeconds))
    ": > ""$stdout"""
    ": > ""$stderr"""
    "rm -f ""$exit_file"" ""$attempt_file"""
    "echo running > ""$status_file"""
    "attempt=1"
    "final_status=1"
    "while [ ""$attempt"" -le ""$max_attempts"" ]; do"
    "  echo ""===== External agent attempt ${attempt}/${max_attempts} ====="" >> ""$stdout"""
    "  " + string(commandText) + " >> ""$stdout"" 2>> ""$stderr"""
    "  final_status=$?"
    "  echo ""$attempt"" > ""$attempt_file"""
    "  if [ ""$final_status"" -eq 0 ]; then"
    "    break"
    "  fi"
    "  combined=$(cat ""$stdout"" ""$stderr"" 2>/dev/null | tr '[:upper:]' '[:lower:]')"
    "  if printf '%s' ""$combined"" | grep -Eq 'daily quota|terminalquotaerror|generate_requests_per_model_per_day|you have exhausted your daily quota'; then"
    "    break"
    "  fi"
    "  if [ ""$attempt"" -ge ""$max_attempts"" ]; then"
    "    break"
    "  fi"
    "  if printf '%s' ""$combined"" | grep -Eq '503|service unavailable|temporarily unavailable|internal server error|server error|deadline exceeded|connection reset|econnreset|etimedout|socket hang up'; then"
    "    echo ""CiTT retrying external agent after transient Gemini/API error in ${delay_seconds}s."" >> ""$stderr"""
    "    sleep ""$delay_seconds"""
    "    attempt=$((attempt + 1))"
    "    continue"
    "  fi"
    "  break"
    "done"
    "echo ""$final_status"" > ""$exit_file"""
    "if [ ""$final_status"" -eq 0 ]; then"
    "  echo completed > ""$status_file"""
    "else"
    "  echo failed > ""$status_file"""
    "fi"
    "exit ""$final_status"""
];
writeTextFile(runtime.script_path, strjoin(lines, newline) + newline);
try
    fileattrib(char(runtime.script_path), "+x");
catch
end
end

function systemResult = runAgentCommandWithRetries(commandText, config)
maxAttempts = max(1, config.AgentMaxAttempts);
delaySeconds = max(0, config.AgentRetryDelaySeconds);
combinedStdout = strings(0, 1);
combinedStderr = strings(0, 1);

for attempt = 1:maxAttempts
    attemptResult = feval('citt.util.safeSystem', commandText);
    attemptHeader = "===== External agent attempt " + string(attempt) + "/" + string(maxAttempts) + " =====";
    combinedStdout(end + 1) = appendBlock(attemptHeader, attemptResult.stdout);
    if strlength(strtrim(string(attemptResult.stderr))) > 0
        combinedStderr(end + 1) = appendBlock(attemptHeader, attemptResult.stderr);
    end

    shouldRetry = attemptResult.status ~= 0 && attempt < maxAttempts && isRetryableAgentFailure(attemptResult);
    if ~shouldRetry
        systemResult = attemptResult;
        systemResult.stdout = strjoin(combinedStdout, newline);
        systemResult.stderr = strjoin(combinedStderr, newline);
        systemResult.attempts = attempt;
        return
    end

    retryNote = "CiTT retrying external agent after transient Gemini/API error in " + ...
        string(delaySeconds) + "s.";
    combinedStderr(end + 1) = retryNote;
    if delaySeconds > 0
        pause(delaySeconds);
    end
end

systemResult = attemptResult;
systemResult.stdout = strjoin(combinedStdout, newline);
systemResult.stderr = strjoin(combinedStderr, newline);
systemResult.attempts = maxAttempts;
end

function retryable = isRetryableAgentFailure(systemResult)
text = lower(string(systemResult.stdout) + newline + string(systemResult.stderr));

dailyQuotaFailure = contains(text, "daily quota") || ...
    contains(text, "terminalquotaerror") || ...
    contains(text, "generate_requests_per_model_per_day") || ...
    contains(text, "you have exhausted your daily quota");
if dailyQuotaFailure
    retryable = false;
    return
end

retryPatterns = [
    "503"
    "service unavailable"
    "temporarily unavailable"
    "internal server error"
    "server error"
    "deadline exceeded"
    "connection reset"
    "econnreset"
    "etimedout"
    "socket hang up"
];
retryable = any(contains(text, retryPatterns));
end

function text = appendBlock(header, body)
body = string(body);
if strlength(strtrim(body)) == 0
    text = header;
else
    text = header + newline + body;
end
end

function result = manualAgentResult(taskPath, config)
result = baseResult("manual agent: " + taskPath, config);
result.mode = "manual_agent";
result.agent_name = "manual";
result.summary = "No configured Gemini/Codex agent CLI was found.";
result.stdout = manualInstructions(taskPath, config);

try
    edit(char(taskPath));
catch editError
    result.stderr = "Could not open task markdown automatically: " + string(editError.message);
end
end

function result = runLocalFallback(config, options, reason)
specPath = config.LastSpecPath;
if isfield(options, "SpecPath")
    specPath = string(options.SpecPath);
end

buildResult = feval('citt.buildLocalSimscapeFallback', specPath, struct( ...
    "ModelPath", config.GeneratedModelPath, ...
    "ScriptPath", config.GeneratedBuildScriptPath, ...
    "FocusMapPath", config.FocusMapPath, ...
    "ProbeMapPath", config.ProbeMapPath, ...
    "ReportPath", config.AgentReportPath, ...
    "WriteGeneratedScript", true, ...
    "RunGeneratedScript", true, ...
    "OpenModel", true));

result = baseResult("local fallback: citt.buildLocalSimscapeFallback", config);
result.mode = "local_fallback";
result.agent_name = "local_simscape_fallback";
result.success = true;
result.exit_status = 0;
result.summary = "Agent build unavailable. Running local Simscape fallback.";
result.stdout = strjoin([
    result.summary
    "Reason: " + reason
    buildResult.summary
    "Generated fallback code: " + buildResult.generated_code_path
    "Model: " + buildResult.model_path
], newline);
result.produced_model_path = existingPath(buildResult.model_path);
result.produced_focus_map_path = existingPath(buildResult.focus_map_path);
result.produced_probe_map_path = existingPath(buildResult.probe_map_path);
result.generated_code_path = buildResult.generated_code_path;
result.agent_report_path = existingPath(buildResult.agent_report_path);
result.build_result = buildResult;
end

function setup = requireRealRunSetup()
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
        "CiTT agent mode requires: %s", strjoin(missing, ", "));
end
end

function runner = selectAgentRunner(config, setup, taskPath, options)
runner = struct("mode", "", "name", "", "command", "", "reason", "");

if strlength(strtrim(config.AgentCommand)) > 0
    runner.mode = "external_agent";
    runner.name = "CITT_AGENT_COMMAND";
    runner.command = commandFromTemplate(config.AgentCommand, taskPath);
    return
end

gemini = cliPath(setup, "gemini");
if strlength(gemini) > 0
    runner.mode = "external_agent";
    runner.name = "gemini";
    runner.command = geminiCommand(gemini, config, taskPath);
    return
end

codex = cliPath(setup, "codex");
if strlength(codex) > 0
    runner.mode = "external_agent";
    runner.name = "codex";
    runner.command = shellQuote(codex) + " exec " + taskContentArgument(taskPath);
    return
end

if localFallbackEnabled(options)
    runner.mode = "local_fallback";
    runner.name = "local_simscape_fallback";
    runner.command = "citt.buildLocalSimscapeFallback";
    runner.reason = "No configured agent CLI was found and local fallback was explicitly enabled.";
    return
end

runner.mode = "manual_agent";
runner.name = "manual";
runner.command = "manual agent: " + taskPath;
end

function command = commandFromTemplate(commandTemplate, taskPath)
command = string(commandTemplate);
quotedTaskPath = shellQuote(taskPath);
if contains(command, "{taskPath}")
    command = replace(command, "{taskPath}", quotedTaskPath);
elseif contains(command, "{task}")
    command = replace(command, "{task}", quotedTaskPath);
else
    command = strtrim(command) + " " + quotedTaskPath;
end
end

function command = geminiCommand(geminiPath, config, taskPath)
command = shellQuote(geminiPath) + " --approval-mode yolo --allowed-mcp-server-names matlab";
if strlength(strtrim(config.GeminiModel)) > 0
    command = command + " --model " + shellQuote(config.GeminiModel);
end
command = command + " --prompt " + taskContentArgument(taskPath);
end

function argument = taskContentArgument(taskPath)
if ispc
    argument = shellQuote(fileread(char(taskPath)));
else
    argument = """" + "$(cat " + shellQuote(taskPath) + ")" + """";
end
end

function path = cliPath(setup, name)
path = "";
for i = 1:numel(setup.agent_clis)
    if setup.agent_clis(i).name == string(name) && setup.agent_clis(i).available
        path = string(setup.agent_clis(i).path);
        return
    end
end
end

function enabled = localFallbackEnabled(options)
enabled = false;
if isfield(options, "UseLocalFallback")
    enabled = logical(options.UseLocalFallback);
end
enabled = enabled || envFlag("CITT_USE_LOCAL_SIMSCAPE_FALLBACK") || ...
    envFlag("CITT_LOCAL_SIMSCAPE_FALLBACK");
end

function enabled = asyncEnabled(options)
enabled = false;
if isfield(options, "Async")
    enabled = logical(options.Async);
end
enabled = enabled || envFlag("CITT_AGENT_ASYNC");
end

function enabled = envFlag(name)
value = lower(strtrim(string(getenv(char(name)))));
enabled = any(value == ["1", "true", "yes", "on"]);
end

function result = baseResult(commandText, config)
result = struct();
result.success = false;
result.mode = "";
result.agent_name = "";
result.summary = "";
result.command = string(commandText);
result.exit_status = [];
result.stdout = "";
result.stderr = "";
result.agent_attempts = 0;
result.produced_model_path = "";
result.produced_focus_map_path = "";
result.produced_probe_map_path = "";
result.generated_code_path = "";
result.agent_report_path = "";
result.expected_model_path = config.GeneratedModelPath;
result.expected_focus_map_path = config.FocusMapPath;
result.expected_probe_map_path = config.ProbeMapPath;
result.expected_report_path = config.AgentReportPath;
end

function snapshot = expectedArtifactSnapshot(config)
snapshot = struct();
snapshot.model = fileStamp(config.GeneratedModelPath);
snapshot.focus_map = fileStamp(config.FocusMapPath);
snapshot.probe_map = fileStamp(config.ProbeMapPath);
snapshot.report = fileStamp(config.AgentReportPath);
end

function [result, missingArtifacts] = collectArtifacts(result, config, snapshot)
result.produced_model_path = existingPath(config.GeneratedModelPath);
result.produced_focus_map_path = existingPath(config.FocusMapPath);
result.produced_probe_map_path = existingPath(config.ProbeMapPath);
result.generated_code_path = existingPath(config.GeneratedBuildScriptPath);
result.agent_report_path = existingPath(config.AgentReportPath);

missingArtifacts = strings(0, 1);
if strlength(result.produced_model_path) == 0 || ~artifactIsFresh(config.GeneratedModelPath, snapshot.model)
    missingArtifacts(end + 1) = "model " + config.GeneratedModelPath;
end
if strlength(result.produced_focus_map_path) == 0 || ~artifactIsFresh(config.FocusMapPath, snapshot.focus_map)
    missingArtifacts(end + 1) = "focus map " + config.FocusMapPath;
end
if strlength(result.produced_probe_map_path) == 0 || ~artifactIsFresh(config.ProbeMapPath, snapshot.probe_map)
    missingArtifacts(end + 1) = "probe map " + config.ProbeMapPath;
end
if strlength(result.agent_report_path) == 0 || ~artifactIsFresh(config.AgentReportPath, snapshot.report)
    missingArtifacts(end + 1) = "agent report " + config.AgentReportPath;
end
end

function fresh = artifactIsFresh(path, previousStamp)
currentStamp = fileStamp(path);
if isnan(currentStamp)
    fresh = false;
elseif isnan(previousStamp)
    fresh = true;
else
    fresh = currentStamp ~= previousStamp;
end
end

function stamp = fileStamp(path)
info = dir(char(string(path)));
if isempty(info)
    stamp = NaN;
else
    stamp = info(1).datenum;
end
end

function result = openProducedModel(result)
try
    open_system(char(result.produced_model_path));
catch openError
    result.stderr = appendLine(result.stderr, "Model artifact exists but could not be opened: " + string(openError.message));
end
end

function path = existingPath(pathCandidate)
pathCandidate = string(pathCandidate);
if exist(pathCandidate, "file") == 2
    path = pathCandidate;
else
    path = "";
end
end

function detected = localFallbackBypassDetected(result, config)
text = string(result.stdout) + newline + string(result.stderr);
if exist(config.GeneratedBuildScriptPath, "file") == 2
    text = text + newline + readText(config.GeneratedBuildScriptPath);
end
if exist(config.AgentReportPath, "file") == 2
    text = text + newline + readText(config.AgentReportPath);
end

patterns = [
    "Generated by CiTT local fallback"
    "citt.buildLocalSimscapeFallback"
    "buildLocalSimscapeFallback"
    "citt.buildSimscapeModelFromSpec"
    "buildSimscapeModelFromSpec"
];
detected = any(contains(text, patterns));
end

function text = readText(path)
try
    text = string(fileread(char(path)));
catch
    text = "";
end
end

function text = manualInstructions(taskPath, config)
text = strjoin([
    "No configured Gemini/Codex agent CLI was found."
    "CiTT opened the generated SATK task markdown."
    ""
    "Manual agent mode:"
    "1. Paste this task into a SATK-configured agent with MATLAB MCP tools enabled."
    "2. The agent must use SATK tools such as model_read, model_edit, model_check, model_query_params, and model_resolve_params."
    "3. The agent must save the expected CiTT artifacts:"
    "   Model: " + config.GeneratedModelPath
    "   Focus map: " + config.FocusMapPath
    "   Probe map: " + config.ProbeMapPath
    "   Report: " + config.AgentReportPath
    ""
    "Set CITT_AGENT_COMMAND to automate this, for example: your-agent-command {taskPath}"
    "For demo-only emergency use, set CITT_USE_LOCAL_SIMSCAPE_FALLBACK=1 to run the local Simscape fallback."
    ""
    "Task: " + taskPath
], newline);
end

function text = appendLine(text, line)
line = string(line);
if strlength(strtrim(string(text))) == 0
    text = line;
else
    text = string(text) + newline + line;
end
end

function text = emptyString(value, defaultText)
if strlength(strtrim(string(value))) == 0
    text = string(defaultText);
else
    text = string(value);
end
end

function writeTextFile(path, text)
fid = fopen(char(path), "w");
if fid < 0
    error("CiTT:FileWriteFailed", "Could not write file: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
delete(cleanup);
end

function quoted = shellQuote(value)
raw = char(string(value));
if ispc
    raw = strrep(raw, '"', '\"');
    quoted = """" + string(raw) + """";
else
    singleQuote = char(39);
    doubleQuote = char(34);
    replacement = [singleQuote doubleQuote singleQuote doubleQuote singleQuote];
    raw = strrep(raw, singleQuote, replacement);
    quoted = string([singleQuote raw singleQuote]);
end
end
