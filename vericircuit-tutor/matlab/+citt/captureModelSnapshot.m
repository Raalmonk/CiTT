function result = captureModelSnapshot(modelPath, options)
%CAPTUREMODELSNAPSHOT Export the current Simulink diagram view to a PNG.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(options)
    options = struct();
end

outputPath = optionString(options, "OutputPath", config.ModelSnapshotPath);
targetSystem = optionString(options, "TargetSystem", "");

result = struct();
result.success = false;
result.image_path = string(outputPath);
result.target_system = "";
result.message = "";

if strlength(strtrim(modelPath)) == 0 || ~isExistingFile(modelPath)
    error("CiTT:ModelSnapshotMissingModel", "No Simulink model is available for preview.");
end

folder = fileparts(char(outputPath));
if exist(folder, "dir") ~= 7
    mkdir(folder);
end

[~, modelName, ~] = fileparts(char(modelPath));
try
    load_system(char(modelPath));
    open_system(char(modelName));
catch openError
    error("CiTT:ModelSnapshotOpenFailed", "Could not open model for preview: %s", openError.message);
end

printTarget = snapshotTarget(modelName, targetSystem);
try
    try
        open_system(char(printTarget));
    catch
    end
    try
        set_param(char(printTarget), "ZoomFactor", "FitSystem");
    catch
        try
            set_param(char(modelName), "ZoomFactor", "FitSystem");
        catch
        end
    end
    drawnow;
    pause(0.15);
    print(char("-s" + printTarget), "-dpng", "-r160", char(outputPath));
catch printError
    error("CiTT:ModelSnapshotPrintFailed", "Could not export Simulink preview: %s", printError.message);
end

if ~isExistingFile(outputPath)
    error("CiTT:ModelSnapshotNotWritten", "Simulink preview was not written: %s", outputPath);
end

result.success = true;
result.target_system = string(printTarget);
result.message = "Preview updated.";
end

function value = optionString(options, fieldName, defaultValue)
value = string(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    raw = options.(fieldName);
    if ~isempty(raw)
        value = string(raw);
    end
end
end

function target = snapshotTarget(modelName, requestedTarget)
target = string(modelName);
requestedTarget = string(requestedTarget);
if strlength(strtrim(requestedTarget)) == 0
    return
end
try
    if strcmp(get_param(char(requestedTarget), "Type"), "block")
        parent = string(get_param(char(requestedTarget), "Parent"));
        if strlength(strtrim(parent)) > 0
            target = parent;
            return
        end
    end
    target = requestedTarget;
catch
    target = string(modelName);
end
end

function tf = isExistingFile(pathValue)
code = exist(string(pathValue), "file");
tf = code == 2 || code == 4;
end
