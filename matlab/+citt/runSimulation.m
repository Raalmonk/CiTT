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
    result.messages = [result.messages; feval('citt.ensureStopTimeReady', modelName)];
    result.simscape_logging = configureSimscapeLogging(modelName);
    result.messages(end + 1) = result.simscape_logging.message;
    simOut = sim(char(modelName));
    result.simscape_logging = collectSimscapeLoggingResult(result.simscape_logging, simOut, modelName);
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

function info = configureSimscapeLogging(modelName)
info = struct();
info.available = false;
info.attempted = false;
info.enabled = false;
info.output_found = false;
info.log_name = "";
info.output_variable = "";
info.message = "Simscape logging parameter was not available for this model.";

try
    get_param(char(modelName), "SimscapeLogType");
    info.available = true;
catch
    return
end

info.attempted = true;
try
    set_param(char(modelName), "SimscapeLogType", "all");
    info.enabled = true;
    info.message = "Simscape logging enabled for this simulation.";
catch loggingError
    info.message = "Could not enable Simscape logging: " + string(loggingError.message);
end

try
    info.log_name = string(get_param(char(modelName), "SimscapeLogName"));
catch
    info.log_name = "simlog_" + string(matlab.lang.makeValidName(char(modelName)));
end
end

function info = collectSimscapeLoggingResult(info, simOut, modelName)
if ~isfield(info, "enabled") || ~info.enabled
    return
end

try
    outputVariables = string(simOut.who);
catch
    outputVariables = strings(0, 1);
end

candidates = unique([
    string(info.log_name)
    "simlog_" + string(matlab.lang.makeValidName(char(modelName)))
    "simlog"
], "stable");
matches = candidates(ismember(candidates, outputVariables));
if ~isempty(matches)
    info.output_found = true;
    info.output_variable = matches(1);
    info.message = "Simscape logging enabled; output variable `" + matches(1) + "` was captured.";
elseif ~isempty(outputVariables)
    info.message = "Simscape logging enabled; no Simscape log variable was found among simulation outputs.";
else
    info.message = "Simscape logging enabled; simulation produced no named output variables.";
end
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
