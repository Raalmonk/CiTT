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
        "Probe target %s was not found in the SATK-generated probe map: %s. Available probes: %s", ...
        string(targetId), string(probeMapInput), strjoin(availableProbeIds(probeMap), ", "));
end
validateProbeEntry(probe, targetId);
result.used_probe_map = true;

result.instructions = [result.instructions; probeInstructions(probe)];

if ~isExistingFile(modelPath)
    error("CiTT:ModelMissing", "Model file not found. Run the SATK agent first: %s", string(modelPath));
end

[~, modelName, ~] = fileparts(modelPath);
load_system(char(modelPath));
open_system(char(modelName));
paths = getPathList(probe, "block_paths");
if ~isempty(paths)
    targetPath = firstExistingPath(paths);
    if strlength(targetPath) == 0
        error("CiTT:ProbePathMissing", "None of the probe block_paths exist in the model for target: %s", string(targetId));
    end
    clearResult = feval('citt.clearHighlights', modelPath);
    result.automated_actions(end + 1) = "Cleared previous highlights for model: " + clearResult.model_name;
    hilite_system(char(targetPath), "find");
    result.automated_actions(end + 1) = "Highlighted target block: " + targetPath;
    [result, modelChanged] = ensureProbeLogging(modelName, probe, targetPath, result);
    if modelChanged
        save_system(char(modelName), char(modelPath));
        result.automated_actions(end + 1) = "Saved model after adding probe logging.";
    end
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

function path = firstExistingPath(paths)
path = "";
for i = 1:numel(paths)
    candidate = string(paths(i));
    try
        get_param(char(candidate), "Handle");
        path = candidate;
        return
    catch
    end
end
end

function [result, changed] = ensureProbeLogging(modelName, probe, targetPath, result)
changed = false;
if ~isSimscapeSensor(targetPath, probe)
    result.warnings(end + 1) = "Automatic probe insertion currently supports existing Simscape Voltage Sensor or Current Sensor blocks.";
    return
end

try
    handles = get_param(char(targetPath), "PortHandles");
    signalPort = sensorSignalPort(handles);
catch portError
    result.warnings(end + 1) = "Could not inspect probe target ports: " + string(portError.message);
    return
end

if isempty(signalPort)
    result.warnings(end + 1) = "Probe target has no detectable physical signal output port.";
    return
end

if portHasLine(signalPort)
    result.automated_actions(end + 1) = "Probe signal output is already connected: " + targetPath + " RConn(1).";
    return
end

suffix = probeBlockSuffix(probe);
converterPath = uniqueBlockPath(modelName, "PS2SL_" + suffix);
scopePath = uniqueBlockPath(modelName, "Scope_" + suffix);
position = shiftedPosition(targetPath);

try
    add_block("nesl_utility/PS-Simulink Converter", char(converterPath), ...
        "Position", position.converter);
    add_block("simulink/Sinks/Scope", char(scopePath), ...
        "Position", position.scope);

    converterHandles = get_param(char(converterPath), "PortHandles");
    scopeHandles = get_param(char(scopePath), "PortHandles");
    add_line(char(modelName), signalPort, converterHandles.LConn(1), "autorouting", "on");
    add_line(char(modelName), converterHandles.Outport(1), scopeHandles.Inport(1), "autorouting", "on");

    result.automated_actions(end + 1) = "Added probe logging chain: " + ...
        targetPath + " -> " + converterPath + " -> " + scopePath;
    changed = true;
catch addError
    result.warnings(end + 1) = "Could not add probe logging chain: " + string(addError.message);
end
end

function supported = isSimscapeSensor(targetPath, probe)
referenceBlock = "";
try
    referenceBlock = string(get_param(char(targetPath), "ReferenceBlock"));
catch
end
quantityText = lower(getField(probe, "quantity") + " " + getField(probe, "target_type") + " " + referenceBlock);
supported = contains(quantityText, "voltage sensor") || contains(quantityText, "current sensor") || ...
    contains(quantityText, "voltage") || contains(quantityText, "current");
supported = supported && contains(lower(referenceBlock), "sensor");
end

function signalPort = sensorSignalPort(handles)
signalPort = [];
if isfield(handles, "RConn") && numel(handles.RConn) >= 1
    signalPort = handles.RConn(1);
end
end

function connected = portHasLine(portHandle)
connected = false;
try
    lineHandle = get_param(portHandle, "Line");
    connected = isnumeric(lineHandle) && isscalar(lineHandle) && lineHandle > 0;
catch
end
end

function suffix = probeBlockSuffix(probe)
raw = getField(probe, "probe_id");
if strlength(raw) == 0
    raw = getField(probe, "focus_id");
end
if strlength(raw) == 0
    raw = getField(probe, "quantity");
end
suffix = string(matlab.lang.makeValidName(char(raw)));
end

function path = uniqueBlockPath(modelName, baseName)
baseName = string(matlab.lang.makeValidName(char(baseName)));
path = string(modelName) + "/" + baseName;
index = 2;
while blockExists(path)
    path = string(modelName) + "/" + baseName + "_" + string(index);
    index = index + 1;
end
end

function exists = blockExists(path)
try
    get_param(char(path), "Handle");
    exists = true;
catch
    exists = false;
end
end

function tf = isExistingFile(pathValue)
code = exist(string(pathValue), "file");
tf = code == 2 || code == 4;
end

function position = shiftedPosition(targetPath)
try
    targetPosition = get_param(char(targetPath), "Position");
catch
    targetPosition = [500 300 580 360];
end
x = targetPosition(3) + 120;
y = targetPosition(2);
position = struct();
position.converter = [x y x + 110 y + 55];
position.scope = [x + 160 y x + 240 y + 55];
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

function ids = availableProbeIds(probeMap)
items = unwrapItems(probeMap);
ids = strings(0, 1);
for i = 1:numel(items)
    probeId = getField(items(i), "probe_id");
    focusId = getField(items(i), "focus_id");
    if strlength(probeId) > 0
        ids(end + 1) = probeId; %#ok<AGROW>
    end
    if strlength(focusId) > 0
        ids(end + 1) = focusId; %#ok<AGROW>
    end
end
ids = unique(ids);
if isempty(ids)
    ids = "none";
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
