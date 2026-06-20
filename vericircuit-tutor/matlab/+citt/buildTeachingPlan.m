function result = buildTeachingPlan(circuitSpecInput, focusMapInput, modelCheckInput, simulationInput, options)
%BUILDTEACHINGPLAN Build ordered Socratic steps from spec and focus map.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(circuitSpecInput)
    circuitSpecInput = config.LastSpecPath;
end
if nargin < 2 || isempty(focusMapInput)
    focusMapInput = config.FocusMapPath;
end
if nargin < 3
    modelCheckInput = [];
end
if nargin < 4
    simulationInput = [];
end
if nargin < 5 || isempty(options)
    options = struct();
end

outputPath = config.TeachingPlanPath;
if isfield(options, "OutputPath")
    outputPath = string(options.OutputPath);
end

[spec, specSource] = readJsonOrStruct(circuitSpecInput);
focusItems = focusItemsFromInputs(focusMapInput);
if isempty(focusItems)
    error("CiTT:FocusMapEmpty", ...
        "SATK-generated focus map is required for teaching. Missing or empty: %s", string(focusMapInput));
end

steps = struct([]);
for i = 1:numel(focusItems)
    focus = focusItems(i);
    validateFocusEntry(focus, i);
    focusId = getFieldString(focus, ["focus_id", "id"], "focus_" + string(i));
    label = getFieldString(focus, ["label"], focusId);
    question = getFieldString(focus, ["teaching_question"], "");
    concept = getFieldString(focus, ["explanation"], "");
    step = struct();
    step.id = "step_" + pad(string(i), 2, "left", "0");
    step.title = "Inspect " + label;
    step.focus_id = focusId;
    step.concept = concept;
    step.student_question = question;
    step.expected_reasoning = expectedReasoning(spec, focus);
    step.reveal_hint = "Name the component, node, or physical quantity first; then relate it to KCL/KVL, impedance, or energy storage.";
    step.common_mistake = "Jumping to a numeric answer before checking polarity, units, or the measured node.";
    step.optional_value_reference = requestedOutputsText(spec);
    steps = [steps; step]; %#ok<AGROW>
end

plan = struct();
plan.created_at = string(datetime("now"));
plan.source_spec = specSource;
plan.model_check_source = sourceText(modelCheckInput);
plan.simulation_source = sourceText(simulationInput);
plan.steps = steps;

writeJson(outputPath, plan);

result = struct();
result.success = true;
result.plan = plan;
result.plan_path = string(outputPath);
result.step_count = numel(steps);
end

function validateFocusEntry(focus, index)
required = [
    "focus_id"
    "label"
    "explanation"
    "model_paths"
    "block_paths"
    "related_components"
    "related_nodes"
    "teaching_question"
];
missing = strings(0, 1);
for i = 1:numel(required)
    if ~isfield(focus, required(i))
        missing(end + 1) = required(i); %#ok<AGROW>
    end
end
if ~isempty(missing)
    error("CiTT:FocusMapInvalid", ...
        "Focus map entry %d is missing required field(s): %s", index, strjoin(missing, ", "));
end
end

function focusItems = focusItemsFromInputs(focusMapInput)
[focusMap, ~] = readJsonOrStruct(focusMapInput);
focusItems = unwrapFocusMap(focusMap);
end

function items = unwrapFocusMap(focusMap)
if isstruct(focusMap) && isfield(focusMap, "focus_map")
    items = focusMap.focus_map;
elseif isstruct(focusMap) && isfield(focusMap, "items")
    items = focusMap.items;
elseif isstruct(focusMap)
    items = focusMap;
else
    items = struct([]);
end
end

function text = expectedReasoning(spec, focus)
componentText = getFieldString(focus, ["related_components"], "");
nodeText = getFieldString(focus, ["related_nodes"], "");
analysisText = getFieldString(spec, ["likely_analysis"], "the selected analysis");
if strlength(componentText) > 0 || strlength(nodeText) > 0
    text = "Use " + analysisText + " reasoning around components [" + componentText + ...
        "] and nodes [" + nodeText + "]. Explain the physical quantity before computing it.";
else
    text = "Use " + analysisText + " reasoning. Identify reference polarity, current direction, and units before revealing values.";
end
end

function text = requestedOutputsText(spec)
if isfield(spec, "requested_outputs")
    text = valueToText(spec.requested_outputs);
else
    text = "";
end
end

function value = getFieldString(container, fieldNames, defaultValue)
value = string(defaultValue);
for i = 1:numel(fieldNames)
    name = char(fieldNames(i));
    if isstruct(container) && isfield(container, name)
        value = valueToText(container.(name));
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
    text = string(mat2str(value));
elseif isstruct(value)
    if numel(value) == 1 && isfield(value, "id")
        text = string(value.id);
    else
        text = string(feval('citt.util.jsonEncode', value));
    end
else
    text = string(value);
end
end

function [value, source] = readJsonOrStruct(inputValue)
if isstruct(inputValue)
    value = inputValue;
    source = "MATLAB struct";
    return
end
path = string(inputValue);
if strlength(path) == 0 || exist(path, "file") ~= 2
    error("CiTT:JsonMissing", "JSON file not found: %s", path);
end
value = jsondecode(fileread(path));
source = path;
end

function text = sourceText(value)
if isempty(value)
    text = "";
elseif isstruct(value)
    text = "MATLAB struct";
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
if fid < 0
    error("CiTT:WriteFailed", "Could not write: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end
