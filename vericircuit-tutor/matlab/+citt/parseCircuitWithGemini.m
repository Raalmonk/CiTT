function result = parseCircuitWithGemini(imagePath, promptText, options)
%PARSECIRCUITWITHGEMINI Parse an image/prompt into a structured circuit spec.
% Gemini is required for parsing.

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

if strlength(config.GeminiApiKey) == 0
    error("CiTT:GeminiKeyMissing", ...
        "Gemini parsing requires GEMINI_API_KEY.");
end

if strlength(string(imagePath)) == 0 && strlength(string(promptText)) == 0
    error("CiTT:EmptyCircuitInput", "Provide a circuit image path or a text circuit prompt.");
end

rawText = callGemini(imagePath, promptText, config);

rawText = stripCodeFence(rawText);
try
    spec = jsondecode(char(rawText));
catch decodeError
    error("CiTT:GeminiJsonDecodeFailed", ...
        "Gemini response was not valid JSON: %s", decodeError.message);
end

spec = normalizeCircuitSpec(spec);
validation = validateCircuitSpec(spec);
writeText(outputPath, feval('citt.util.jsonEncode', spec));
result = parseResult(true, spec, outputPath, rawText, validation);
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
        "Gemini circuit spec is missing required field(s): %s", strjoin(missing, ", "));
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
