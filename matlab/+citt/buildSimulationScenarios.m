function scenarioSpec = buildSimulationScenarios(context, options)
%BUILDSIMULATIONSCENARIOS Build CiTT SimulationInput scenario specifications.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
outputPath = optionString(options, "OutputPath", config.SimulationScenarioSpecPath);
spec = readSpec(context);

scenarios = struct("id", {}, "type", {}, "stop_time", {}, "variables", {}, "learning_objective_id", {}, "csv_path", {});
scenarios(end + 1) = scenario("nominal", "nominal", optionNumber(options, "StopTime", 2.0), struct(), "", "");

[~, capId] = firstComponentValue(spec, ["capacitor", "capacitance", "c"], "f");
if strlength(capId) > 0
    vars = struct();
    vars.(matlab.lang.makeValidName(char(capId + "_value"))) = "100e-6";
    scenarios(end + 1) = scenario("wrong_component_unit_" + matlab.lang.makeValidName(char(capId)), ...
        "wrong_component_unit", 2.0, vars, "LO_wrong_unit", "");
end

scenarios(end + 1) = scenario("parameter_sweep_rc_nominal", "parameter_sweep", 2.0, struct(), "LO_parameter_sensitivity", "");

if strlength(strtrim(string(context.LabCsvPath))) > 0
    scenarios(end + 1) = scenario("lab_replay", "lab_replay", 5.0, struct(), "LO_lab_replay", context.LabCsvPath);
end

scenarioSpec = struct();
scenarioSpec.success = true;
scenarioSpec.created_at = string(datetime("now"));
scenarioSpec.source_spec = string(context.SpecPath);
scenarioSpec.model_path = string(context.ModelPath);
scenarioSpec.scenarios = scenarios;
scenarioSpec.spec_path = string(outputPath);

writeJson(outputPath, scenarioSpec);
end

function context = normalizeContext(context, config)
defaults = struct();
defaults.Spec = [];
defaults.SpecPath = config.LastSpecPath;
defaults.ModelPath = config.GeneratedModelPath;
defaults.LabCsvPath = "";
names = fieldnames(defaults);
for i = 1:numel(names)
    name = names{i};
    if ~isfield(context, name)
        context.(name) = defaults.(name);
    end
end
end

function item = scenario(id, type, stopTime, variables, objectiveId, csvPath)
item = struct();
item.id = string(id);
item.type = string(type);
item.stop_time = double(stopTime);
item.variables = variables;
item.learning_objective_id = string(objectiveId);
item.csv_path = string(csvPath);
end

function spec = readSpec(context)
if isstruct(context.Spec) && ~isempty(context.Spec)
    spec = context.Spec;
    return
end
spec = [];
path = string(context.SpecPath);
if exist(path, "file") == 2
    try
        spec = jsondecode(fileread(path));
    catch
        spec = [];
    end
end
end

function [value, id] = firstComponentValue(spec, typeHints, unitFamily)
value = [];
id = "";
components = getField(spec, "components");
if isempty(components)
    return
end
for i = 1:numel(components)
    component = components(i);
    text = lower(valueText(component));
    if any(contains(text, lower(string(typeHints))))
        id = firstFieldText(component, ["id"], "component_" + string(i));
        raw = getFirstField(component, ["value", "nominal_value", "resistance", "capacitance"]);
        value = parseSi(raw, unitFamily);
        return
    end
end
end

function value = parseSi(raw, unitFamily)
value = [];
text = lower(strtrim(valueText(raw)));
tokens = regexp(char(text), '([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zµ]*)', 'tokens', 'once');
if isempty(tokens)
    return
end
base = str2double(tokens{1});
suffix = replace(string(tokens{2}), "µ", "u");
factor = 1;
if startsWith(suffix, "meg")
    factor = 1e6;
elseif startsWith(suffix, "k")
    factor = 1e3;
elseif startsWith(suffix, "m") && unitFamily ~= "f"
    factor = 1e-3;
elseif startsWith(suffix, "u")
    factor = 1e-6;
elseif startsWith(suffix, "n")
    factor = 1e-9;
elseif startsWith(suffix, "p")
    factor = 1e-12;
end
if unitFamily == "f" && startsWith(suffix, "m")
    factor = 1e-3;
end
value = base * factor;
end

function value = getField(container, name)
if isstruct(container) && isfield(container, char(name))
    value = container.(char(name));
else
    value = [];
end
end

function value = getFirstField(container, names)
value = [];
for i = 1:numel(names)
    name = char(names(i));
    if isstruct(container) && isfield(container, name)
        value = container.(name);
        return
    end
end
end

function text = firstFieldText(container, names, defaultValue)
text = string(defaultValue);
for i = 1:numel(names)
    name = char(names(i));
    if isstruct(container) && isfield(container, name)
        text = valueText(container.(name));
        return
    end
end
end

function text = valueText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', " ");
elseif ischar(value)
    text = string(value);
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueText(value{i});
    end
    text = strjoin(parts, " ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
elseif isnumeric(value) || islogical(value)
    text = string(mat2str(value));
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

function value = optionNumber(options, fieldName, defaultValue)
value = defaultValue;
if isstruct(options) && isfield(options, fieldName)
    raw = options.(fieldName);
    if isnumeric(raw) && isscalar(raw)
        value = double(raw);
    else
        parsed = str2double(string(raw));
        if ~isnan(parsed)
            value = parsed;
        end
    end
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
