function matchedEntry = highlightFocus(modelName, focusMap, focusId)
%HIGHLIGHTFOCUS Highlight a focus-map target in Simulink/Simscape when possible.
% Missing models or targets produce warnings instead of crashing the tutor.
% Demo focus IDs include rc_filter and feedback_loop.

if nargin < 3
    error("CiTT:HighlightFocus", "Usage: citt.highlightFocus(modelName, focusMap, focusId)");
end

matchedEntry = [];
focusId = string(focusId);

try
    if strlength(string(modelName)) > 0
        open_system(modelName);
        try
            hilite_system(modelName, "none");
        catch
        end
    end
catch modelError
    warning("CiTT:ModelOpen", "Could not open model %s: %s", string(modelName), modelError.message);
end

entries = focusMap;
if isstruct(entries) && isfield(entries, "id")
    for index = 1:numel(entries)
        if string(entries(index).id) == focusId
            matchedEntry = entries(index);
            break
        end
    end
elseif iscell(entries)
    for index = 1:numel(entries)
        candidate = entries{index};
        if isstruct(candidate) && isfield(candidate, "id") && string(candidate.id) == focusId
            matchedEntry = candidate;
            break
        end
    end
end

if isempty(matchedEntry)
    warning("CiTT:MissingFocus", "Focus id %s was not found.", focusId);
    return
end

targets = matchedEntry.targets;
for targetIndex = 1:numel(targets)
    target = targets(targetIndex);
    targetPath = "";
    if isfield(target, "model_path") && strlength(string(target.model_path)) > 0
        targetPath = string(target.model_path);
    elseif isfield(target, "id")
        targetPath = string(target.id);
    end

    if strlength(targetPath) == 0
        warning("CiTT:MissingTargetPath", "Focus %s has a target without a model path.", focusId);
        continue
    end

    try
        style = "find";
        if isfield(target, "style") && any(string(target.style) == ["find", "default", "lineTrace", "fade"])
            style = string(target.style);
        end
        hilite_system(targetPath, style);
    catch highlightError
        warning("CiTT:HighlightUnavailable", ...
            "Could not highlight %s for focus %s: %s", targetPath, focusId, highlightError.message);
    end
end
end
