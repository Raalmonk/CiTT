function result = teachingTaskExplorer(taskId, options)
%TEACHINGTASKEXPLORER Stage a reproducible CiTT teaching benchmark task.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(taskId)
    taskId = "";
end
if nargin < 2 || isempty(options)
    options = struct();
end

datasetPath = optionString(options, "DatasetPath", fullfile(config.SatkProjectRoot, "teaching_tasks", "dataset.json"));
validation = feval('citt.validateTeachingTasks', datasetPath);
if ~validation.success
    error("CiTT:TeachingTaskDatasetInvalid", "%s", strjoin(validation.messages, " | "));
end

tasks = validation.tasks;
if strlength(strtrim(string(taskId))) == 0
    task = tasks(1);
else
    task = selectTask(tasks, string(taskId));
end

workspaceRoot = optionString(options, "WorkspaceRoot", ...
    fullfile(config.WorkDir, "teaching_task_" + matlab.lang.makeValidName(char(task.id)) + "_" + string(datetime("now", "Format", "yyyyMMdd_HHmmss"))));
if exist(workspaceRoot, "dir") ~= 7
    mkdir(workspaceRoot);
end

datasetDir = fileparts(datasetPath);
taskDir = fullfile(datasetDir, "tasks", char(string(task.id)));
stagedTaskDir = fullfile(workspaceRoot, "task");
if exist(stagedTaskDir, "dir") ~= 7
    mkdir(stagedTaskDir);
end
copyfile(taskDir, stagedTaskDir, "f");
sharedDir = fullfile(datasetDir, "shared");
if exist(sharedDir, "dir") == 7
    copyfile(sharedDir, fullfile(workspaceRoot, "shared"), "f");
end

promptPath = string(fullfile(stagedTaskDir, char(string(task.prompt_file))));
runbookPath = string(fullfile(workspaceRoot, "RUNBOOK.md"));
writeText(runbookPath, renderRunbook(task, promptPath, workspaceRoot));

previousWorkDir = string(getenv("CITT_WORK_DIR"));
setenv("CITT_WORK_DIR", char(workspaceRoot));

result = struct();
result.success = true;
result.task_id = string(task.id);
result.title = string(task.title);
result.workspace_root = string(workspaceRoot);
result.prompt_path = promptPath;
result.runbook_path = runbookPath;
result.previous_work_dir = previousWorkDir;
result.expected_outputs = task.expected_outputs;
result.learning_objectives = task.learning_objectives;
result.stages = task.stages;
result.messages = [
    "Teaching task staged in isolated workspace."
    "CITT_WORK_DIR now points at the staged workspace for this MATLAB session."
];

if optionFlag(options, "Launch", false)
    result.app = feval('citt.openHtmlApp');
end
end

function task = selectTask(tasks, taskId)
for i = 1:numel(tasks)
    if string(tasks(i).id) == taskId
        task = tasks(i);
        return
    end
end
error("CiTT:TeachingTaskNotFound", "Teaching task not found: %s", taskId);
end

function text = renderRunbook(task, promptPath, workspaceRoot)
lines = [
    "# CiTT Teaching Task Explorer"
    ""
    "Task: " + string(task.id) + " - " + string(task.title)
    "Workspace: " + string(workspaceRoot)
    "Prompt: " + string(promptPath)
    ""
    "## Runbook"
    ""
];
for i = 1:numel(task.stages)
    stage = objectAt(task.stages, i);
    artifacts = "";
    if isfield(stage, "success_artifacts")
        artifacts = strjoin(string(stage.success_artifacts), ", ");
    end
    lines(end + 1) = string(i) + ". " + string(stage.id) + " -> UI action `" + string(stage.ui_action) + "`; artifacts: " + artifacts; %#ok<AGROW>
end
lines = [lines; ""; "## Learning Objectives"; ""];
for i = 1:numel(task.learning_objectives)
    objective = objectAt(task.learning_objectives, i);
    lines(end + 1) = "- " + fieldText(objective, "id") + ": " + fieldText(objective, "summary"); %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function item = objectAt(value, index)
if iscell(value)
    item = value{index};
else
    item = value(index);
end
end

function text = fieldText(value, name)
if isstruct(value) && isfield(value, char(name))
    text = string(value.(char(name)));
else
    text = "";
end
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function value = optionFlag(options, fieldName, defaultValue)
value = logical(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    value = logical(options.(fieldName));
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
