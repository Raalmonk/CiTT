function result = highlightExplainabilityAction(modelPath, explainabilityMapInput, actionId, focusMapInput)
%HIGHLIGHTEXPLAINABILITYACTION Highlight a saved explainability action.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(explainabilityMapInput)
    explainabilityMapInput = config.ExplainabilityMapPath;
end
if nargin < 3 || isempty(actionId)
    actionId = "";
end
if nargin < 4 || isempty(focusMapInput)
    focusMapInput = config.FocusMapPath;
end

map = readMap(explainabilityMapInput);
action = findAction(map, actionId);
if isempty(action)
    error("CiTT:ExplainabilityActionMissing", "Explainability action not found: %s", string(actionId));
end

result = struct();
result.success = false;
result.action_id = string(action.action_id);
result.action_type = string(action.action_type);
result.focus_id = string(action.focus_id);
result.highlight = [];
result.highlighted_paths = strings(0, 1);
result.message = "";

if strlength(result.focus_id) > 0
    result.highlight = feval('citt.highlightFocus', modelPath, focusMapInput, result.focus_id);
    result.highlighted_paths = result.highlight.highlighted_paths;
    result.success = result.highlight.success;
    result.message = "Highlighted focus action.";
    return
end

paths = string(action.target_paths);
tryOpenModel(modelPath);
for i = 1:numel(paths)
    path = paths(i);
    if strlength(path) == 0
        continue
    end
    try
        hilite_system(char(path), "find");
        result.highlighted_paths(end + 1) = path; %#ok<AGROW>
    catch
    end
end
result.success = ~isempty(result.highlighted_paths);
if result.success
    result.message = "Highlighted action target paths.";
else
    result.message = "Action is conceptual or has no highlightable target paths.";
end
end

function map = readMap(inputValue)
if isstruct(inputValue)
    map = inputValue;
    return
end
path = string(inputValue);
if exist(path, "file") ~= 2
    error("CiTT:ExplainabilityMapMissing", "Explainability map missing: %s", path);
end
map = jsondecode(fileread(path));
end

function action = findAction(map, actionId)
action = [];
if ~isstruct(map) || ~isfield(map, "actions")
    return
end
actions = map.actions;
if isempty(actions)
    return
end
actionId = string(actionId);
if strlength(actionId) == 0
    action = actions(1);
    return
end
for i = 1:numel(actions)
    if string(actions(i).action_id) == actionId
        action = actions(i);
        return
    end
end
end

function tryOpenModel(modelPath)
modelPath = string(modelPath);
if strlength(modelPath) == 0
    return
end
try
    feval('citt.openOrCreateModel', modelPath);
catch
end
end
