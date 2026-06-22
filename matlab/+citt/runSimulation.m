function result = runSimulation(modelPath, options)
%RUNSIMULATION Run the generated Simulink model when possible.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(options)
    options = struct();
end

summaryPath = config.SimulationSummaryPath;
if isfield(options, "SummaryPath")
    summaryPath = string(options.SummaryPath);
end

result = struct();
result.success = false;
result.model_path = string(modelPath);
result.summary_path = string(summaryPath);
result.messages = strings(0, 1);
result.error = "";
result.output_variables = strings(0, 1);

try
    openResult = feval('citt.openOrCreateModel', modelPath);
    modelName = openResult.model_name;
    simOut = sim(char(modelName));
    result.success = true;
    result.messages(end + 1) = "Simulation completed.";
    try
        result.output_variables = string(simOut.who);
    catch
        result.output_variables = strings(0, 1);
    end
catch simError
    result.error = string(simError.message);
    result.messages(end + 1) = "Simulation failed: " + result.error;
    writeJson(summaryPath, result);
    rethrow(simError);
end

writeJson(summaryPath, result);
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid >= 0
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end
end
