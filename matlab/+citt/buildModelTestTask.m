function result = buildModelTestTask(context, options)
%BUILDMODELTESTTASK Write the external SATK model_test task markdown.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
taskPath = optionString(options, "TaskPath", config.ModelTestTaskPath);
if exist(config.ModelTestFeaturePath, "file") ~= 2 || exist(config.ModelTestManifestPath, "file") ~= 2
    generated = feval('citt.generateModelTests', context);
else
    generated = struct("feature_path", config.ModelTestFeaturePath, "manifest_path", config.ModelTestManifestPath);
end

promptPath = fullfile(config.MatlabRoot, "resources", "prompts", "agent_run_model_tests.txt");
if exist(promptPath, "file") == 2
    basePrompt = string(fileread(promptPath));
else
    basePrompt = "";
end

taskText = strjoin([
    "# CiTT SATK Model Test Task"
    ""
    "You are operating inside MATLAB/Simulink with Simulink Agentic Toolkit."
    "Load/use the `testing-simulink-models` skill before editing or running the `.feature` file."
    "The `.feature` file is SATK model_test syntax, not plain Gherkin."
    ""
    "## Inputs"
    "- Model: `" + string(context.ModelPath) + "`"
    "- Gherkin feature file: `" + string(generated.feature_path) + "`"
    "- Test manifest: `" + string(generated.manifest_path) + "`"
    "- Expected report JSON: `" + config.ModelTestReportPath + "`"
    "- Expected report Markdown: `" + config.ModelTestMarkdownPath + "`"
    ""
    "## Required Workflow"
    "1. Use model_overview/model_read on the component named in the feature file."
    "2. If the component has physical modeling ports, do not run model_test on it; identify a signal-based wrapper or write failure with reason."
    "3. Run model_test with scenarios = [], verbose = true, draft_mode = true, coverage = none."
    "4. If draft mode passes, run again with draft_mode = false and coverage = none."
    "5. If Stateflow or decision logic is present and coverage tooling is available, optionally run coverage = decision."
    "6. Write JSON and Markdown reports with scenario status, failures, focus/probe mapping, and recommendations."
    ""
    "## Report JSON Contract"
    "Write a JSON object with: success, created_at, model_path, feature_path, manifest_path, scenarios, summary, recommendations, report_path, markdown_path."
    "Each scenario must include: scenario_id, scenario, focus_id, probe_id, status, draft_status, full_status, evidence, failures."
    ""
    "## CiTT Teaching Meaning"
    "These tests are not replacing teaching. They verify that the model behaviors used for teaching are executable and linked to specific focus/probe evidence."
    ""
    basePrompt
], newline);

writeText(taskPath, taskText);

result = struct();
result.success = true;
result.task_path = string(taskPath);
result.feature_path = string(generated.feature_path);
result.manifest_path = string(generated.manifest_path);
result.expected_report_path = config.ModelTestReportPath;
result.expected_markdown_path = config.ModelTestMarkdownPath;
result.summary = "Wrote SATK model_test agent task.";
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

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
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
