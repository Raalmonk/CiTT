function result = parseCircuitWithCli(imagePath, promptText, options)
%PARSECIRCUITWITHCLI Parse an image/prompt using only the configured CLI.

if nargin < 1 || isempty(imagePath)
    imagePath = "";
end
if nargin < 2 || isempty(promptText)
    promptText = "";
end
if nargin < 3 || isempty(options)
    options = struct();
end

config = feval('citt.loadConfig');
outputPath = config.LastSpecPath;
if isfield(options, "OutputPath")
    outputPath = string(options.OutputPath);
end

if strlength(strtrim(string(imagePath))) == 0 && strlength(strtrim(string(promptText))) == 0
    error("CiTT:EmptyCircuitInput", "Provide a circuit image path or a text circuit prompt.");
end

[rawText, runner] = callConfiguredCli(imagePath, promptText, config);
jsonText = extractJsonText(rawText);
if strlength(jsonText) == 0
    error("CiTT:CliParserNoJson", ...
        "%s did not return a valid circuit-spec JSON object.", runner.name);
end

try
    spec = jsondecode(char(jsonText));
catch decodeError
    error("CiTT:ParserJsonDecodeFailed", ...
        "%s response was not valid JSON: %s", runner.name, decodeError.message);
end

spec = normalizeCircuitSpec(spec);
validation = validateCircuitSpec(spec);
writeText(outputPath, feval('citt.util.jsonEncode', spec));
result = struct();
result.success = true;
result.spec = spec;
result.spec_path = string(outputPath);
result.raw_response = string(rawText);
result.validation = validation;
result.ambiguities = spec.ambiguities;
result.parser = runner.name;
end

function [rawText, runner] = callConfiguredCli(imagePath, promptText, config)
runner = selectCliRunner(config);
taskPath = string(fullfile(config.WorkDir, "citt_parse_cli_task.md"));
stdoutPath = string(fullfile(config.WorkDir, "citt_parse_cli_stdout.log"));
stderrPath = string(fullfile(config.WorkDir, "citt_parse_cli_stderr.log"));
writeText(taskPath, buildParsePrompt(imagePath, promptText, config, runner.name));

command = runner.command;
if runner.uses_template
    command = commandFromTemplate(command, taskPath);
end
if runner.name == "codex" && strlength(strtrim(string(imagePath))) > 0 && exist(string(imagePath), "file") == 2
    command = replace(command, " -", " --image " + shellQuote(imagePath) + " -");
end

systemResult = feval('citt.util.safeSystem', command);
writeText(stdoutPath, systemResult.stdout);
writeText(stderrPath, systemResult.stderr);
if systemResult.status ~= 0
    error("CiTT:CliParserFailed", ...
        "%s parser exited with status %d. See %s and %s.", ...
        runner.name, systemResult.status, stdoutPath, stderrPath);
end
rawText = string(systemResult.stdout);
end

function runner = selectCliRunner(config)
runner = struct("name", "", "command", "", "uses_template", false);
if strlength(strtrim(config.AgentCommand)) > 0
    runner.name = "configured_cli";
    runner.command = string(config.AgentCommand);
    runner.uses_template = true;
    return
end

error("CiTT:ParserCliMissing", ...
    "No selected CLI command is configured. Set CITT_AGENT_COMMAND or save a CLI template in Settings; CiTT will not auto-select another CLI.");
end

function prompt = buildParsePrompt(imagePath, promptText, config, runnerName)
systemPrompt = readResourceText(config.MatlabRoot, ...
    fullfile("resources", "prompts", "cli_circuit_parse_system.txt"));
schemaText = readResourceText(config.MatlabRoot, ...
    fullfile("resources", "schemas", "circuit_spec.schema.json"));
imageLine = "No image attached.";
if strlength(strtrim(string(imagePath))) > 0
    imageLine = "Circuit image source path: " + string(imagePath) + ...
        ". Use the selected CLI's image capability if available; otherwise record visual uncertainty instead of guessing.";
end

prompt = strjoin([
    "You are CiTT's selected CLI circuit parser."
    "Selected CLI: " + string(runnerName)
    "Return one JSON object only. Do not include markdown fences, prose, logs, or explanations."
    "Do not solve the circuit. Only parse the image/prompt into the CiTT Circuit Spec."
    ""
    string(systemPrompt)
    ""
    "Schema contract:"
    string(schemaText)
    ""
    string(imageLine)
    ""
    "Student prompt:"
    string(promptText)
], newline);
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

function rawText = extractJsonText(output)
raw = string(output);
text = stripCodeFence(raw);
try
    parsed = jsondecode(char(text));
    if isCircuitSpecLike(parsed)
        rawText = text;
        return
    end
catch
end

rawText = "";
fragments = jsonCandidateFragments(raw);
for fragmentIndex = 1:numel(fragments)
    candidates = circuitSpecCandidates(fragments(fragmentIndex));
    for candidateIndex = 1:numel(candidates)
        candidate = candidates(candidateIndex);
        try
            parsed = jsondecode(char(candidate));
            if isCircuitSpecLike(parsed)
                rawText = candidate;
                return
            end
        catch
        end
    end
end
end

function fragments = jsonCandidateFragments(raw)
fragments = stripCodeFence(raw);
lines = splitlines(string(raw));
for i = numel(lines):-1:1
    if strtrim(lines(i)) == "codex" && i < numel(lines)
        fragments(end + 1, 1) = stripCodeFence(strjoin(lines(i + 1:end), newline)); %#ok<AGROW>
    end
end
end

function candidates = circuitSpecCandidates(text)
chars = char(text);
candidates = strings(0, 1);
if isempty(chars)
    return
end

anchors = strfind(chars, '"circuit_type"');
for i = numel(anchors):-1:1
    startIndex = find(chars(1:anchors(i)) == "{", 1, "last");
    if isempty(startIndex)
        continue
    end
    candidate = balancedJsonObjectFromStart(chars, startIndex);
    if strlength(candidate) > 0
        candidates(end + 1, 1) = candidate; %#ok<AGROW>
    end
end

starts = strfind(chars, "{");
for i = numel(starts):-1:max(1, numel(starts) - 199)
    candidate = balancedJsonObjectFromStart(chars, starts(i));
    if strlength(candidate) > 0
        candidates(end + 1, 1) = candidate; %#ok<AGROW>
    end
end

candidates = unique(candidates, "stable");
end

function objectText = balancedJsonObjectFromStart(chars, startIndex)
objectText = "";
if startIndex < 1 || startIndex > numel(chars) || chars(startIndex) ~= '{'
    return
end

depth = 0;
inString = false;
escaped = false;
for i = startIndex:numel(chars)
    c = chars(i);
    if inString
        if escaped
            escaped = false;
        elseif c == '\'
            escaped = true;
        elseif c == '"'
            inString = false;
        end
        continue
    end

    if c == '"'
        inString = true;
    elseif c == '{'
        depth = depth + 1;
    elseif c == '}'
        depth = depth - 1;
        if depth == 0
            objectText = string(chars(startIndex:i));
            return
        end
    end
end
end

function tf = isCircuitSpecLike(value)
tf = isstruct(value) && isfield(value, "circuit_type") && ...
    isfield(value, "components") && isfield(value, "connections");
if tf
    tf = looksLikeObjectArray(value.components, "id") && ...
        looksLikeObjectArray(value.connections, "from");
end
end

function tf = looksLikeObjectArray(value, fieldName)
tf = false;
if isstruct(value)
    tf = numel(value) > 0 && isfield(value, fieldName);
elseif iscell(value) && ~isempty(value)
    first = value{1};
    tf = isstruct(first) && isfield(first, fieldName);
end
end

function text = stripCodeFence(text)
text = strtrim(string(text));
text = regexprep(text, "^```json\s*", "");
text = regexprep(text, "^```\s*", "");
text = regexprep(text, "\s*```$", "");
text = strtrim(text);
end

function spec = normalizeCircuitSpec(spec)
arrayFields = [
    "components"
    "nodes"
    "connections"
    "sources"
    "requested_outputs"
    "assumptions"
    "ambiguities"
    "unsupported_or_unclear_regions"
    "suggested_simscape_blocks"
    "digital_or_state_logic"
];

for i = 1:numel(arrayFields)
    fieldName = arrayFields(i);
    if isfield(spec, fieldName)
        spec.(fieldName) = ensureJsonArray(spec.(fieldName));
    end
end

hasFocus = isfield(spec, "focus_points");
hasTeachingFocus = isfield(spec, "teaching_focus_points");
if hasFocus && hasTeachingFocus
    focusPoints = mergeJsonArrays(spec.focus_points, spec.teaching_focus_points);
    spec.focus_points = focusPoints;
    spec.teaching_focus_points = focusPoints;
elseif hasTeachingFocus
    spec.focus_points = ensureJsonArray(spec.teaching_focus_points);
    spec.teaching_focus_points = spec.focus_points;
elseif hasFocus
    spec.focus_points = ensureJsonArray(spec.focus_points);
    spec.teaching_focus_points = spec.focus_points;
end

spec = feval('citt.demoteNonBlockingUnsupportedRegions', spec);
end

function values = ensureJsonArray(value)
if isempty(value)
    values = {};
elseif iscell(value)
    values = value(:)';
elseif isstruct(value)
    values = cell(1, numel(value));
    for i = 1:numel(value)
        values{i} = value(i);
    end
elseif isstring(value)
    values = cellstr(value(:)');
elseif ischar(value)
    values = {value};
elseif isnumeric(value) || islogical(value)
    values = num2cell(value(:)');
else
    values = {value};
end
end

function values = mergeJsonArrays(left, right)
leftValues = ensureJsonArray(left);
rightValues = ensureJsonArray(right);
values = [leftValues(:); rightValues(:)]';
if isempty(values)
    values = {};
    return
end

seen = strings(0, 1);
keep = true(size(values));
for i = 1:numel(values)
    item = values{i};
    if isstruct(item) && isfield(item, "id")
        itemId = string(item.id);
        if any(seen == itemId)
            keep(i) = false;
        else
            seen(end + 1) = itemId; %#ok<AGROW>
        end
    end
end
values = values(keep);
end

function validation = validateCircuitSpec(spec)
required = [
    "circuit_type"
    "components"
    "nodes"
    "connections"
    "ground_node"
    "sources"
    "requested_outputs"
    "likely_analysis"
    "assumptions"
    "ambiguities"
    "unsupported_or_unclear_regions"
    "suggested_simscape_blocks"
    "focus_points"
];

missing = strings(0, 1);
for i = 1:numel(required)
    if ~isfield(spec, required(i))
        missing(end + 1) = required(i); %#ok<AGROW>
    end
end
if ~isempty(missing)
    error("CiTT:CircuitSpecInvalid", ...
        "Circuit spec is missing required field(s): %s", strjoin(missing, ", "));
end

validateArrayObjects(spec.components, ["id", "type", "label", "value", "unit", "terminals", "confidence"], "components");
validateArrayObjects(spec.connections, ["from", "to", "label", "confidence"], "connections");
validateArrayObjects(spec.focus_points, ["id", "label", "reason", "related_components", "related_nodes", "teaching_question"], "focus_points");

validation = struct();
validation.valid = true;
validation.required_fields = required;
validation.message = "Circuit spec passed local CiTT validation.";
end

function validateArrayObjects(value, requiredFields, label)
if ~(isstruct(value) || iscell(value))
    error("CiTT:CircuitSpecInvalid", "Field %s must be an array of objects.", label);
end
if isempty(value)
    return
end

if iscell(value)
    for i = 1:numel(value)
        validateObject(value{i}, requiredFields, label);
    end
else
    for i = 1:numel(value)
        validateObject(value(i), requiredFields, label);
    end
end
end

function validateObject(value, requiredFields, label)
if ~isstruct(value)
    error("CiTT:CircuitSpecInvalid", "Field %s contains a non-object item.", label);
end
missing = strings(0, 1);
for i = 1:numel(requiredFields)
    if ~isfield(value, requiredFields(i))
        missing(end + 1) = requiredFields(i); %#ok<AGROW>
    end
end
if ~isempty(missing)
    error("CiTT:CircuitSpecInvalid", ...
        "%s item is missing required field(s): %s", label, strjoin(missing, ", "));
end
end

function text = readResourceText(matlabRoot, relativePath)
path = fullfile(matlabRoot, relativePath);
if exist(path, "file") ~= 2
    error("CiTT:MissingResource", "Required resource not found: %s", path);
end
text = string(fileread(path));
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid < 0
    error("CiTT:WriteFailed", "Could not write: %s", path);
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
