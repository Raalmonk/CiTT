function result = clearHighlights(modelPath)
%CLEARHIGHLIGHTS Remove stale Simulink highlighting for a model.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end

result = struct();
result.success = false;
result.model_path = string(modelPath);
result.model_name = "";
result.cleared_paths = strings(0, 1);
result.warnings = strings(0, 1);

try
    modelName = resolveModelName(modelPath);
    if strlength(modelName) == 0
        result.warnings(end + 1) = "No model is available for highlight clearing.";
        return
    end

    result.model_name = modelName;
    clearOne(modelName);
    result.cleared_paths(end + 1) = modelName;

    blocks = find_system(char(modelName), ...
        "LookUnderMasks", "all", ...
        "FollowLinks", "on", ...
        "Type", "Block");
    for i = 1:numel(blocks)
        clearOne(blocks{i});
    end

    lineHandles = find_system(char(modelName), "FindAll", "on", "Type", "Line");
    for i = 1:numel(lineHandles)
        clearOne(lineHandles(i));
    end

    result.success = true;
catch clearError
    result.warnings(end + 1) = string(clearError.message);
end
end

function modelName = resolveModelName(modelPath)
modelName = "";
modelPath = string(modelPath);
if strlength(modelPath) > 0 && exist(modelPath, "file") == 2
    [~, name, ~] = fileparts(modelPath);
    load_system(char(modelPath));
    modelName = string(name);
    return
end

openModels = string(find_system("SearchDepth", 0, "Type", "block_diagram"));
openModels(openModels == "simulink") = [];
if ~isempty(openModels)
    modelName = openModels(1);
end
end

function clearOne(target)
try
    warningState = warning("off", "all");
    cleanup = onCleanup(@() warning(warningState));
    hilite_system(target, "none");
catch
end
end
