function result = parseCircuitWithGemini(imagePath, promptText, options)
%PARSECIRCUITWITHGEMINI Parse an image/prompt into a structured circuit spec.
% Uses the configured parser backend strictly. No automatic backend switching.

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
backend = string(config.ParserBackend);
if isfield(options, "ParserBackend")
    backend = normalizeParserBackend(options.ParserBackend);
end

if strlength(string(imagePath)) == 0 && strlength(string(promptText)) == 0
    error("CiTT:EmptyCircuitInput", "Provide a circuit image path or a text circuit prompt.");
end

spec = [];
switch backend
    case "codex"
        rawText = callAgentParser(imagePath, promptText, config);
    case "gemini"
        if strlength(config.GeminiApiKey) == 0
            error("CiTT:GeminiKeyMissing", ...
                "CITT_PARSER_BACKEND=gemini requires GEMINI_API_KEY.");
        end
        rawText = callGemini(imagePath, promptText, config);
    case "local"
        spec = deterministicTextParser(promptText, imagePath);
        if isempty(spec)
            error("CiTT:LocalParserUnsupported", ...
                "CITT_PARSER_BACKEND=local only supports explicit text circuits currently.");
        end
        rawText = string(feval('citt.util.jsonEncode', spec));
    otherwise
        error("CiTT:ParserBackendUnsupported", ...
            "Unsupported CITT_PARSER_BACKEND: %s", backend);
end

if isempty(spec)
    rawText = stripCodeFence(rawText);
    try
        spec = jsondecode(char(rawText));
    catch decodeError
        error("CiTT:ParserJsonDecodeFailed", ...
            "%s parser response was not valid JSON: %s", backend, decodeError.message);
    end
end

spec = normalizeCircuitSpec(spec);
validation = validateCircuitSpec(spec);
writeText(outputPath, feval('citt.util.jsonEncode', spec));
result = parseResult(true, spec, outputPath, rawText, validation);
end

function backend = normalizeParserBackend(value)
backend = lower(strtrim(string(value)));
if backend == "cli"
    backend = "codex";
elseif backend == "deterministic"
    backend = "local";
end
end

function rawText = callGemini(imagePath, promptText, config)
systemPrompt = readResourceText(config.MatlabRoot, ...
    fullfile("resources", "prompts", "gemini_circuit_parse_system.txt"));
schemaText = readResourceText(config.MatlabRoot, ...
    fullfile("resources", "schemas", "circuit_spec.schema.json"));

userText = strjoin([
    string(systemPrompt)
    ""
    "Return JSON only. Use this schema as the contract:"
    string(schemaText)
    ""
    "Student prompt:"
    string(promptText)
], newline);

parts = {struct("text", char(userText))};
if strlength(string(imagePath)) > 0
    image = feval('citt.util.readImageBytes', imagePath);
    inlineData = struct();
    inlineData.mime_type = char(image.mime_type);
    inlineData.data = char(image.base64);
    parts{end + 1} = struct("inline_data", inlineData);
end

content = struct();
content.role = "user";
content.parts = parts;

generationConfig = struct();
generationConfig.response_mime_type = "application/json";

body = struct();
body.contents = {content};
body.generationConfig = generationConfig;

url = "https://generativelanguage.googleapis.com/v1beta/models/" + ...
    config.GeminiModel + ":generateContent?key=" + config.GeminiApiKey;
webOpts = weboptions("MediaType", "application/json", "Timeout", 90);
response = webwrite(char(url), body, webOpts);
rawText = extractGeminiText(response);
end

function rawText = callAgentParser(imagePath, promptText, config)
codexPath = findCodexCli();
if strlength(codexPath) == 0
    error("CiTT:CodexCliMissing", ...
        "CITT_PARSER_BACKEND=codex requires Codex CLI. Set CITT_CODEX_CLI or install Codex.");
end

taskPath = string(fullfile(config.WorkDir, "citt_parse_agent_task.md"));
stdoutPath = string(fullfile(config.WorkDir, "citt_parse_agent_stdout.log"));
stderrPath = string(fullfile(config.WorkDir, "citt_parse_agent_stderr.log"));
promptTextForAgent = buildAgentParsePrompt(imagePath, promptText, config);
writeText(taskPath, promptTextForAgent);

command = "cat " + shellQuote(taskPath) + " | " + shellQuote(codexPath) + ...
    " exec --dangerously-bypass-approvals-and-sandbox --cd " + shellQuote(config.MatlabRoot);
if strlength(strtrim(string(imagePath))) > 0 && exist(string(imagePath), "file") == 2
    command = command + " --image " + shellQuote(imagePath);
end
command = command + " -";

result = feval('citt.util.safeSystem', command);
writeText(stdoutPath, result.stdout);
writeText(stderrPath, result.stderr);
if result.status ~= 0
    error("CiTT:CodexParserFailed", ...
        "Codex parser exited with status %d. See %s and %s.", ...
        result.status, stdoutPath, stderrPath);
end

rawText = extractJsonText(result.stdout);
if strlength(rawText) == 0
    error("CiTT:CodexParserNoJson", ...
        "Codex parser did not return a valid circuit-spec JSON object. See %s.", stdoutPath);
end
end

function prompt = buildAgentParsePrompt(imagePath, promptText, config)
systemPrompt = readResourceText(config.MatlabRoot, ...
    fullfile("resources", "prompts", "gemini_circuit_parse_system.txt"));
schemaText = readResourceText(config.MatlabRoot, ...
    fullfile("resources", "schemas", "circuit_spec.schema.json"));
imageLine = "No image attached.";
if strlength(strtrim(string(imagePath))) > 0
    imageLine = "Image is attached to this Codex request. Also record this source path: " + string(imagePath);
end

prompt = strjoin([
    "You are CiTT's CLI circuit parser."
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

function path = findCodexCli()
candidatePaths = [
    string(getenv("CITT_CODEX_CLI"))
    "/Applications/Codex.app/Contents/Resources/codex"
];
for i = 1:numel(candidatePaths)
    candidate = strtrim(candidatePaths(i));
    if strlength(candidate) > 0 && exist(candidate, "file") == 2
        path = candidate;
        return
    end
end
result = feval('citt.util.safeSystem', "/bin/zsh -lc 'command -v codex'");
if result.status == 0 && strlength(strtrim(result.stdout)) > 0
    lines = splitlines(strtrim(result.stdout));
    path = string(lines(1));
else
    path = "";
end
end

function text = extractJsonText(output)
raw = string(output);
text = stripCodeFence(raw);
try
    parsed = jsondecode(char(text));
    if isCircuitSpecLike(parsed)
        return
    end
catch
end

chars = char(raw);
starts = strfind(chars, "{");
ends = strfind(chars, "}");
text = "";
if isempty(starts) || isempty(ends)
    return
end
for s = starts
    candidateEnds = ends(ends > s);
    for eIndex = numel(candidateEnds):-1:1
        e = candidateEnds(eIndex);
        candidate = string(chars(s:e));
        try
            parsed = jsondecode(char(candidate));
            if isCircuitSpecLike(parsed)
                text = candidate;
                return
            end
        catch
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

function quoted = shellQuote(value)
raw = char(string(value));
singleQuote = char(39);
doubleQuote = char(34);
replacement = [singleQuote doubleQuote singleQuote doubleQuote singleQuote];
raw = strrep(raw, singleQuote, replacement);
quoted = string([singleQuote raw singleQuote]);
end

function rawText = extractGeminiText(response)
rawText = "";
try
    candidates = response.candidates;
    if numel(candidates) > 0
        parts = candidates(1).content.parts;
        if numel(parts) > 0 && isfield(parts(1), "text")
            rawText = string(parts(1).text);
        end
    end
catch
    rawText = "";
end

if strlength(rawText) == 0
    error("CiTT:GeminiEmptyResponse", "Gemini did not return a text JSON response.");
end
end

function spec = deterministicTextParser(promptText, imagePath)
spec = [];
if strlength(strtrim(string(imagePath))) > 0
    return
end

text = lower(string(promptText));
if ~(contains(text, "resistor") || contains(text, "ohm") || contains(text, "Ω"))
    return
end
if ~(contains(text, "capacitor") || contains(text, "farad") || contains(text, " f"))
    return
end
if ~(contains(text, "ac") || contains(text, "hz") || contains(text, "vpp"))
    return
end

[rValue, rOk] = parseNumberNearUnit(text, ["ohm", "Ω"]);
[cValue, cOk] = parseNumberNearUnit(text, ["f", "farad", "farads"]);
[frequency, fOk] = parseNumberNearUnit(text, ["hz", "hertz"]);
[vpp, vOk] = parseNumberNearUnit(text, ["vpp", "vp-p"]);
if ~vOk
    [vpp, vOk] = parseNumberNearUnit(text, ["v"]);
end
if ~(rOk && cOk && frequency > 0 && fOk && vOk)
    spec = [];
    return
end

sourceValue = struct("v_pp", vpp, "amplitude", vpp / 2, "frequency", frequency);
spec = struct();
spec.x_schema = "https://json-schema.org/draft/2020-12/schema";
spec.circuit_type = "Series RC Circuit";
spec.components = [
    component("R1", "resistor", "R1", rValue, "Ohm", ["p1", "p2"])
    component("C1", "capacitor", "C1", cValue, "F", ["p1", "p2"])
    component("Vac", "ac_voltage_source", "Vac", sourceValue, "V", ["p", "n"])
];
spec.nodes = {"n_source_out", "n_mid", "gnd"};
spec.connections = [
    connection("Vac.p", "R1.p1", "source_to_resistor")
    connection("R1.p2", "C1.p1", "resistor_to_capacitor")
    connection("C1.p2", "Vac.n", "capacitor_to_source_return")
];
spec.ground_node = "gnd";
spec.sources = struct( ...
    "id", "Vac", ...
    "type", "sinusoidal", ...
    "amplitude_v", vpp / 2, ...
    "peak_to_peak_voltage", vpp, ...
    "frequency_hz", frequency, ...
    "phase_deg", 0);
spec.requested_outputs = { ...
    "RMS current", ...
    "Peak current", ...
    "Peak-to-peak current", ...
    "Phase relationship between voltage and current"};
spec.likely_analysis = "AC steady-state phasor analysis";
spec.assumptions = { ...
    "Used the deterministic text parser for an explicit series RC AC prompt.", ...
    "The AC source is sinusoidal and ideal.", ...
    "The resistor and capacitor are ideal.", ...
    "The listed elements are connected in series."};
spec.ambiguities = {};
spec.unsupported_or_unclear_regions = {};
spec.suggested_simscape_blocks = { ...
    "foundation.electrical.sources.ac_voltage", ...
    "foundation.electrical.elements.resistor", ...
    "foundation.electrical.elements.capacitor", ...
    "foundation.electrical.sensors.current", ...
    "foundation.electrical.elements.reference"};
spec.focus_points = [
    focusPoint("cap_impedance", "Capacitive reactance", ...
        "The capacitor impedance at the source frequency sets the reactive part of the series impedance.", ...
        {"C1"}, {"n_mid", "gnd"}, ...
        "What is Xc = 1/(2*pi*f*C), and how does it compare with R?")
    focusPoint("series_current", "Series current", ...
        "All series elements share the same current, so source current equals resistor and capacitor branch current.", ...
        {"Vac", "R1", "C1"}, {"n_source_out", "n_mid", "gnd"}, ...
        "How do Vpp, RMS voltage, and total impedance determine RMS current?")
];
spec.teaching_focus_points = spec.focus_points;
end

function item = component(id, type, label, value, unit, terminals)
item = struct();
item.id = id;
item.type = type;
item.label = label;
item.value = value;
item.unit = unit;
item.terminals = cellstr(terminals);
item.confidence = 0.88;
end

function item = connection(from, to, label)
item = struct("from", from, "to", to, "label", label, "confidence", 0.88);
end

function item = focusPoint(id, label, reason, components, nodes, question)
item = struct();
item.id = id;
item.label = label;
item.reason = reason;
item.related_components = components;
item.related_nodes = nodes;
item.teaching_question = question;
end

function [value, ok] = parseNumberNearUnit(text, units)
value = NaN;
ok = false;
for i = 1:numel(units)
    unit = regexptranslate("escape", char(units(i)));
    pattern = "([0-9]+(?:\.[0-9]+)?)\s*(" + unit + ")";
    tokens = regexp(char(text), char(pattern), "tokens", "once");
    if ~isempty(tokens)
        value = str2double(tokens{1});
        ok = ~isnan(value);
        return
    end
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

function result = parseResult(success, spec, outputPath, rawText, validation)
result = struct();
result.success = success;
result.spec = spec;
result.spec_path = string(outputPath);
result.raw_response = string(rawText);
result.validation = validation;
result.ambiguities = spec.ambiguities;
end
