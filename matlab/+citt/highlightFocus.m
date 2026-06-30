function result = highlightFocus(modelPath, focusMapInput, focusId, options)
%HIGHLIGHTFOCUS Highlight blocks from an agent-generated focus map.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(focusMapInput)
    focusMapInput = config.FocusMapPath;
end
if nargin < 3 || isempty(focusId)
    focusId = "";
end
if nargin < 4 || isempty(options)
    options = struct();
end
showModel = optionLogical(options, "ShowModel", false);

result = struct();
result.success = false;
result.focus_id = string(focusId);
result.highlighted_paths = strings(0, 1);
result.warnings = strings(0, 1);
result.focus = [];
result.visual_highlight_applied = showModel;

focusMap = readFocusMap(focusMapInput);
focus = findFocus(focusMap, focusId);
if isempty(focus)
    error("CiTT:MissingFocus", "Focus id was not found in the SATK-generated focus map: %s", string(focusId));
end
result.focus = focus;

tryOpenModel(modelPath, result.focus, showModel);
if showModel
    clearResult = feval('citt.clearHighlights', modelPath);
    result.cleared_highlights = clearResult.cleared_paths;
else
    result.cleared_highlights = strings(0, 1);
end

paths = focusPaths(focus);
for i = 1:numel(paths)
    targetPath = paths(i);
    if strlength(targetPath) == 0
        continue
    end
    try
        if showModel
            hilite_system(char(targetPath), "find");
        end
        result.highlighted_paths(end + 1) = targetPath; %#ok<AGROW>
    catch highlightError
        error("CiTT:HighlightUnavailable", ...
            "Could not highlight %s for focus %s: %s", targetPath, string(focusId), highlightError.message);
    end
end

result.success = ~isempty(result.highlighted_paths);
if ~result.success
    error("CiTT:FocusPathMissing", "Focus map entry has no highlightable block/model paths: %s", string(focusId));
end
end

function focusMap = readFocusMap(inputValue)
if isstruct(inputValue)
    focusMap = inputValue;
    return
end
if iscell(inputValue)
    focusMap = inputValue;
    return
end
path = string(inputValue);
if exist(path, "file") ~= 2
    error("CiTT:FocusMapMissing", "Focus map file does not exist: %s", path);
end
focusMap = jsondecode(fileread(path));
end

function focus = findFocus(focusMap, focusId)
focus = [];
items = unwrapItems(focusMap);
focusId = string(focusId);
if strlength(focusId) == 0 && ~isempty(items)
    focus = items(1);
    return
end
for i = 1:numel(items)
    candidateId = entryId(items(i));
    if candidateId == focusId
        focus = items(i);
        return
    end
end
end

function items = unwrapItems(focusMap)
if isstruct(focusMap) && isfield(focusMap, "focus_map")
    items = focusMap.focus_map;
elseif isstruct(focusMap) && isfield(focusMap, "items")
    items = focusMap.items;
elseif isstruct(focusMap)
    items = focusMap;
elseif iscell(focusMap)
    items = [focusMap{:}];
else
    items = struct([]);
end
end

function id = entryId(entry)
if isfield(entry, "focus_id")
    id = string(entry.focus_id);
elseif isfield(entry, "id")
    id = string(entry.id);
else
    id = "";
end
end

function paths = focusPaths(focus)
paths = strings(0, 1);
paths = appendFieldPaths(paths, focus, "block_paths");
paths = appendFieldPaths(paths, focus, "model_paths");
if isfield(focus, "targets")
    targets = focus.targets;
    for i = 1:numel(targets)
        if isfield(targets(i), "model_path")
            paths(end + 1) = string(targets(i).model_path); %#ok<AGROW>
        elseif isfield(targets(i), "id")
            paths(end + 1) = string(targets(i).id); %#ok<AGROW>
        end
    end
end
paths = paths(~isFileSystemModelPath(paths));
paths = unique(paths, "stable");
end

function paths = appendFieldPaths(paths, entry, fieldName)
if ~isfield(entry, fieldName)
    return
end
value = entry.(fieldName);
if iscell(value)
    for i = 1:numel(value)
        paths(end + 1) = string(value{i}); %#ok<AGROW>
    end
elseif isstring(value) || ischar(value)
    paths = [paths; string(value(:))]; %#ok<AGROW>
else
    paths = [paths; string(value(:))]; %#ok<AGROW>
end
end

function tryOpenModel(modelPath, focus, showModel)
try
    if strlength(string(modelPath)) > 0 && isExistingFile(modelPath)
        load_system(char(modelPath));
        [~, modelName, ~] = fileparts(modelPath);
        if showModel
            open_system(char(modelName));
        end
        return
    end
    paths = focusPaths(focus);
    if showModel && ~isempty(paths)
        open_system(char(paths(1)));
    end
catch
end
end

function value = optionLogical(options, fieldName, defaultValue)
value = logical(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    try
        value = logical(options.(fieldName));
    catch
        value = logical(defaultValue);
    end
end
end

function tf = isExistingFile(pathValue)
code = exist(string(pathValue), "file");
tf = code == 2 || code == 4;
end

function tf = isFileSystemModelPath(paths)
paths = string(paths);
tf = false(size(paths));
for i = 1:numel(paths)
    [~, ~, ext] = fileparts(char(paths(i)));
    tf(i) = isExistingFile(paths(i)) || any(lower(string(ext)) == [".slx", ".mdl"]);
end
end
