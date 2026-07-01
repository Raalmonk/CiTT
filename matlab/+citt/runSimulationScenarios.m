function report = runSimulationScenarios(context, options)
%RUNSIMULATIONSCENARIOS Run CiTT teaching scenarios with SimulationInput.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.SimulationScenarioReportPath);
markdownPath = optionString(options, "MarkdownPath", config.SimulationScenarioMarkdownPath);
scenarioSpec = feval('citt.buildSimulationScenarios', context);

results = struct("id", {}, "type", {}, "success", {}, "status", {}, "stop_time", {}, "output_variables", {}, "evidence", {}, "error", {});
for i = 1:numel(scenarioSpec.scenarios)
    scenarioItem = scenarioSpec.scenarios(i);
    results(end + 1) = runOneScenario(context, scenarioItem); %#ok<AGROW>
end

statuses = string({results.status});
summary = struct( ...
    "pass", sum(statuses == "PASS"), ...
    "warn", sum(statuses == "WARN"), ...
    "fail", sum(statuses == "FAIL"), ...
    "not_run", sum(statuses == "NOT_RUN"));
report = struct();
report.success = summary.fail == 0 && summary.not_run == 0;
report.created_at = string(datetime("now"));
report.model_path = string(context.ModelPath);
report.scenario_spec_path = scenarioSpec.spec_path;
report.scenarios = results;
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);
report.summary = summary;

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
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

function result = runOneScenario(context, scenarioItem)
result = struct();
result.id = string(scenarioItem.id);
result.type = string(scenarioItem.type);
result.success = false;
result.status = "NOT_RUN";
result.stop_time = scenarioItem.stop_time;
result.output_variables = strings(0, 1);
result.evidence = struct();
result.error = "";

if exist(context.ModelPath, "file") ~= 2 && exist(context.ModelPath, "file") ~= 4
    result.error = "Model file is missing.";
    return
end
if exist("Simulink.SimulationInput", "class") ~= 8
    result.error = "Simulink.SimulationInput is unavailable.";
    return
end

try
    opened = feval('citt.openOrCreateModel', context.ModelPath);
    modelName = string(opened.model_name);
    in = Simulink.SimulationInput(char(modelName));
    in = in.setModelParameter("StopTime", string(scenarioItem.stop_time));
    vars = fieldOr(scenarioItem, "variables", struct());
    if isstruct(vars)
        names = fieldnames(vars);
        for k = 1:numel(names)
            rawValue = vars.(names{k});
            numericValue = str2double(string(rawValue));
            if ~isnan(numericValue)
                rawValue = numericValue;
            end
            in = in.setVariable(names{k}, rawValue);
        end
    end
    out = sim(in);
    result.success = true;
    result.status = "PASS";
    result.evidence = feval('citt.extractSimulationEvidence', out, scenarioItem, context);
    result.output_variables = result.evidence.output_variables;
catch simError
    result.status = "FAIL";
    result.error = string(simError.message);
end
end

function value = fieldOr(data, fieldName, defaultValue)
if isstruct(data) && isfield(data, char(fieldName))
    value = data.(char(fieldName));
else
    value = defaultValue;
end
end

function text = renderMarkdown(report)
lines = [
    "# CiTT SimulationInput Scenarios"
    ""
    "Created: " + report.created_at
    "Model: " + report.model_path
    "Success: " + string(report.success)
    ""
    "| Scenario | Type | Status | Stop time | Outputs | Error |"
    "| --- | --- | --- | --- | --- | --- |"
];
for i = 1:numel(report.scenarios)
    row = report.scenarios(i);
    lines(end + 1) = "| " + md(row.id) + " | " + md(row.type) + " | " + md(row.status) + ...
        " | " + md(string(row.stop_time)) + " | " + md(strjoin(string(row.output_variables(:)), "<br>")) + ...
        " | " + md(row.error) + " |"; %#ok<AGROW>
end
text = strjoin(lines, newline);
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
