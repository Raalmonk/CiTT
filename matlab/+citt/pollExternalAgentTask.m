function result = pollExternalAgentTask(startResult)
%POLLEXTERNALAGENTTASK Poll an asynchronously launched non-build SATK task.

result = startResult;
if ~isstruct(result) || isempty(result)
    error("CiTT:ExternalAgentRunMissing", "No external agent run state was provided.");
end

result.stdout = readTextIfExists(fieldOr(result, "agent_stdout_path", ""));
result.stderr = readTextIfExists(fieldOr(result, "agent_stderr_path", ""));
result.agent_attempts = parseIntegerFile(fieldOr(result, "agent_attempt_path", ""), 0);

expectedArtifacts = string(fieldOr(result, "expected_artifacts", strings(0, 1)));
snapshot = fieldOr(result, "artifact_snapshot", artifactSnapshot(expectedArtifacts));
waitForArtifacts(expectedArtifacts, snapshot, 1);
[produced, missing] = collectArtifacts(expectedArtifacts, snapshot);
result.produced_artifacts = produced;

exitPath = string(fieldOr(result, "agent_exit_status_path", ""));
pid = string(fieldOr(result, "agent_pid", ""));
if strlength(pid) > 0 && processIsRunning(pid) && exist(exitPath, "file") ~= 2
    result.mode = "external_agent_pending";
    result.success = false;
    result.exit_status = [];
    result.summary = "External SATK agent is still running.";
    return
end

if exist(exitPath, "file") == 2
    result.exit_status = parseIntegerFile(exitPath, -1);
else
    result.exit_status = -1;
    result.stderr = appendLine(result.stderr, "Agent process is not running and no exit status file was written.");
end

result.mode = "external_agent";
purpose = string(fieldOr(result, "purpose", "external"));
if result.exit_status == 0 && isempty(missing)
    result.success = true;
    result.summary = "External SATK agent completed " + purpose + " and produced expected artifacts.";
else
    result.success = false;
    result.summary = "External SATK agent did not complete the " + purpose + " contract.";
    if result.exit_status ~= 0
        result.stderr = appendLine(result.stderr, "Agent CLI exited with status " + string(result.exit_status) + ".");
    end
    if ~isempty(missing)
        result.stderr = appendLine(result.stderr, "Missing or stale expected artifacts: " + strjoin(missing, ", ") + ".");
    end
end
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
if strlength(path) == 0 || exist(path, "file") ~= 2
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
    value = data.(char(fieldName));
else
    value = defaultValue;
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
