function result = validateTeachingTasks(datasetPath)
%VALIDATETEACHINGTASKS Validate CiTT teaching task dataset metadata.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(datasetPath)
    datasetPath = fullfile(config.SatkProjectRoot, "teaching_tasks", "dataset.json");
end
datasetPath = string(datasetPath);

result = struct();
result.success = false;
result.dataset_path = datasetPath;
result.tasks = struct([]);
result.messages = strings(0, 1);

if exist(datasetPath, "file") ~= 2
    result.messages(end + 1) = "Dataset file is missing.";
    return
end

try
    dataset = jsondecode(fileread(datasetPath));
catch readError
    result.messages(end + 1) = "Dataset JSON could not be parsed: " + string(readError.message);
    return
end

if ~isfield(dataset, "tasks") || ~isstruct(dataset.tasks)
    result.messages(end + 1) = "Dataset must contain a tasks array.";
    return
end

tasks = dataset.tasks;
required = ["id", "title", "prompt_file", "expected_outputs", "learning_objectives", "stages"];
ok = true;
baseDir = fileparts(datasetPath);
for i = 1:numel(tasks)
    for k = 1:numel(required)
        if ~isfield(tasks(i), char(required(k)))
            ok = false;
            result.messages(end + 1) = "Task " + string(i) + " is missing " + required(k) + ".";
        end
    end
    taskDir = fullfile(baseDir, "tasks", char(string(tasks(i).id)));
    promptPath = fullfile(taskDir, char(string(fieldText(tasks(i), "prompt_file"))));
    if exist(promptPath, "file") ~= 2
        ok = false;
        result.messages(end + 1) = "Task " + fieldText(tasks(i), "id") + " prompt file is missing: " + string(promptPath);
    end
end

result.success = ok;
result.tasks = tasks;
if ok
    result.messages(end + 1) = "Teaching task dataset is valid.";
end
end

function text = fieldText(value, name)
if isstruct(value) && isfield(value, char(name))
    text = string(value.(char(name)));
else
    text = "";
end
end
