function result = addProbe(modelPath, targetId, probeMapInput, circuitSpecInput, options)
%ADDPROBE Add or highlight a probe from the SATK-generated probe map.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(targetId)
    targetId = "";
end
if nargin < 3 || isempty(probeMapInput)
    probeMapInput = config.ProbeMapPath;
end
if nargin < 4 || isempty(circuitSpecInput)
    circuitSpecInput = config.LastSpecPath;
end
if nargin < 5 || isempty(options)
    options = struct();
end

outputPath = config.ProbeActionPlanPath;
if isfield(options, "OutputPath")
    outputPath = string(options.OutputPath);
end

result = struct();
result.success = false;
result.model_path = string(modelPath);
result.target_id = string(targetId);
result.used_probe_map = false;
result.instructions = strings(0, 1);
result.automated_actions = strings(0, 1);
result.warnings = strings(0, 1);

probeMap = readJsonOrStruct(probeMapInput);
probe = findProbe(probeMap, targetId);
if isempty(probe)
    error("CiTT:ProbeMissing", ...
        "Probe target %s was not found in the SATK-generated probe map: %s", string(targetId), string(probeMapInput));
end
validateProbeEntry(probe, targetId);
result.used_probe_map = true;

result.instructions = [result.instructions; probeInstructions(probe)];

if exist(modelPath, "file") ~= 2
    error("CiTT:ModelMissing", "Model file not found. Run the SATK agent first: %s", string(modelPath));
end

[~, modelName, ~] = fileparts(modelPath);
load_system(char(modelPath));
open_system(char(modelName));
paths = getPathList(probe, "block_paths");
if ~isempty(paths)
    hilite_system(char(paths(1)), "find");
    result.automated_actions(end + 1) = "Highlighted target block: " + paths(1);
else
    modelPaths = getPathList(probe, "model_paths");
    if isempty(modelPaths)
        error("CiTT:ProbePathMissing", "Probe map entry has no block_paths or model_paths for target: %s", string(targetId));
    else
        open_system(char(modelPaths(1)));
        result.automated_actions(end + 1) = "Opened probe model path: " + modelPaths(1);
    end
end

result.success = true;
writeJson(outputPath, result);
end

function validateProbeEntry(probe, targetId)
required = [
    "probe_id"
    "focus_id"
    "label"
    "target_type"
    "model_paths"
    "block_paths"
    "quantity"
    "unit"
    "suggested_sensor_or_logging"
    "instructions"
];
missing = strings(0, 1);
for i = 1:numel(required)
    if ~isfield(probe, required(i))
        missing(end + 1) = required(i); %#ok<AGROW>
    end
end
if ~isempty(missing)
    error("CiTT:ProbeMapInvalid", ...
        "Probe map entry for %s is missing required field(s): %s", string(targetId), strjoin(missing, ", "));
end
end

function value = readJsonOrStruct(inputValue)
if isstruct(inputValue)
    value = inputValue;
    return
end
path = string(inputValue);
if strlength(path) == 0 || exist(path, "file") ~= 2
    error("CiTT:JsonMissing", "JSON file not found: %s", path);
end
value = jsondecode(fileread(path));
end

function probe = findProbe(probeMap, targetId)
probe = [];
items = unwrapItems(probeMap);
targetId = string(targetId);
if strlength(targetId) == 0 && ~isempty(items)
    probe = items(1);
    return
end
for i = 1:numel(items)
    ids = [getField(items(i), "probe_id"), getField(items(i), "focus_id"), getField(items(i), "id")];
    if any(ids == targetId)
        probe = items(i);
        return
    end
end
end

function items = unwrapItems(value)
if isstruct(value) && isfield(value, "probe_map")
    items = value.probe_map;
elseif isstruct(value) && isfield(value, "items")
    items = value.items;
elseif isstruct(value)
    items = value;
else
    items = struct([]);
end
end

function lines = probeInstructions(probe)
lines = strings(0, 1);
lines(end + 1) = "Probe target: " + getField(probe, "label");
lines(end + 1) = "Quantity: " + getField(probe, "quantity") + " (" + getField(probe, "unit") + ")";
lines(end + 1) = "Simscape-first action: " + getField(probe, "suggested_sensor_or_logging");
lines(end + 1) = "If using Simscape, add a Voltage Sensor or Current Sensor and route through PS-Simulink Converter for logging.";
extra = getField(probe, "instructions");
if strlength(extra) > 0
    lines(end + 1) = "Agent instructions: " + extra;
end
end

function paths = getPathList(value, fieldName)
paths = strings(0, 1);
if ~isstruct(value) || ~isfield(value, fieldName)
    return
end
raw = value.(fieldName);
if iscell(raw)
    for i = 1:numel(raw)
        paths(end + 1) = string(raw{i}); %#ok<AGROW>
    end
else
    paths = string(raw(:));
end
end

function value = getField(container, fieldName)
if isstruct(container) && isfield(container, fieldName)
    value = valueToText(container.(fieldName));
else
    value = "";
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
    text = string(mat2str(value));
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid >= 0
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end
end
