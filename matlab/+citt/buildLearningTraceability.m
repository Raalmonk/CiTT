function report = buildLearningTraceability(context, options)
%BUILDLEARNINGTRACEABILITY Link learning objectives to model/test evidence.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.LearningTraceabilityPath);
markdownPath = optionString(options, "MarkdownPath", config.LearningTraceabilityMarkdownPath);

spec = readJson(context.SpecPath);
focusItems = unwrapItems(readJson(context.FocusMapPath), ["focus_map", "items"]);
probeItems = unwrapItems(readJson(context.ProbeMapPath), ["probe_map", "probes", "items"]);
teachingPlan = context.TeachingPlan;
if isempty(teachingPlan) && exist(config.TeachingPlanPath, "file") == 2
    teachingPlan = readJson(config.TeachingPlanPath);
end
modelTests = context.LastModelTests;
if isempty(modelTests)
    modelTests = feval('citt.loadModelTestReport', config.ModelTestReportPath);
end
assessment = context.LastAssessment;
if isempty(assessment)
    assessment = readJson(config.AssessmentReportPath);
end

objectives = buildObjectives(focusItems, probeItems, teachingPlan, modelTests, assessment, config);
if isempty(objectives)
    objectives = fallbackObjective(spec, probeItems, modelTests, assessment, config);
end

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.source_spec = string(context.SpecPath);
report.focus_map_path = string(context.FocusMapPath);
report.probe_map_path = string(context.ProbeMapPath);
report.model_test_report_path = string(config.ModelTestReportPath);
report.assessment_report_path = string(config.AssessmentReportPath);
report.objectives = objectives;
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function context = normalizeContext(context, config)
defaults = struct();
defaults.SpecPath = config.LastSpecPath;
defaults.FocusMapPath = config.FocusMapPath;
defaults.ProbeMapPath = config.ProbeMapPath;
defaults.TeachingPlan = [];
defaults.LastModelTests = [];
defaults.LastProbe = [];
defaults.LastAssessment = [];
names = fieldnames(defaults);
for i = 1:numel(names)
    name = names{i};
    if ~isfield(context, name)
        context.(name) = defaults.(name);
    end
end
end

function objectives = buildObjectives(focusItems, probeItems, teachingPlan, modelTests, assessment, config)
objectives = repmat(emptyObjective(), 0, 1);
for i = 1:numel(focusItems)
    focus = focusItems(i);
    focusId = firstNonempty(firstFieldText(focus, ["focus_id", "id"], ""), "focus_" + string(i));
    probeIds = matchingProbeIds(probeItems, focusId);
    objective = baseObjective(i, focusId, focus, probeIds, teachingPlan, modelTests, assessment, config);
    objectives(end + 1) = objective; %#ok<AGROW>
end
end

function objective = fallbackObjective(spec, probeItems, modelTests, assessment, config)
title = firstNonempty(firstFieldText(spec, ["likely_analysis", "circuit_type"], ""), "CiTT generated circuit lesson");
objective = emptyObjective();
objective.learning_objective_id = "LO_001";
objective.title = "Explain " + title;
objective.focus_id = "general_model_behavior";
objective.teaching_step_id = "";
objective.model_paths = strings(0, 1);
objective.block_paths = strings(0, 1);
objective.probe_ids = idsFromItems(probeItems, ["probe_id", "id"]);
objective.model_test_scenarios = modelTestScenarios(modelTests, "general_model_behavior");
objective.simulation_evidence = simulationEvidence(config);
objective.student_evidence = studentEvidence(assessment);
objective.mastery_status = masteryStatus(assessment);
end

function objective = baseObjective(index, focusId, focus, probeIds, teachingPlan, modelTests, assessment, config)
objective = emptyObjective();
objective.learning_objective_id = "LO_" + compose("%03d", index);
objective.title = firstNonempty( ...
    firstFieldText(focus, ["learning_objective", "teaching_question", "label", "explanation"], ""), ...
    "Explain " + focusId);
objective.focus_id = focusId;
objective.teaching_step_id = teachingStepId(teachingPlan, focusId);
objective.model_paths = unique([stringList(getField(focus, "model_paths")); stringList(getField(focus, "stateflow_paths"))], "stable");
objective.block_paths = unique(stringList(getField(focus, "block_paths")), "stable");
objective.probe_ids = probeIds;
objective.model_test_scenarios = modelTestScenarios(modelTests, focusId);
objective.simulation_evidence = simulationEvidence(config);
objective.student_evidence = studentEvidence(assessment);
objective.mastery_status = masteryStatus(assessment);
end

function objective = emptyObjective()
objective = struct();
objective.learning_objective_id = "";
objective.title = "";
objective.focus_id = "";
objective.teaching_step_id = "";
objective.model_paths = strings(0, 1);
objective.block_paths = strings(0, 1);
objective.probe_ids = strings(0, 1);
objective.model_test_scenarios = strings(0, 1);
objective.simulation_evidence = strings(0, 1);
objective.student_evidence = struct("hint_levels_used", 0, "classification", "", "assessment_report", "");
objective.mastery_status = "";
end

function stepId = teachingStepId(teachingPlan, focusId)
stepId = "";
if ~isstruct(teachingPlan) || ~isfield(teachingPlan, "steps")
    return
end
steps = teachingPlan.steps;
for i = 1:numel(steps)
    if firstFieldText(steps(i), ["focus_id"], "") == focusId
        stepId = firstNonempty(firstFieldText(steps(i), ["step_id", "id"], ""), "step_" + string(i));
        return
    end
end
end

function probeIds = matchingProbeIds(probeItems, focusId)
probeIds = strings(0, 1);
for i = 1:numel(probeItems)
    itemFocus = firstFieldText(probeItems(i), ["focus_id"], "");
    if strlength(itemFocus) == 0 || itemFocus == focusId
        id = firstFieldText(probeItems(i), ["probe_id", "id"], "");
        if strlength(id) > 0
            probeIds(end + 1, 1) = id; %#ok<AGROW>
        end
    end
end
probeIds = unique(probeIds, "stable");
end

function scenarios = modelTestScenarios(modelTests, focusId)
scenarios = strings(0, 1);
if ~isstruct(modelTests) || ~isfield(modelTests, "scenarios")
    config = feval('citt.loadConfig');
    manifest = readJson(config.ModelTestManifestPath);
    if isstruct(manifest) && isfield(manifest, "tests")
        scenarios = scenarioNamesFromTests(manifest.tests, focusId);
    end
    return
end
scenarios = scenarioNamesFromTests(modelTests.scenarios, focusId);
end

function scenarios = scenarioNamesFromTests(tests, focusId)
scenarios = strings(0, 1);
if ~isstruct(tests)
    return
end
for i = 1:numel(tests)
    testFocus = firstFieldText(tests(i), ["focus_id"], "");
    if strlength(testFocus) == 0 || testFocus == focusId
        name = firstNonempty(firstFieldText(tests(i), ["scenario_id"], ""), firstFieldText(tests(i), ["scenario", "name"], ""));
        if strlength(name) > 0
            scenarios(end + 1, 1) = name; %#ok<AGROW>
        end
    end
end
scenarios = unique(scenarios, "stable");
end

function paths = simulationEvidence(config)
candidatePaths = [
    config.SimulationSummaryPath
    config.BodeReportPath
    config.SimulationScenarioReportPath
];
paths = strings(0, 1);
for i = 1:numel(candidatePaths)
    if exist(candidatePaths(i), "file") == 2
        paths(end + 1, 1) = candidatePaths(i); %#ok<AGROW>
    end
end
end

function evidence = studentEvidence(assessment)
evidence = struct();
evidence.hint_levels_used = numericField(assessment, "hint_levels_used", 0);
evidence.classification = firstFieldText(assessment, ["classification", "student_level"], "");
config = feval('citt.loadConfig');
evidence.assessment_report = config.AssessmentReportPath;
end

function status = masteryStatus(assessment)
status = firstFieldText(assessment, ["mastery_status", "classification", "student_level"], "RECORDED");
if strlength(status) == 0
    status = "RECORDED";
end
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Learning Objective Traceability"
    ""
    "Created: " + report.created_at
    "Source spec: " + report.source_spec
    ""
    "| Learning objective | Focus | Model evidence | Probe evidence | Test evidence | Simulation evidence | Student evidence | Mastery |"
    "| --- | --- | --- | --- | --- | --- | --- | --- |"
];
for i = 1:numel(report.objectives)
    o = report.objectives(i);
    lines(end + 1) = "| " + md(o.learning_objective_id + ": " + o.title) + ...
        " | " + md(o.focus_id) + ...
        " | " + md(strjoin(unique([string(o.model_paths(:)); string(o.block_paths(:))], "stable"), "<br>")) + ...
        " | " + md(strjoin(string(o.probe_ids(:)), "<br>")) + ...
        " | " + md(strjoin(string(o.model_test_scenarios(:)), "<br>")) + ...
        " | " + md(strjoin(string(o.simulation_evidence(:)), "<br>")) + ...
        " | " + md(studentEvidenceText(o.student_evidence)) + ...
        " | " + md(o.mastery_status) + " |"; %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function text = studentEvidenceText(value)
if ~isstruct(value)
    text = "";
    return
end
parts = [
    "hints=" + string(numericField(value, "hint_levels_used", 0))
    "classification=" + firstFieldText(value, ["classification"], "")
];
text = strjoin(parts(strlength(strtrim(parts)) > 0), "<br>");
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
elseif isstruct(value)
    values = string(feval('citt.util.jsonEncode', value));
else
    values = string(value);
end
values = values(strlength(strtrim(values)) > 0);
end

function ids = idsFromItems(items, fieldNames)
ids = strings(0, 1);
for i = 1:numel(items)
    for k = 1:numel(fieldNames)
        id = firstFieldText(items(i), fieldNames(k), "");
        if strlength(id) > 0
            ids(end + 1, 1) = id; %#ok<AGROW>
            break
        end
    end
end
ids = unique(ids, "stable");
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
    if isscalar(value)
        text = string(value);
    else
        text = string(mat2str(value));
    end
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function value = numericField(container, fieldName, defaultValue)
value = defaultValue;
if ~isstruct(container) || isempty(container) || ~isfield(container, char(fieldName))
    return
end
raw = container.(char(fieldName));
if isnumeric(raw) && isscalar(raw)
    value = double(raw);
elseif isstring(raw) || ischar(raw)
    parsed = str2double(raw);
    if ~isnan(parsed)
        value = parsed;
    end
end
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function text = md(value)
text = replace(string(value), "|", "\|");
text = replace(text, newline, "<br>");
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
