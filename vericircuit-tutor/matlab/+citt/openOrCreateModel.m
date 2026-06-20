function result = openOrCreateModel(modelPath, options)
%OPENORCREATEMODEL Open an existing SATK-generated Simulink model.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2
    options = struct(); %#ok<NASGU>
end

modelPath = string(modelPath);
result = struct();
result.success = false;
result.model_path = modelPath;
result.model_name = "";
result.created = false;
result.message = "";

if exist(modelPath, "file") == 2
    [~, modelName, ~] = fileparts(modelPath);
    load_system(char(modelPath));
    open_system(char(modelName));
    result.success = true;
    result.model_name = string(modelName);
    result.message = "Opened existing model.";
    return
end

result.message = "Model file is missing. Run the SATK agent task first.";
error("CiTT:ModelMissing", "%s", result.message);
end
