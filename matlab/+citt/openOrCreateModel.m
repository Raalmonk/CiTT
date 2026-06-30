function result = openOrCreateModel(modelPath, options)
%OPENORCREATEMODEL Open an existing SATK-generated Simulink model.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2
    options = struct();
end
showModel = false;
if isfield(options, "ShowModel")
    showModel = logical(options.ShowModel);
elseif isfield(options, "Open")
    showModel = logical(options.Open);
end

modelPath = string(modelPath);
result = struct();
result.success = false;
result.model_path = modelPath;
result.model_name = "";
result.created = false;
result.message = "";

fileCode = exist(modelPath, "file");
if fileCode == 2 || fileCode == 4
    [~, modelName, ~] = fileparts(modelPath);
    load_system(char(modelPath));
    if showModel
        open_system(char(modelName));
    end
    result.success = true;
    result.model_name = string(modelName);
    if showModel
        result.message = "Opened existing model.";
    else
        result.message = "Loaded existing model.";
    end
    return
end

result.message = "Model file is missing. Run the SATK agent task first.";
error("CiTT:ModelMissing", "%s", result.message);
end
