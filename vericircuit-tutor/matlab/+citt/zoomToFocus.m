function result = zoomToFocus(modelPath, focusMapInput, focusId)
%ZOOMTOFOCUS Open the subsystem/block associated with a focus map entry.

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

highlight = feval('citt.highlightFocus', modelPath, focusMapInput, focusId);
result = struct();
result.success = false;
result.focus_id = string(focusId);
result.opened_path = "";
result.message = "";
result.highlight = highlight;

paths = highlight.highlighted_paths;
if isempty(paths)
    error("CiTT:ZoomPathMissing", "No highlighted path was available to zoom for focus %s.", string(focusId));
end

targetPath = paths(1);
try
    parentPath = targetPath;
    try
        parentPath = string(get_param(char(targetPath), "Parent"));
    catch
    end
    if strlength(parentPath) > 0
        open_system(char(parentPath));
    else
        open_system(char(targetPath));
    end
    try
        set_param(bdroot(char(targetPath)), "ZoomFactor", "FitSystem");
    catch
    end
    result.opened_path = string(parentPath);
    result.success = true;
    result.message = "Opened focus target.";
catch zoomError
    error("CiTT:ZoomFailed", "Could not zoom/open focus target: %s", zoomError.message);
end
end
