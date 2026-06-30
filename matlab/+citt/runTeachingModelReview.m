function report = runTeachingModelReview(context, options)
%RUNTEACHINGMODELREVIEW Review teaching artifact health for a CiTT model.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.TeachingReviewReportPath);
markdownPath = optionString(options, "MarkdownPath", config.TeachingReviewMarkdownPath);

spec = readJson(context.SpecPath);
focusItems = unwrapItems(readJson(context.FocusMapPath), ["focus_map", "items"]);
probeItems = unwrapItems(readJson(context.ProbeMapPath), ["probe_map", "probes", "items"]);
modelInfo = inspectModel(context.ModelPath);

checks = [
    checkRow("CITT_CHECK_001", "Simscape physical network exists", ...
        statusFromCount(modelInfo.simscape_block_count, modelInfo.inspectable), ...
        string(modelInfo.simscape_block_count) + " Simscape-like block(s) detected")
    checkRow("CITT_CHECK_002", "Solver Configuration exists", ...
        statusFromFlag(modelInfo.solver_configuration_count > 0, modelInfo.inspectable), ...
        string(modelInfo.solver_configuration_count) + " Solver Configuration block(s) detected")
    checkRow("CITT_CHECK_003", "Electrical Reference exists", ...
        statusFromFlag(modelInfo.electrical_reference_count > 0, modelInfo.inspectable), ...
        string(modelInfo.electrical_reference_count) + " Electrical Reference block(s) detected")
    checkRequestedOutputs(spec, probeItems)
    checkMapPaths("CITT_CHECK_005", "Focus map block paths exist", focusItems, modelInfo)
    checkMapPaths("CITT_CHECK_006", "Probe map block paths exist", probeItems, modelInfo)
    checkFocusProbeCoverage(focusItems, probeItems)
    checkModelTestInterface(modelInfo)
];

summary = summarizeChecks(checks);
report = struct();
report.success = summary.fail == 0;
report.created_at = string(datetime("now"));
report.model_path = string(context.ModelPath);
report.spec_path = string(context.SpecPath);
report.focus_map_path = string(context.FocusMapPath);
report.probe_map_path = string(context.ProbeMapPath);
report.checks = checks;
report.summary = summary;
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);
report.model_inspection = modelInfo;

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function context = normalizeContext(context, config)
if ~isfield(context, "ModelPath") || strlength(strtrim(string(context.ModelPath))) == 0
    context.ModelPath = config.GeneratedModelPath;
end
if ~isfield(context, "SpecPath") || strlength(strtrim(string(context.SpecPath))) == 0
    context.SpecPath = config.LastSpecPath;
end
if ~isfield(context, "FocusMapPath") || strlength(strtrim(string(context.FocusMapPath))) == 0
    context.FocusMapPath = config.FocusMapPath;
end
if ~isfield(context, "ProbeMapPath") || strlength(strtrim(string(context.ProbeMapPath))) == 0
    context.ProbeMapPath = config.ProbeMapPath;
end
end

function info = inspectModel(modelPath)
info = struct();
info.inspectable = false;
info.model_exists = exist(modelPath, "file") == 2 || exist(modelPath, "file") == 4;
info.model_name = "";
info.error = "";
info.simscape_block_count = 0;
info.solver_configuration_count = 0;
info.electrical_reference_count = 0;
info.test_interface_exists = false;
info.block_paths = strings(0, 1);

if ~info.model_exists
    info.error = "Model file is missing.";
    return
end
if exist("load_system", "file") ~= 2 && exist("load_system", "builtin") ~= 5
    info.error = "Simulink model inspection is unavailable in this MATLAB session.";
    return
end

try
    opened = feval('citt.openOrCreateModel', modelPath);
    modelName = char(opened.model_name);
    info.model_name = string(modelName);
    blocks = find_system(modelName, "LookUnderMasks", "all", "FollowLinks", "on", "Type", "Block");
    info.block_paths = string(blocks(:));
    refs = strings(numel(blocks), 1);
    masks = strings(numel(blocks), 1);
    for i = 1:numel(blocks)
        refs(i) = safeGetParam(blocks{i}, "ReferenceBlock");
        masks(i) = safeGetParam(blocks{i}, "MaskType");
    end
    combined = lower(refs + " " + masks + " " + string(blocks(:)));
    info.simscape_block_count = sum(contains(combined, "simscape") | contains(combined, "foundation library") | contains(combined, "electrical"));
    info.solver_configuration_count = sum(contains(combined, "solver configuration"));
    info.electrical_reference_count = sum(contains(combined, "electrical reference"));
    info.test_interface_exists = any(info.block_paths == string(modelName) + "/CiTT_TestInterface");
    info.inspectable = true;
catch inspectError
    info.error = string(inspectError.message);
end
end

function value = safeGetParam(blockPath, paramName)
try
    value = string(get_param(blockPath, paramName));
catch
    value = "";
end
end

function row = checkRequestedOutputs(spec, probeItems)
requested = stringList(getField(spec, "requested_outputs"));
if isempty(requested)
    row = checkRow("CITT_CHECK_004", "Every requested output has a probe map entry", ...
        "WARN", "No requested_outputs field was available to cross-check.");
elseif isempty(probeItems)
    row = checkRow("CITT_CHECK_004", "Every requested output has a probe map entry", ...
        "FAIL", string(numel(requested)) + " requested output(s), but no probe map entries.");
else
    row = checkRow("CITT_CHECK_004", "Every requested output has a probe map entry", ...
        "PASS", string(numel(requested)) + " requested output(s), " + string(numel(probeItems)) + " probe map item(s).");
end
row.teaching_requirement = "Probe coverage for requested outputs";
end

function row = checkMapPaths(id, title, items, modelInfo)
paths = collectPaths(items);
if isempty(paths)
    row = checkRow(id, title, "WARN", "No block_paths/model_paths were found in the map.");
    row.missing = strings(0, 1);
    return
end
if ~modelInfo.inspectable
    row = checkRow(id, title, "WARN", "Model paths were recorded but the model could not be inspected: " + modelInfo.error);
    row.missing = strings(0, 1);
    return
end
missing = paths(~ismember(paths, modelInfo.block_paths));
if isempty(missing)
    row = checkRow(id, title, "PASS", string(numel(paths)) + " mapped path(s) exist.");
else
    row = checkRow(id, title, "FAIL", string(numel(missing)) + " mapped path(s) were missing.");
end
row.missing = missing;
end

function row = checkFocusProbeCoverage(focusItems, probeItems)
focusIds = idsFromItems(focusItems, ["focus_id", "id"]);
probeFocusIds = idsFromItems(probeItems, ["focus_id"]);
if isempty(focusIds)
    row = checkRow("CITT_CHECK_007", "Every teaching focus has a measurable evidence path", ...
        "WARN", "No focus map entries were available.");
elseif isempty(probeItems)
    row = checkRow("CITT_CHECK_007", "Every teaching focus has a measurable evidence path", ...
        "FAIL", "Focus map exists but probe map is empty.");
elseif isempty(probeFocusIds)
    row = checkRow("CITT_CHECK_007", "Every teaching focus has a measurable evidence path", ...
        "WARN", "Probe entries exist but do not declare focus_id links.");
else
    missing = focusIds(~ismember(focusIds, probeFocusIds));
    if isempty(missing)
        row = checkRow("CITT_CHECK_007", "Every teaching focus has a measurable evidence path", ...
            "PASS", string(numel(focusIds)) + " focus item(s) have probe links.");
    else
        row = checkRow("CITT_CHECK_007", "Every teaching focus has a measurable evidence path", ...
            "FAIL", "Missing probe focus links: " + strjoin(missing, ", "));
    end
end
row.teaching_requirement = "Focus-to-probe evidence coverage";
end

function row = checkModelTestInterface(modelInfo)
if ~modelInfo.inspectable
    row = checkRow("CITT_CHECK_008", "Generated model has signal-level test interface if model_test is required", ...
        "WARN", "Model could not be inspected: " + modelInfo.error);
elseif modelInfo.test_interface_exists
    row = checkRow("CITT_CHECK_008", "Generated model has signal-level test interface if model_test is required", ...
        "PASS", "CiTT_TestInterface subsystem exists.");
else
    row = checkRow("CITT_CHECK_008", "Generated model has signal-level test interface if model_test is required", ...
        "WARN", "CiTT_TestInterface was not found; SATK model_test should target another signal-based wrapper or report the limitation.");
end
row.teaching_requirement = "SATK model_test signal-based wrapper";
end

function row = checkRow(id, title, status, evidence)
row = struct();
row.id = string(id);
row.title = string(title);
row.teaching_requirement = string(title);
row.status = string(status);
row.evidence = string(evidence);
row.recommended_fix = recommendedFix(row.id, row.status);
row.missing = strings(0, 1);
end

function text = recommendedFix(id, status)
if status == "PASS"
    text = "No action needed.";
    return
end
switch string(id)
    case "CITT_CHECK_001"
        text = "Build the circuit with Simscape/Simscape Electrical physical blocks, not a pure signal-flow substitute.";
    case "CITT_CHECK_002"
        text = "Add a Solver Configuration block to every Simscape physical network.";
    case "CITT_CHECK_003"
        text = "Add an Electrical Reference block to the electrical network.";
    case "CITT_CHECK_004"
        text = "Add probe map entries for each requested output.";
    case {"CITT_CHECK_005", "CITT_CHECK_006"}
        text = "Regenerate the focus/probe map with valid model block paths.";
    case "CITT_CHECK_007"
        text = "Link each focus_id to at least one probe or logged measurement path.";
    case "CITT_CHECK_008"
        text = "Add CiTT_TestInterface or document a signal-based wrapper for SATK model_test.";
    otherwise
        text = "Review the generated model and teaching artifacts.";
end
end

function status = statusFromCount(count, inspectable)
if ~inspectable
    status = "WARN";
elseif count > 0
    status = "PASS";
else
    status = "FAIL";
end
end

function status = statusFromFlag(flag, inspectable)
if ~inspectable
    status = "WARN";
elseif flag
    status = "PASS";
else
    status = "FAIL";
end
end

function summary = summarizeChecks(checks)
statuses = string({checks.status});
summary = struct();
summary.pass = sum(statuses == "PASS");
summary.warn = sum(statuses == "WARN");
summary.fail = sum(statuses == "FAIL");
summary.not_run = sum(statuses == "NOT_RUN");
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Teaching Model Review"
    ""
    "Created: " + report.created_at
    "Model: " + report.model_path
    ""
    "| Check | Teaching requirement | Status | Evidence | Recommended fix |"
    "| --- | --- | --- | --- | --- |"
];
for i = 1:numel(report.checks)
    row = report.checks(i);
    lines(end + 1) = "| " + md(row.id + " " + row.title) + " | " + md(row.teaching_requirement) + ...
        " | " + md(row.status) + " | " + md(row.evidence) + " | " + md(row.recommended_fix) + " |"; %#ok<AGROW>
end
lines = [lines; ""; "Summary: PASS=" + string(report.summary.pass) + ...
    ", WARN=" + string(report.summary.warn) + ", FAIL=" + string(report.summary.fail)];
text = strjoin(lines, newline);
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

function value = getField(container, name)
if isstruct(container) && ~isempty(container) && isfield(container, char(name))
    value = container.(char(name));
else
    value = [];
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

function paths = collectPaths(items)
paths = strings(0, 1);
for i = 1:numel(items)
    paths = [paths; stringList(getField(items(i), "block_paths")); stringList(getField(items(i), "model_paths")); stringList(getField(items(i), "target_paths"))]; %#ok<AGROW>
end
paths = unique(paths(strlength(strtrim(paths)) > 0), "stable");
end

function ids = idsFromItems(items, fieldNames)
ids = strings(0, 1);
for i = 1:numel(items)
    for k = 1:numel(fieldNames)
        values = stringList(getField(items(i), fieldNames(k)));
        if ~isempty(values)
            ids(end + 1, 1) = values(1); %#ok<AGROW>
            break
        end
    end
end
ids = unique(ids(strlength(strtrim(ids)) > 0), "stable");
end

function text = md(value)
text = replace(string(value), "|", "\|");
text = replace(text, newline, "<br>");
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
