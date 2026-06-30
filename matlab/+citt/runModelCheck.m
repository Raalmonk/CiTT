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
    result.messages = [result.messages; feval('citt.ensureStopTimeReady', modelName)];
    set_param(char(modelName), "SimulationCommand", "update");
    result.messages(end + 1) = "Diagram update completed.";
    checksum = Simulink.BlockDiagram.getChecksum(char(modelName));
    result.checksum = checksumValue(checksum);
    result.messages(end + 1) = "Model checksum captured.";
    result.simscape_audit = simscapeArtifactAudit(modelName);
    result.messages = [result.messages; simscapeAuditMessages(result.simscape_audit)];
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

function value = checksumValue(checksum)
if isstruct(checksum) && isfield(checksum, "Value")
    value = checksum.Value;
else
    value = checksum;
end
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
if isfield(result, "simscape_audit")
    audit = result.simscape_audit;
    lines = [
        lines
        ""
        "Simscape audit:"
        "- Total blocks: " + string(audit.total_blocks)
        "- Simscape-like blocks: " + string(audit.simscape_blocks)
        "- Solver Configuration blocks: " + string(audit.solver_configuration_blocks)
        "- Reference blocks: " + string(audit.reference_blocks)
        "- Sensor blocks: " + string(audit.sensor_blocks)
        "- PS-Simulink converters: " + string(audit.ps_simulink_converters)
        "- Simulink-PS converters: " + string(audit.simulink_ps_converters)
        "- Logging/output blocks: " + string(audit.logging_blocks)
    ];
    if ~isempty(audit.warnings)
        lines = [lines; "Warnings:"; audit.warnings(:)];
    end
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

function audit = simscapeArtifactAudit(modelName)
blocks = findBlocks(modelName);
refs = strings(numel(blocks), 1);
types = strings(numel(blocks), 1);
names = strings(numel(blocks), 1);
masks = strings(numel(blocks), 1);
for i = 1:numel(blocks)
    refs(i) = getParamText(blocks{i}, "ReferenceBlock");
    types(i) = getParamText(blocks{i}, "BlockType");
    names(i) = getParamText(blocks{i}, "Name");
    masks(i) = getParamText(blocks{i}, "MaskType");
end

refsText = normalizeBlockText(refs);
typesText = normalizeBlockText(types);
namesText = normalizeBlockText(names);
masksText = normalizeBlockText(masks);
haystack = refsText + " " + masksText + " " + typesText + " " + namesText;
simscapeMask = typesText == "simscapeblock" | containsAny(refsText, ["simscape", "ee_lib", ...
    "fl_lib", "foundation"]) | containsAny(masksText, ["solver configuration", ...
    "ps-simulink converter", "simulink-ps converter"]);
solverMask = contains(masksText, "solver configuration") | endsWith(refsText, "solver configuration");
referenceMask = containsAny(masksText, ["electrical reference", "mechanical rotational reference", ...
    "mechanical translational reference", "thermal reference", "isothermal liquid reference"]);
sensorMask = contains(masksText, "sensor") | contains(namesText, "sensor");
psToSimulinkMask = contains(masksText, "ps-simulink converter") | endsWith(refsText, "ps-simulink converter");
simulinkToPsMask = contains(masksText, "simulink-ps converter") | endsWith(refsText, "simulink-ps converter");
loggingMask = typesText == "toworkspace" | typesText == "scope" | typesText == "outport" | ...
    containsAny(haystack, ["to workspace", "scope"]);

audit = struct();
audit.total_blocks = numel(blocks);
audit.simscape_blocks = sum(simscapeMask);
audit.solver_configuration_blocks = sum(solverMask);
audit.reference_blocks = sum(referenceMask);
audit.sensor_blocks = sum(sensorMask);
audit.ps_simulink_converters = sum(psToSimulinkMask);
audit.simulink_ps_converters = sum(simulinkToPsMask);
audit.logging_blocks = sum(loggingMask);
audit.physical_network_likely = audit.simscape_blocks > 0;
audit.warnings = simscapeAuditWarnings(audit);
end

function blocks = findBlocks(modelName)
try
    blocks = find_system(char(modelName), "LookUnderMasks", "all", "FollowLinks", "on", "Type", "Block");
catch
    blocks = find_system(char(modelName), "LookUnderMasks", "all", "Type", "Block");
end
blocks = blocks(:);
end

function text = getParamText(blockPath, parameterName)
try
    text = string(get_param(blockPath, parameterName));
catch
    text = "";
end
end

function text = normalizeBlockText(text)
text = lower(string(text));
text = regexprep(text, "\s+", " ");
text = strip(text);
end

function tf = containsAny(text, needles)
tf = false(size(text));
for i = 1:numel(needles)
    tf = tf | contains(text, needles(i), "IgnoreCase", true);
end
end

function warnings = simscapeAuditWarnings(audit)
warnings = strings(0, 1);
if audit.simscape_blocks == 0
    warnings(end + 1, 1) = "No Simscape-like library blocks were detected. Generated model may not be using the physical modeling path.";
    return
end
if audit.solver_configuration_blocks == 0
    warnings(end + 1, 1) = "No Solver Configuration block detected for the physical network.";
end
if audit.reference_blocks == 0
    warnings(end + 1, 1) = "No physical reference block detected for the physical network.";
end
if audit.sensor_blocks == 0
    warnings(end + 1, 1) = "No sensor blocks detected; requested measurements may not be grounded in Simscape sensors.";
end
if audit.ps_simulink_converters == 0 && audit.logging_blocks > 0
    warnings(end + 1, 1) = "Logging blocks exist, but no PS-Simulink Converter was detected.";
end
if audit.logging_blocks == 0
    warnings(end + 1, 1) = "No logging, Scope, or Outport blocks detected for simulation evidence.";
end
end

function messages = simscapeAuditMessages(audit)
messages = [
    "Simscape audit: " + string(audit.simscape_blocks) + " Simscape-like blocks, " + ...
        string(audit.sensor_blocks) + " sensors, " + string(audit.logging_blocks) + " logging/output blocks."
];
if ~isempty(audit.warnings)
    messages = [messages; "Simscape audit warning: " + audit.warnings(:)];
end
end
