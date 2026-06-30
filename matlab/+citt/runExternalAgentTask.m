function result = runExternalAgentTask(taskPath, options)
%RUNEXTERNALAGENTTASK Run a prepared non-build SATK task with the agent CLI.

config = feval('citt.loadConfig');
feval('citt.ensureAgenticToolkit', config);
if nargin < 1 || isempty(taskPath)
    error("CiTT:AgentTaskMissing", "An agent task path is required.");
end
if nargin < 2 || isempty(options)
    options = struct();
end

taskPath = string(taskPath);
if exist(taskPath, "file") ~= 2
    error("CiTT:AgentTaskMissing", "Agent task file does not exist: %s", taskPath);
end

if optionFlag(options, "RequireRealRunSetup", true)
    requireRealRunSetup();
end

purpose = matlab.lang.makeValidName(char(optionString(options, "Purpose", "external")));
expectedArtifacts = optionStringArray(options, "ExpectedArtifacts", strings(0, 1));
runner = selectAgentRunner(config, taskPath);
runtime = agentRuntimePaths(config, purpose);
snapshot = artifactSnapshot(expectedArtifacts);

if optionFlag(options, "Async", false)
    result = startExternalAgent(runner, runtime, config, purpose, expectedArtifacts, snapshot);
else
    result = runExternalAgent(runner, runtime, config, purpose, expectedArtifacts, snapshot);
end
end

function result = startExternalAgent(runner, runtime, config, purpose, expectedArtifacts, snapshot)
clearAgentRuntimeFiles(runtime);
writeAgentRunScript(runtime, runner.command, config);

launchCommand = "/bin/zsh " + shellQuote(runtime.script_path) + " >/dev/null 2>&1 & echo $!";
launchResult = feval('citt.util.safeSystem', launchCommand);

result = baseResult(runner.command, purpose, expectedArtifacts, snapshot);
result.mode = "external_agent_pending";
result.agent_name = runner.name;
result.agent_pid = strtrim(string(launchResult.stdout));
result.agent_stdout_path = runtime.stdout_path;
result.agent_stderr_path = runtime.stderr_path;
result.agent_status_path = runtime.status_path;
result.agent_exit_status_path = runtime.exit_status_path;
result.agent_attempt_path = runtime.attempt_path;
result.agent_script_path = runtime.script_path;
result.summary = "External SATK agent started asynchronously for " + string(purpose) + ".";
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

function result = runExternalAgent(runner, runtime, config, purpose, expectedArtifacts, snapshot)
clearAgentRuntimeFiles(runtime);
systemResult = runAgentCommandWithRetries(runner.command, config);

result = baseResult(runner.command, purpose, expectedArtifacts, snapshot);
result.mode = "external_agent";
result.agent_name = runner.name;
result.exit_status = systemResult.status;
result.stdout = systemResult.stdout;
result.stderr = systemResult.stderr;
result.agent_attempts = systemResult.attempts;
result.agent_stdout_path = runtime.stdout_path;
result.agent_stderr_path = runtime.stderr_path;

waitForArtifacts(expectedArtifacts, snapshot, 10);
[produced, missing] = collectArtifacts(expectedArtifacts, snapshot);
result.produced_artifacts = produced;
if result.exit_status == 0 && isempty(missing)
    result.success = true;
    result.summary = "External SATK agent completed " + string(purpose) + " and produced expected artifacts.";
else
    result.success = false;
    result.summary = "External SATK agent did not complete the " + string(purpose) + " contract.";
    if result.exit_status ~= 0
        result.stderr = appendLine(result.stderr, "Agent CLI exited with status " + string(result.exit_status) + ".");
    end
    if ~isempty(missing)
        result.stderr = appendLine(result.stderr, "Missing or stale expected artifacts: " + strjoin(missing, ", ") + ".");
    end
end
end

function runtime = agentRuntimePaths(config, purpose)
prefix = "citt_" + string(purpose) + "_agent";
runtime = struct();
runtime.stdout_path = string(fullfile(config.WorkDir, prefix + "_stdout.log"));
runtime.stderr_path = string(fullfile(config.WorkDir, prefix + "_stderr.log"));
runtime.status_path = string(fullfile(config.WorkDir, prefix + "_status.txt"));
runtime.exit_status_path = string(fullfile(config.WorkDir, prefix + "_exit_status.txt"));
runtime.attempt_path = string(fullfile(config.WorkDir, prefix + "_attempt.txt"));
runtime.script_path = string(fullfile(config.WorkDir, "citt_run_" + string(purpose) + "_agent.sh"));
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
    "    echo ""CiTT retrying external agent after transient service/API error in ${delay_seconds}s."" >> ""$stderr"""
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
writeText(runtime.script_path, strjoin(lines, newline) + newline);
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

    combinedStderr(end + 1) = "CiTT retrying external agent after transient service/API error in " + ...
        string(delaySeconds) + "s.";
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
if contains(text, "daily quota") || contains(text, "terminalquotaerror") || ...
        contains(text, "generate_requests_per_model_per_day") || ...
        contains(text, "you have exhausted your daily quota")
    retryable = false;
    return
end
retryable = any(contains(text, [
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
]));
end

function setup = requireRealRunSetup()
setup = feval('citt.checkSetup');
missing = strings(0, 1);
if ~setup.simulink_available || ~setup.simulink_license
    missing(end + 1) = "Simulink";
end
if ~setup.satk_initialize_available
    missing(end + 1) = "Simulink Agentic Toolkit";
end
if ~setup.matlab_mcp_available
    missing(end + 1) = "MATLAB MCP Server";
end
if ~isempty(missing)
    error("CiTT:RealRunSetupMissing", "CiTT external SATK tasks require: %s", strjoin(missing, ", "));
end
end

function runner = selectAgentRunner(config, taskPath)
runner = struct("mode", "", "name", "", "command", "");
if strlength(strtrim(config.AgentCommand)) > 0
    runner.mode = "external_agent";
    runner.name = configuredAgentName(config.AgentCommand);
    runner.command = commandFromTemplate(config.AgentCommand, taskPath);
    return
end
error("CiTT:AgentCliMissing", ...
    "No selected CLI command is configured. Set CITT_AGENT_COMMAND or save a CLI template in Settings.");
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

function name = configuredAgentName(commandTemplate)
lowerCommand = lower(string(commandTemplate));
if contains(lowerCommand, "codex")
    name = "codex";
elseif contains(lowerCommand, "claude")
    name = "claude";
elseif contains(lowerCommand, "deepseek")
    name = "deepseek";
else
    name = "CITT_AGENT_COMMAND";
end
end

function result = baseResult(commandText, purpose, expectedArtifacts, snapshot)
result = struct();
result.success = false;
result.mode = "";
result.purpose = string(purpose);
result.agent_name = "";
result.summary = "";
result.command = string(commandText);
result.exit_status = [];
result.stdout = "";
result.stderr = "";
result.agent_attempts = 0;
result.agent_pid = "";
result.agent_stdout_path = "";
result.agent_stderr_path = "";
result.agent_status_path = "";
result.agent_exit_status_path = "";
result.agent_attempt_path = "";
result.agent_script_path = "";
result.expected_artifacts = string(expectedArtifacts(:));
result.produced_artifacts = strings(0, 1);
result.artifact_snapshot = snapshot;
end

function snapshot = artifactSnapshot(paths)
paths = string(paths(:));
snapshot = repmat(struct("path", "", "stamp", NaN), numel(paths), 1);
for i = 1:numel(paths)
    snapshot(i).path = paths(i);
    snapshot(i).stamp = fileStamp(paths(i));
end
end

function waitForArtifacts(paths, snapshot, timeoutSeconds)
if isempty(paths)
    return
end
startTime = tic;
while toc(startTime) < timeoutSeconds
    [~, missing] = collectArtifacts(paths, snapshot);
    if isempty(missing)
        return
    end
    pause(0.25);
end
end

function [produced, missing] = collectArtifacts(paths, snapshot)
paths = string(paths(:));
produced = strings(0, 1);
missing = strings(0, 1);
for i = 1:numel(paths)
    path = paths(i);
    previousStamp = NaN;
    if i <= numel(snapshot)
        previousStamp = snapshot(i).stamp;
    end
    if exist(path, "file") == 2 && artifactIsFresh(path, previousStamp)
        produced(end + 1, 1) = path; %#ok<AGROW>
    else
        missing(end + 1, 1) = path; %#ok<AGROW>
    end
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

function value = optionFlag(options, fieldName, defaultValue)
value = logical(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    value = logical(options.(fieldName));
end
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function values = optionStringArray(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    values = string(options.(fieldName));
else
    values = string(defaultValue);
end
values = values(:);
values = values(strlength(strtrim(values)) > 0);
end

function text = appendBlock(header, body)
body = string(body);
if strlength(strtrim(body)) == 0
    text = header;
else
    text = header + newline + body;
end
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

function writeText(path, text)
fid = fopen(char(path), "w");
if fid < 0
    error("CiTT:FileWriteFailed", "Could not write file: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end

function quoted = shellQuote(value)
raw = char(string(value));
singleQuote = char(39);
doubleQuote = char(34);
replacement = [singleQuote doubleQuote singleQuote doubleQuote singleQuote];
raw = strrep(raw, singleQuote, replacement);
quoted = string([singleQuote raw singleQuote]);
end
