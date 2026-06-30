function result = exportLearningObjectives(context, options)
%EXPORTLEARNINGOBJECTIVES Export CiTT learning objectives as YAML fallback.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

trace = [];
if isstruct(context) && isfield(context, "LastLearningTraceability")
    trace = context.LastLearningTraceability;
end
if isempty(trace)
    trace = feval('citt.buildLearningTraceability', context);
end

yamlPath = optionString(options, "YamlPath", config.LearningObjectivesYamlPath);
slreqxPath = optionString(options, "SlreqxPath", config.LearningObjectivesSlreqxPath);
yamlText = renderYaml(trace);
writeText(yamlPath, yamlText);

result = struct();
result.success = true;
result.created_at = string(datetime("now"));
result.yaml_path = string(yamlPath);
result.slreqx_path = string(slreqxPath);
result.slreqx_created = false;
result.messages = "YAML learning-objective traceability exported. Requirements Toolbox .slreqx export is reserved for reviewed human-curated objective sets.";
end

function text = renderYaml(trace)
lines = [
    "objectives:"
];
if ~isstruct(trace) || ~isfield(trace, "objectives") || isempty(trace.objectives)
    lines(end + 1) = "  []";
    text = strjoin(lines, newline);
    return
end
for i = 1:numel(trace.objectives)
    objective = trace.objectives(i);
    lines = [lines; ...
        "  - id: " + yamlScalar(fieldText(objective, "learning_objective_id")); ...
        "    status: Draft"; ...
        "    keywords: [draft, citt, learning-objective]"; ...
        "    summary: " + yamlScalar(fieldText(objective, "title")); ...
        "    focus_id: " + yamlScalar(fieldText(objective, "focus_id")); ...
        "    model_links:"; ...
        yamlList(unique([stringList(getField(objective, "model_paths")); stringList(getField(objective, "block_paths"))], "stable")); ...
        "    probe_links:"; ...
        yamlList(stringList(getField(objective, "probe_ids")))]; %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function lines = yamlList(values)
values = string(values(:));
values = values(strlength(strtrim(values)) > 0);
if isempty(values)
    lines = "      []";
    return
end
lines = strings(numel(values), 1);
for i = 1:numel(values)
    lines(i) = "      - " + yamlScalar(values(i));
end
end

function text = yamlScalar(value)
raw = char(string(value));
raw = strrep(raw, '\', '\\');
raw = strrep(raw, '"', '\"');
text = """" + string(raw) + """";
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function value = getField(container, name)
if isstruct(container) && ~isempty(container) && isfield(container, char(name))
    value = container.(char(name));
else
    value = [];
end
end

function text = fieldText(container, name)
text = "";
if isstruct(container) && ~isempty(container) && isfield(container, char(name))
    text = valueText(container.(char(name)));
end
end

function values = stringList(value)
if isempty(value)
    values = strings(0, 1);
elseif isstring(value)
    values = value(:);
elseif ischar(value)
    values = string(value);
elseif iscell(value)
    values = strings(0, 1);
    for i = 1:numel(value)
        values = [values; stringList(value{i})]; %#ok<AGROW>
    end
elseif isnumeric(value) || islogical(value)
    values = string(value(:));
else
    values = string(value);
end
values = values(strlength(strtrim(values)) > 0);
end

function text = valueText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif isnumeric(value) || islogical(value)
    text = string(value);
else
    text = string(feval('citt.util.jsonEncode', value));
end
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
