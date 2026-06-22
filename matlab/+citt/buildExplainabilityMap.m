function report = buildExplainabilityMap(context, options)
%BUILDEXPLAINABILITYMAP Build focus/probe highlight actions from saved maps.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.ExplainabilityMapPath);
markdownPath = optionString(options, "MarkdownPath", config.ExplainabilityMarkdownPath);

spec = readJsonOrStruct(context.Spec, context.SpecPath);
focusItems = unwrapItems(readJsonOrStruct([], context.FocusMapPath), "focus_map");
probeItems = unwrapItems(readJsonOrStruct([], context.ProbeMapPath), "probe_map");

actions = struct("action_id", {}, "action_type", {}, "label", {}, "focus_id", {}, ...
    "target_paths", {}, "reason", {}, "status", {});
for i = 1:numel(focusItems)
    item = focusItems(i);
    focusId = firstFieldText(item, ["focus_id", "id"], "focus_" + string(i));
    label = firstFieldText(item, ["label", "name"], focusId);
    actionType = classifyAction(label + " " + firstFieldText(item, ["explanation", "teaching_question"], ""));
    actions(end + 1) = actionRow("focus_" + safeId(focusId), actionType, label, focusId, ...
        focusPaths(item), firstFieldText(item, ["teaching_question", "explanation"], ""), "READY"); %#ok<AGROW>
end

for i = 1:numel(probeItems)
    item = probeItems(i);
    probeId = firstFieldText(item, ["probe_id", "id"], "probe_" + string(i));
    focusId = firstFieldText(item, ["focus_id"], "");
    label = firstFieldText(item, ["label", "quantity"], probeId);
    actions(end + 1) = actionRow("probe_" + safeId(probeId), "probe_location", label, focusId, ...
        focusPaths(item), firstFieldText(item, ["instructions", "suggested_sensor_or_logging"], ""), "READY"); %#ok<AGROW>
end

specText = lower(valueText(spec));
if contains(specText, "feedback")
    actions(end + 1) = actionRow("concept_feedback_loop", "feedback_loop", "Feedback loop", "", strings(0, 1), ...
        "Focus the summing/comparator path and return path when present in the generated focus map.", "CONCEPTUAL"); %#ok<AGROW>
end
if contains(specText, "alias") || contains(specText, "adc") || contains(specText, "sampling")
    actions(end + 1) = actionRow("concept_aliasing_path", "aliasing_path", "Aliasing path", "", strings(0, 1), ...
        "Connect analog bandwidth, sampling rate, and ADC output in the teaching explanation.", "CONCEPTUAL"); %#ok<AGROW>
end
if contains(specText, "saturation") || contains(specText, "op-amp") || contains(specText, "opamp")
    actions(end + 1) = actionRow("concept_saturation_source", "saturation_source", "Saturation source", "", strings(0, 1), ...
        "Highlight active-stage output limits and compare expected output swing to rail assumptions.", "CONCEPTUAL"); %#ok<AGROW>
end

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.actions = actions;
report.focus_map_path = string(context.FocusMapPath);
report.probe_map_path = string(context.ProbeMapPath);
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function context = normalizeContext(context, config)
defaults = struct("Spec", [], "SpecPath", config.LastSpecPath, ...
    "FocusMapPath", config.FocusMapPath, "ProbeMapPath", config.ProbeMapPath);
names = fieldnames(defaults);
for i = 1:numel(names)
    if ~isfield(context, names{i})
        context.(names{i}) = defaults.(names{i});
    end
end
end

function value = readJsonOrStruct(value, path)
if isstruct(value) && ~isempty(value)
    return
end
value = [];
path = string(path);
if strlength(path) > 0 && exist(path, "file") == 2
    try
        value = jsondecode(fileread(path));
    catch
        value = [];
    end
end
end

function items = unwrapItems(value, preferredField)
if ~isstruct(value) || isempty(value)
    items = struct([]);
elseif isfield(value, preferredField)
    items = value.(char(preferredField));
elseif isfield(value, "items")
    items = value.items;
else
    items = value;
end
if ~isstruct(items)
    items = struct([]);
end
end

function row = actionRow(actionId, actionType, label, focusId, targetPaths, reason, status)
row = struct();
row.action_id = string(actionId);
row.action_type = string(actionType);
row.label = string(label);
row.focus_id = string(focusId);
row.target_paths = string(targetPaths(:)');
row.reason = string(reason);
row.status = string(status);
end

function actionType = classifyAction(text)
text = lower(string(text));
if contains(text, "feedback")
    actionType = "feedback_loop";
elseif contains(text, "input")
    actionType = "input_path";
elseif contains(text, "output")
    actionType = "output_path";
elseif contains(text, "saturation") || contains(text, "clip")
    actionType = "saturation_source";
elseif contains(text, "alias") || contains(text, "sample") || contains(text, "adc")
    actionType = "aliasing_path";
else
    actionType = "signal_path";
end
end

function paths = focusPaths(item)
paths = strings(0, 1);
paths = appendPaths(paths, item, "block_paths");
paths = appendPaths(paths, item, "model_paths");
paths = appendPaths(paths, item, "target_paths");
paths = unique(paths(strlength(paths) > 0), "stable");
end

function paths = appendPaths(paths, item, fieldName)
if isstruct(item) && isfield(item, fieldName)
    value = item.(fieldName);
    paths = [paths; string(value(:))]; %#ok<AGROW>
end
end

function text = firstFieldText(item, names, defaultValue)
text = string(defaultValue);
for i = 1:numel(names)
    name = char(names(i));
    if isstruct(item) && isfield(item, name)
        text = valueText(item.(name));
        return
    end
end
end

function id = safeId(value)
id = regexprep(char(string(value)), '[^A-Za-z0-9_]+', '_');
if isempty(id)
    id = "item";
end
id = string(id);
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
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

function text = renderMarkdown(report)
lines = [
    "# CiTT Explainability Map"
    ""
    "Created: " + report.created_at
    ""
    "| Action | Type | Focus | Targets | Status |"
    "| --- | --- | --- | --- | --- |"
];
for i = 1:numel(report.actions)
    a = report.actions(i);
    lines(end + 1) = "| " + md(a.label) + " | " + md(a.action_type) + " | " + ...
        md(a.focus_id) + " | " + md(strjoin(a.target_paths, ", ")) + " | " + md(a.status) + " |"; %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function text = md(value)
text = replace(string(value), "|", "\|");
text = replace(text, newline, "<br>");
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end
