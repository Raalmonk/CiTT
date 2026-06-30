function result = ensureAgenticToolkit(config)
%ENSUREAGENTICTOOLKIT Put SATK model tools on the active MATLAB path.

if nargin < 1 || isempty(config)
    config = feval('citt.loadConfig');
end

result = struct();
result.satk_path_added = false;
result.tools_path_added = false;
result.satk_initialized = false;
result.model_overview_available = false;
result.model_edit_available = false;
result.model_check_available = false;
result.message = "";

satkPath = string(config.SatkInstallPath);
if strlength(strtrim(satkPath)) > 0 && exist(satkPath, "dir") == 7
    addpath(char(satkPath), "-begin");
    result.satk_path_added = true;

    toolsPath = fullfile(satkPath, "tools");
    if exist(toolsPath, "dir") == 7
        addpath(genpath(char(toolsPath)), "-begin");
        result.tools_path_added = true;
    end
end

rehash;
if exist("satk_initialize", "file") == 2 || exist("satk_initialize", "file") == 6
    try
        satk_initialize;
        result.satk_initialized = true;
    catch initError
        result.message = "satk_initialize failed: " + string(initError.message);
    end
end
rehash;

result.model_overview_available = toolAvailable("model_overview");
result.model_edit_available = toolAvailable("model_edit");
result.model_check_available = toolAvailable("model_check");
if strlength(result.message) == 0
    result.message = "SATK model tools checked.";
end
end

function tf = toolAvailable(name)
kind = exist(char(name), "file");
tf = kind == 2 || kind == 6;
end
