function result = runModelCheck(modelPath, options)
%RUNMODELCHECK Update/check the generated model and write a concise report.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(modelPath)
    modelPath = config.GeneratedModelPath;
end
if nargin < 2 || isempty(options)
    options = struct();
end

reportPath = config.ModelCheckReportPath;
if isfield(options, "ReportPath")
    reportPath = string(options.ReportPath);
end

result = struct();
result.success = false;
result.model_path = string(modelPath);
result.report_path = string(reportPath);
result.messages = strings(0, 1);
result.error = "";

try
    openResult = feval('citt.openOrCreateModel', modelPath);
    modelName = openResult.model_name;
    set_param(char(modelName), "SimulationCommand", "update");
    result.messages(end + 1) = "Diagram update completed.";
    checksum = Simulink.BlockDiagram.getChecksum(char(modelName));
    result.checksum = checksum.Value;
    result.messages(end + 1) = "Model checksum captured.";
    if exist("modeladvisor", "file") == 2
        result.messages(end + 1) = "Model Advisor is available.";
    else
        result.messages(end + 1) = "Model Advisor command not found on this MATLAB path.";
    end
    result.success = true;
catch checkError
    result.error = string(checkError.message);
    result.messages(end + 1) = "Model check failed: " + result.error;
    writeReport(reportPath, result);
    rethrow(checkError);
end

writeReport(reportPath, result);
end

function writeReport(path, result)
lines = [
    "# CiTT Model Check Report"
    ""
    "Model: " + result.model_path
    "Success: " + string(result.success)
    ""
    "Messages:"
    result.messages(:)
];
if strlength(result.error) > 0
    lines(end + 1) = "Error: " + result.error;
end
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid >= 0
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s", char(strjoin(lines, newline)));
end
end
