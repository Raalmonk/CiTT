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
    step.fact_lines = focusFactLines(focus, spec);
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

function lines = focusFactLines(focus, spec)
lines = strings(0, 1);
components = getFieldString(focus, ["related_components"], "");
nodes = getFieldString(focus, ["related_nodes"], "");
blocks = blockFacts(focus);
outputs = requestedOutputsText(spec);
values = componentValueFacts(focus, spec);
taskValues = taskValueFacts(spec);
if strlength(strtrim(components)) > 0
    lines(end + 1) = "Components: " + components;
end
if strlength(strtrim(nodes)) > 0
    lines(end + 1) = "Nodes: " + nodes;
end
if strlength(strtrim(values)) > 0
    lines(end + 1) = "Known values: " + values;
end
if strlength(strtrim(taskValues)) > 0
    lines(end + 1) = "Task values: " + taskValues;
end
if strlength(strtrim(blocks)) > 0
    lines(end + 1) = "Model values: " + blocks;
end
if strlength(strtrim(outputs)) > 0
    lines(end + 1) = "Measured outputs: " + outputs;
end
end

function text = blockFacts(focus)
text = "";
if ~isstruct(focus) || ~isfield(focus, "block_paths")
    return
end
raw = string(focus.block_paths);
if isempty(raw)
    return
end
parts = strings(0, 1);
limit = min(numel(raw), 5);
for i = 1:limit
    blockPathParts = split(raw(i), "/");
    blockName = blockPathParts(end);
    if strlength(strtrim(blockName)) == 0
        blockName = raw(i);
    end
    parts(end + 1) = prettifyBlockName(blockName); %#ok<AGROW>
end
if numel(raw) > limit
    parts(end + 1) = "+" + string(numel(raw) - limit) + " more";
end
text = strjoin(parts, "; ");
end

function text = componentValueFacts(focus, spec)
text = "";
if ~isstruct(spec) || ~isfield(spec, "components")
    return
end
ids = relatedComponentIds(focus);
if isempty(ids)
    return
end
components = forceStructArray(spec.components);
if isempty(components)
    return
end
parts = strings(0, 1);
for i = 1:numel(ids)
    component = findComponentById(components, ids(i));
    if isempty(component)
        continue
    end
    fact = componentFact(component);
    if strlength(strtrim(fact)) > 0
        parts(end + 1, 1) = fact; %#ok<AGROW>
    end
end
parts = [parts; generatedDefaultFacts(ids)];
if ~isempty(parts)
    text = strjoin(unique(parts, "stable"), "; ");
end
end

function parts = generatedDefaultFacts(ids)
parts = strings(0, 1);
idsLower = lower(strjoin(ids, " "));
if contains(idsLower, "src_pk") || contains(idsLower, "pk")
    parts(end + 1, 1) = "generated PK defaults: peak scale 10 uM, ka 0.02 1/s, ke 0.002 1/s, bioavailability 1";
end
if contains(idsLower, "adc")
    parts(end + 1, 1) = "generated ADC references: Vref lo 0 V, Vref hi 3.3 V";
end
if contains(idsLower, "u_tia") || contains(idsLower, "opamp") || contains(idsLower, "op_amp")
    parts(end + 1, 1) = "generated op-amp defaults: rails 0 to 3.3 V, open-loop gain 1e5, pole 100 kHz";
end
end

function text = taskValueFacts(spec)
text = "";
if ~isstruct(spec)
    return
end
ignored = ["components", "nodes", "connections", "assumptions", "ambiguities", ...
    "unsupported_or_unclear_regions", "suggested_simscape_blocks", "focus_points", ...
    "teaching_focus_points", "requested_outputs", "circuit_type", "likely_analysis", ...
    "ground_node", "sources"];
names = string(fieldnames(spec));
parts = strings(0, 1);
for i = 1:numel(names)
    name = names(i);
    if any(name == ignored)
        continue
    end
    value = spec.(char(name));
    if isstruct(value) || iscell(value)
        continue
    end
    valueText = valueToText(value);
    if strlength(strtrim(valueText)) == 0
        continue
    end
    parts(end + 1) = prettifyFieldName(name) + " = " + valueText; %#ok<AGROW>
    if numel(parts) >= 6
        break
    end
end
if ~isempty(parts)
    text = strjoin(parts, "; ");
end
end

function ids = relatedComponentIds(focus)
ids = strings(0, 1);
if ~isstruct(focus) || ~isfield(focus, "related_components")
    return
end
rawValues = flattenStrings(focus.related_components);
for i = 1:numel(rawValues)
    pieces = split(rawValues(i), [",", ";", "|"]);
    for j = 1:numel(pieces)
        piece = stripComponentToken(pieces(j));
        if strlength(piece) > 0
            ids(end + 1, 1) = piece; %#ok<AGROW>
        end
    end
end
ids = unique(ids, "stable");
end

function values = flattenStrings(value)
if isempty(value)
    values = strings(0, 1);
elseif isstring(value)
    values = value(:);
elseif ischar(value)
    values = string(value);
elseif iscell(value)
    values = strings(0, 1);
    for i = 1:numel(value)
        values = [values; flattenStrings(value{i})]; %#ok<AGROW>
    end
elseif isnumeric(value) || islogical(value)
    values = string(value(:));
else
    values = string(valueToText(value));
end
end

function text = stripComponentToken(value)
text = strtrim(string(value));
text = regexprep(text, "^[\[\]\(\)""']+|[\[\]\(\)""']+$", "");
text = strtrim(text);
end

function components = forceStructArray(value)
if isempty(value)
    components = struct([]);
elseif iscell(value)
    components = struct([]);
    for i = 1:numel(value)
        if isstruct(value{i})
            components = [components; value{i}(:)]; %#ok<AGROW>
        end
    end
elseif isstruct(value)
    components = value(:);
else
    components = struct([]);
end
end

function component = findComponentById(components, id)
component = [];
target = lower(strtrim(string(id)));
for i = 1:numel(components)
    componentId = lower(strtrim(getFieldString(components(i), ["id", "name"], "")));
    componentLabel = lower(strtrim(getFieldString(components(i), ["label"], "")));
    if componentId == target || componentLabel == target
        component = components(i);
        return
    end
end
end

function text = componentFact(component)
id = getFieldString(component, ["id", "name"], "component");
label = getFieldString(component, ["label", "type"], "");
unit = getFieldString(component, ["unit"], "");
value = "";
if isfield(component, "value")
    value = componentValueText(component.value, unit);
elseif isfield(component, "nominal_value")
    value = componentValueText(component.nominal_value, unit);
end
value = strtrim(string(value));
unit = strtrim(string(unit));
if strlength(value) > 0 && value ~= "[]" && lower(value) ~= "unspecified"
    text = id + labelSuffix(label, id) + " = " + value;
elseif strlength(unit) > 0
    text = id + labelSuffix(label, id) + " uses " + unit + " units";
else
    text = id + labelSuffix(label, id) + " is parameterized";
end
end

function text = componentValueText(value, unit)
unit = strtrim(string(unit));
if isnumeric(value) && isscalar(value) && isfinite(value)
    text = engineeringValueText(double(value), unit);
    return
end
text = strtrim(valueToText(value));
if strlength(text) == 0 || text == "[]" || lower(text) == "unspecified"
    return
end
if strlength(unit) > 0 && ~contains(lower(text), lower(unit))
    text = text + " " + unit;
end
end

function text = engineeringValueText(value, unit)
unit = strtrim(string(unit));
unitLower = lower(unit);
switch unitLower
    case {"ohm", "ohms", "ω"}
        text = scaledValueText(value, [1e9, 1e6, 1e3, 1], ["GOhm", "MOhm", "kOhm", "Ohm"]);
    case {"f", "farad", "farads"}
        text = scaledValueText(value, [1, 1e-3, 1e-6, 1e-9, 1e-12], ["F", "mF", "uF", "nF", "pF"]);
    case {"a", "amp", "amps", "ampere", "amperes"}
        text = scaledValueText(value, [1, 1e-3, 1e-6, 1e-9, 1e-12], ["A", "mA", "uA", "nA", "pA"]);
    case {"v", "volt", "volts"}
        text = scaledValueText(value, [1, 1e-3, 1e-6], ["V", "mV", "uV"]);
    case {"s", "sec", "second", "seconds"}
        text = scaledValueText(value, [1, 1e-3, 1e-6], ["s", "ms", "us"]);
    otherwise
        text = numberText(value) + unitSuffix(unit);
end
end

function text = scaledValueText(value, scales, units)
absValue = abs(value);
scale = scales(end);
unit = units(end);
for i = 1:numel(scales)
    if absValue >= scales(i) || i == numel(scales)
        scale = scales(i);
        unit = units(i);
        break
    end
end
text = numberText(value / scale) + " " + unit;
end

function text = numberText(value)
text = string(sprintf("%.6g", value));
end

function text = labelSuffix(label, id)
label = strtrim(string(label));
id = strtrim(string(id));
if strlength(label) == 0 || lower(label) == lower(id)
    text = "";
else
    text = " (" + label + ")";
end
end

function text = unitSuffix(unit)
if strlength(strtrim(string(unit))) == 0
    text = "";
else
    text = " " + string(unit);
end
end

function text = prettifyFieldName(name)
text = replace(string(name), "_", " ");
text = regexprep(text, "\bhz\b", "Hz", "ignorecase");
end

function text = prettifyBlockName(name)
text = string(name);
text = regexprep(text, "([0-9])MOhm", "$1 MOhm");
text = regexprep(text, "([0-9])kOhm", "$1 kOhm");
text = regexprep(text, "([0-9])mV", "$1 mV");
text = regexprep(text, "([0-9])uF", "$1 uF");
text = regexprep(text, "([0-9])nF", "$1 nF");
text = regexprep(text, "([0-9])pF", "$1 pF");
text = replace(text, "_", " ");
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
