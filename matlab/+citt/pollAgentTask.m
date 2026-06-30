function result = pollAgentTask(startResult)
%POLLAGENTTASK Poll an asynchronously launched external SATK agent run.

config = feval('citt.loadConfig');
result = baseResult(fieldOr(startResult, "command", ""), config);
result.mode = "external_agent_pending";
result.agent_name = fieldOr(startResult, "agent_name", "unknown");
result.agent_pid = fieldOr(startResult, "agent_pid", "");
result.agent_stdout_path = fieldOr(startResult, "agent_stdout_path", fullfile(config.WorkDir, "citt_agent_stdout.log"));
result.agent_stderr_path = fieldOr(startResult, "agent_stderr_path", fullfile(config.WorkDir, "citt_agent_stderr.log"));
result.agent_status_path = fieldOr(startResult, "agent_status_path", fullfile(config.WorkDir, "citt_agent_status.txt"));
result.agent_exit_status_path = fieldOr(startResult, "agent_exit_status_path", fullfile(config.WorkDir, "citt_agent_exit_status.txt"));
result.agent_attempt_path = fieldOr(startResult, "agent_attempt_path", fullfile(config.WorkDir, "citt_agent_attempt.txt"));
result.agent_script_path = fieldOr(startResult, "agent_script_path", fullfile(config.WorkDir, "citt_run_agent.sh"));
result.artifact_snapshot = fieldOr(startResult, "artifact_snapshot", expectedArtifactSnapshot(config));
result.stdout = readTextIfExists(result.agent_stdout_path);
result.stderr = readTextIfExists(result.agent_stderr_path);
result.agent_attempts = parseIntegerFile(result.agent_attempt_path, 0);

waitForRequiredArtifacts(config, result.artifact_snapshot, 10);
[result, missingArtifacts] = collectArtifacts(result, config, result.artifact_snapshot);

if strlength(result.agent_pid) > 0 && processIsRunning(result.agent_pid) && ...
        exist(result.agent_exit_status_path, "file") ~= 2
    result.success = false;
    result.exit_status = [];
    result.summary = "External SATK agent is still running.";
    return
end

if exist(result.agent_exit_status_path, "file") == 2
    result.exit_status = parseIntegerFile(result.agent_exit_status_path, -1);
else
    result.exit_status = -1;
    result.stderr = appendLine(result.stderr, "Agent process is not running and no exit status file was written.");
end

result.mode = "external_agent";
if result.exit_status == 0 && isempty(missingArtifacts)
    result.success = true;
    result.summary = "External SATK agent completed and produced CiTT model artifacts.";
else
    result.success = false;
    result.summary = "External SATK agent did not complete the CiTT build contract.";
    if result.exit_status ~= 0
        result.stderr = appendLine(result.stderr, "Agent CLI exited with status " + string(result.exit_status) + ".");
    end
    if ~isempty(missingArtifacts)
        result.stderr = appendLine(result.stderr, "Missing or stale required artifacts: " + strjoin(missingArtifacts, ", ") + ".");
    end
end
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
result.agent_pid = "";
result.agent_stdout_path = "";
result.agent_stderr_path = "";
result.agent_status_path = "";
result.agent_exit_status_path = "";
result.agent_attempt_path = "";
result.agent_script_path = "";
result.produced_model_path = "";
result.produced_focus_map_path = "";
result.produced_probe_map_path = "";
result.generated_code_path = existingPath(config.GeneratedBuildScriptPath);
result.agent_report_path = "";
result.expected_model_path = config.GeneratedModelPath;
result.expected_focus_map_path = config.FocusMapPath;
result.expected_probe_map_path = config.ProbeMapPath;
result.expected_report_path = config.AgentReportPath;
end

function [result, missingArtifacts] = collectArtifacts(result, config, snapshot)
result.produced_model_path = existingPath(config.GeneratedModelPath);
result.produced_focus_map_path = existingPath(config.FocusMapPath);
result.produced_probe_map_path = existingPath(config.ProbeMapPath);
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

function waitForRequiredArtifacts(config, snapshot, timeoutSeconds)
startTime = tic;
while toc(startTime) < timeoutSeconds
    if allRequiredArtifactsFresh(config, snapshot)
        return
    end
    pause(0.25);
end
end

function fresh = allRequiredArtifactsFresh(config, snapshot)
fresh = artifactIsFresh(config.GeneratedModelPath, snapshot.model) && ...
    artifactIsFresh(config.FocusMapPath, snapshot.focus_map) && ...
    artifactIsFresh(config.ProbeMapPath, snapshot.probe_map) && ...
    artifactIsFresh(config.AgentReportPath, snapshot.report);
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

function snapshot = expectedArtifactSnapshot(config)
snapshot = struct();
snapshot.model = fileStamp(config.GeneratedModelPath);
snapshot.focus_map = fileStamp(config.FocusMapPath);
snapshot.probe_map = fileStamp(config.ProbeMapPath);
snapshot.report = fileStamp(config.AgentReportPath);
end

function stamp = fileStamp(path)
info = dir(char(string(path)));
if isempty(info)
    stamp = NaN;
else
    stamp = info(1).datenum;
end
end

function path = existingPath(pathCandidate)
pathCandidate = string(pathCandidate);
if isExistingFile(pathCandidate)
    path = pathCandidate;
else
    path = "";
end
end

function exists = isExistingFile(pathCandidate)
code = exist(pathCandidate, "file");
exists = code == 2 || code == 4;
end

function running = processIsRunning(pid)
pid = strtrim(string(pid));
if strlength(pid) == 0
    running = false;
    return
end
[status, ~] = system("/bin/ps -p " + shellQuote(pid) + " >/dev/null 2>&1");
running = status == 0;
end

function value = parseIntegerFile(path, defaultValue)
value = defaultValue;
text = strtrim(readTextIfExists(path));
if strlength(text) == 0
    return
end
parsed = str2double(text);
if isfinite(parsed)
    value = round(parsed);
end
end

function text = readTextIfExists(path)
path = string(path);
if ~isExistingFile(path)
    text = "";
    return
end
try
    text = string(fileread(char(path)));
catch
    text = "";
end
end

function value = fieldOr(data, fieldName, defaultValue)
if isstruct(data) && isfield(data, fieldName)
    value = data.(fieldName);
else
    value = defaultValue;
end
end

function result = openProducedModel(result)
try
    open_system(char(result.produced_model_path));
catch openError
    result.stderr = appendLine(result.stderr, "Model artifact exists but could not be opened: " + string(openError.message));
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

function quoted = shellQuote(value)
raw = char(string(value));
singleQuote = char(39);
doubleQuote = char(34);
replacement = [singleQuote doubleQuote singleQuote doubleQuote singleQuote];
raw = strrep(raw, singleQuote, replacement);
quoted = string([singleQuote raw singleQuote]);
end
