function result = generateModelTests(context, options)
%GENERATEMODELTESTS Generate conservative SATK model_test feature artifacts.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
featurePath = optionString(options, "FeaturePath", config.ModelTestFeaturePath);
manifestPath = optionString(options, "ManifestPath", config.ModelTestManifestPath);

spec = readJson(context.SpecPath);
focusItems = unwrapItems(readJson(context.FocusMapPath), ["focus_map", "items"]);
probeItems = unwrapItems(readJson(context.ProbeMapPath), ["probe_map", "probes", "items"]);

[~, modelName, ext] = fileparts(char(context.ModelPath));
if strlength(string(modelName)) == 0
    [~, modelName, ext] = fileparts(char(config.GeneratedModelPath));
end
modelFile = string(modelName) + string(ext);
if strlength(ext) == 0
    modelFile = string(modelName) + ".slx";
end
componentPath = string(modelName) + "/CiTT_TestInterface";

focus = firstStruct(focusItems);
probe = firstStruct(probeItems);
focusId = firstNonempty(firstFieldText(focus, ["focus_id", "id"], ""), "focus_001");
probeId = firstNonempty(firstFieldText(probe, ["probe_id", "id"], ""), "probe_vout");
learningObjective = firstNonempty( ...
    firstFieldText(focus, ["teaching_question", "learning_objective", "explanation", "label"], ""), ...
    "Verify that the teaching model has executable signal-level behavior.");

test = struct();
test.scenario_id = "TEST_FOCUS_001";
test.scenario = "Nominal input produces bounded output";
test.focus_id = focusId;
test.probe_id = probeId;
test.learning_objective = learningObjective;
test.component = componentPath;
test.input_aliases = struct("Vin", "Vin");
test.output_aliases = struct("Vout", "Vout");
test.evidence_kind = "behavioral_model_test";

manifest = struct();
manifest.created_at = string(datetime("now"));
manifest.source_spec = string(context.SpecPath);
manifest.model_path = string(context.ModelPath);
manifest.feature_path = string(featurePath);
manifest.tests = test;

featureText = strjoin([
    "# --- front-matter:toml ---"
    "model = """ + modelFile + """"
    "component = """ + componentPath + """"
    ""
    "[inputs]"
    "Vin = ""Vin"""
    ""
    "[outputs]"
    "Vout = ""Vout"""
    "# --- end front-matter ---"
    ""
    "Feature: CiTT teaching behavioral checks"
    "  Behavioral checks generated from CiTT focus and probe maps."
    ""
    "  Scenario: Nominal input produces bounded output"
    "    Given inputs"
    "    * Vin = const(1)"
    "    When simulate for 1s in Normal mode"
    "    Then outputs"
    "    * BoundedVout: Vout == [-10 .. 10]"
    ""
], newline);

writeText(featurePath, featureText);
writeJson(manifestPath, manifest);

result = struct();
result.success = true;
result.feature_path = string(featurePath);
result.manifest_path = string(manifestPath);
result.model_path = string(context.ModelPath);
result.component = componentPath;
result.tests = test;
result.summary = "Generated a conservative SATK model_test feature for CiTT_TestInterface.";
end

function context = normalizeContext(context, config)
if ~isfield(context, "SpecPath") || strlength(strtrim(string(context.SpecPath))) == 0
    context.SpecPath = config.LastSpecPath;
end
if ~isfield(context, "FocusMapPath") || strlength(strtrim(string(context.FocusMapPath))) == 0
    context.FocusMapPath = config.FocusMapPath;
end
if ~isfield(context, "ProbeMapPath") || strlength(strtrim(string(context.ProbeMapPath))) == 0
    context.ProbeMapPath = config.ProbeMapPath;
end
if ~isfield(context, "ModelPath") || strlength(strtrim(string(context.ModelPath))) == 0
    context.ModelPath = config.GeneratedModelPath;
end
end

function value = readJson(path)
value = [];
path = string(path);
if strlength(path) == 0 || exist(path, "file") ~= 2
    return
end
try
    value = jsondecode(fileread(path));
catch
    value = [];
end
end

function items = unwrapItems(value, fieldNames)
items = struct([]);
if ~isstruct(value) || isempty(value)
    return
end
for i = 1:numel(fieldNames)
    name = char(fieldNames(i));
    if isfield(value, name)
        items = value.(name);
        break
    end
end
if isempty(items)
    items = value;
end
if iscell(items)
    converted = struct([]);
    for i = 1:numel(items)
        if isstruct(items{i})
            converted(end + 1) = items{i}; %#ok<AGROW>
        end
    end
    items = converted;
end
if ~isstruct(items)
    items = struct([]);
end
end

function value = firstStruct(items)
if isstruct(items) && ~isempty(items)
    value = items(1);
else
    value = struct();
end
end

function text = firstFieldText(value, fieldNames, defaultValue)
text = string(defaultValue);
if ~isstruct(value) || isempty(value)
    return
end
for i = 1:numel(fieldNames)
    name = char(fieldNames(i));
    if isfield(value, name)
        text = valueToText(value.(name));
        return
    end
end
end

function text = firstNonempty(varargin)
text = "";
for i = 1:nargin
    candidate = string(varargin{i});
    if strlength(strtrim(candidate)) > 0
        text = candidate;
        return
    end
end
end

function text = valueToText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isnumeric(value) || islogical(value)
    text = string(value);
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid < 0
    error("CiTT:WriteFailed", "Could not write: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
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
