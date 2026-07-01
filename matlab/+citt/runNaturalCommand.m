function result = runNaturalCommand(commandText, context)
%RUNNATURALCOMMAND Dispatch a small set of human-language CiTT commands.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(commandText)
    commandText = "";
end
if nargin < 2 || isempty(context)
    context = struct();
end

commandText = strtrim(string(commandText));
modelPath = contextText(context, "ModelPath", config.GeneratedModelPath);
focusMapPath = contextText(context, "FocusMapPath", config.FocusMapPath);
probeMapPath = contextText(context, "ProbeMapPath", config.ProbeMapPath);
specPath = contextText(context, "SpecPath", config.LastSpecPath);
labCsvPath = contextText(context, "LabCsvPath", "");

result = struct();
result.success = false;
result.command = commandText;
result.action = "";
result.message = "";
result.details = [];
result.warnings = strings(0, 1);

if strlength(commandText) == 0
    error("CiTT:EmptyCommand", "Type a command such as 'open Data Inspector' or 'highlight feedback loop'.");
end

cmd = lower(commandText);

if hasAny(cmd, ["clear highlight", "clear highlights", "unhighlight", "remove highlight", ...
        "清除高亮", "取消高亮", "去掉高亮"])
    result.action = "clear_highlights";
    result.details = feval('citt.clearHighlights', modelPath);
    result.success = result.details.success;
    result.message = "Cleared model highlights.";
    return
end

if hasAny(cmd, ["data inspector", "数据检查", "信号检查", "signal logging", "sdi"])
    result = openToolResult(result, "open_data_inspector", ...
        ["Simulink.sdi.view()"], "Opened Simulink Data Inspector.");
    return
end

if hasAny(cmd, ["logic analyzer", "逻辑分析"])
    result = openModelToolResult(result, "open_logic_analyzer", modelPath, ...
        ["Simulink.scopes.LAScope.openLogicAnalyzer(%MODEL%)", ...
        "Simulink.scopes.SLMenus.openLogicAnalyzer(%MODEL%)", ...
        "logicAnalyzer()"], "Opened Logic Analyzer.");
    return
end

if hasAny(cmd, ["bird", "bird's-eye", "birds-eye", "bird eye", "鸟瞰"])
    result = openModelToolResult(result, "open_birds_eye_scope", modelPath, ...
        ["Simulink.scopes.BirdsEyeUtil.openBirdsEyeScope(%MODEL%)", ...
        "birdsEyeScope()", "birdseyeScope()"], "Opened Bird's-Eye Scope.");
    return
end

if hasAny(cmd, ["simulation manager", "仿真管理", "多仿真"])
    result = openModelToolResult(result, "open_simulation_manager", modelPath, ...
        ["openSimulationManager(%MODEL%)", ...
        "Simulink.SimulationManager.open()", ...
        "Simulink.SimulationManager.show()"], ...
        "Opened Simulation Manager.");
    return
end

if hasAny(cmd, ["simscape result", "simscape results", "simscape explorer", ...
        "simscape 结果", "物理结果", "结果浏览"])
    result.action = "open_simscape_results";
    [result.success, result.message, result.warnings] = openSimscapeResults(modelPath);
    return
end

if hasAny(cmd, ["check model", "model check", "update diagram", "检查模型", "更新模型"])
    result.action = "check_model";
    result.details = feval('citt.runModelCheck', modelPath);
    result.success = result.details.success;
    result.message = "Model check complete.";
    return
end

if hasAny(cmd, ["bode", "frequency response", "freq response", "频响", "波特图", "频率响应"])
    result.action = "bode_analysis";
    result.details = feval('citt.runBodeAnalysis', context);
    result.success = result.details.success;
    result.message = "Bode analysis complete.";
    return
end

if hasAny(cmd, ["lab error", "error analysis", "analyze error", "analyse error", ...
        "lab delta", "实验误差", "误差分析", "分析误差"])
    result.action = "analyze_lab_error";
    result.details = feval('citt.analyzeLabError', labCsvPath, context);
    result.success = result.details.success;
    result.message = "Lab error analysis complete.";
    return
end

if hasAny(cmd, ["simulate", "run simulation", "仿真", "运行模型"])
    result.action = "run_simulation";
    result.details = feval('citt.runSimulation', modelPath);
    result.success = result.details.success;
    result.message = "Simulation complete.";
    return
end

if hasAny(cmd, ["probe", "探针", "测量", "measure", "scope", "观察"])
    probeId = bestProbeId(commandText, probeMapPath);
    if strlength(probeId) == 0
        error("CiTT:CommandProbeMissing", "I could not match that command to a probe in: %s", probeMapPath);
    end
    result.action = "measure";
    result.details = feval('citt.addProbe', modelPath, probeId, probeMapPath, specPath, struct("PreviewOnly", true, "ShowModel", false));
    if isfield(result.details, "preview_only") && logical(result.details.preview_only)
        result.details.measurement = previewOnlyMeasurement(result.details);
    else
        try
            result.details.measurement = summarizeLoggedMeasurement(modelPath, result.details);
        catch measurementError
            result.details.measurement_warning = "Measurement summary unavailable: " + string(measurementError.message);
        end
    end
    result.success = result.details.success;
    result.message = "Highlighted measurement target: " + probeId;
    return
end

if hasAny(cmd, ["zoom", "放大", "定位"])
    focusId = bestFocusId(commandText, focusMapPath);
    if strlength(focusId) == 0
        error("CiTT:CommandFocusMissing", "I could not match that command to a focus item in: %s", focusMapPath);
    end
    result.action = "zoom_focus";
    result.details = feval('citt.zoomToFocus', modelPath, focusMapPath, focusId);
    result.success = result.details.success;
    result.message = result.details.message + " " + focusId;
    return
end

if hasAny(cmd, ["highlight", "高亮", "标出", "显示"])
    focusId = bestFocusId(commandText, focusMapPath);
    if strlength(focusId) == 0
        error("CiTT:CommandFocusMissing", "I could not match that command to a focus item in: %s", focusMapPath);
    end
    result.action = "highlight_focus";
    result.details = feval('citt.highlightFocus', modelPath, focusMapPath, focusId);
    result.success = result.details.success;
    result.message = "Highlighted focus: " + focusId;
    return
end

focusId = bestFocusId(commandText, focusMapPath);
if strlength(focusId) > 0
    result.action = "highlight_focus";
    result.details = feval('citt.highlightFocus', modelPath, focusMapPath, focusId);
    result.success = result.details.success;
    result.message = "Highlighted focus: " + focusId;
    return
end

error("CiTT:UnknownCommand", ...
    "I did not understand that command yet. Try 'open Data Inspector', 'clear highlights', 'highlight feedback loop', or 'probe clamp current'.");
end

function result = openToolResult(result, action, commands, successMessage)
result.action = action;
[ok, message, warnings] = tryCommands(commands);
result.success = ok;
result.message = successMessage;
result.warnings = warnings;
if ~ok
    result.message = message;
end
end

function result = openModelToolResult(result, action, modelPath, commandTemplates, successMessage)
result.action = action;
[commands, commandWarnings] = modelCommands(modelPath, commandTemplates);
[ok, message, warnings] = tryCommands(commands);
result.success = ok;
result.message = successMessage;
result.warnings = [commandWarnings; warnings];
if ~ok
    result.message = message;
end
end

function [commands, warnings] = modelCommands(modelPath, commandTemplates)
commands = strings(0, 1);
warnings = strings(0, 1);
modelLiteral = "''";
try
    opened = feval('citt.openOrCreateModel', modelPath);
    modelLiteral = "'" + replace(opened.model_name, "'", "''") + "'";
catch openError
    warnings(end + 1) = "Could not open current model before launching tool: " + string(openError.message);
end
for i = 1:numel(commandTemplates)
    commands(end + 1) = replace(commandTemplates(i), "%MODEL%", modelLiteral); %#ok<AGROW>
end
end

function [ok, message, warnings] = tryCommands(commands)
ok = false;
message = "";
warnings = strings(0, 1);
for i = 1:numel(commands)
    command = string(commands(i));
    try
        eval(char(command));
        ok = true;
        message = "Opened with command: " + command;
        return
    catch commandError
        warnings(end + 1) = command + ": " + string(commandError.message); %#ok<AGROW>
    end
end
if ~isempty(warnings)
    message = warnings(end);
else
    message = "No tool command was available.";
end
end

function [ok, message, warnings] = openSimscapeResults(modelPath)
ok = false;
message = "";
warnings = strings(0, 1);
try
    opened = feval('citt.openOrCreateModel', modelPath);
    modelName = opened.model_name;
catch openError
    warnings(end + 1) = string(openError.message);
    message = "Could not open the model for Simscape results.";
    return
end

logVar = "simlog_" + matlab.lang.makeValidName(char(modelName));
try
    hasLog = evalin("base", "exist('" + logVar + "','var') == 1");
    if hasLog
        evalin("base", "simscape.logging.view(" + logVar + ");");
        ok = true;
        message = "Opened Simscape Results for " + logVar + ".";
        return
    end
catch logError
    warnings(end + 1) = string(logError.message);
end

try
    set_param(char(modelName), "SimscapeLogType", "all");
catch logTypeError
    warnings(end + 1) = "Could not enable Simscape logging: " + string(logTypeError.message);
end

try
    simOut = sim(char(modelName));
    try
        simlog = simOut.get(char(logVar));
        assignin("base", char(logVar), simlog);
        simscape.logging.view(simlog);
        ok = true;
        message = "Ran simulation and opened Simscape Results.";
        return
    catch simlogError
        warnings(end + 1) = "Simulation completed, but no " + logVar + " result was found: " + string(simlogError.message);
    end
catch simError
    warnings(end + 1) = "Simulation for Simscape Results failed: " + string(simError.message);
end

message = "No Simscape log was available to open.";
end

function id = bestFocusId(commandText, focusMapPath)
id = bestEntryId(commandText, focusMapPath, ["focus_id", "id"], ["focus_map", "items"]);
end

function id = bestProbeId(commandText, probeMapPath)
id = bestEntryId(commandText, probeMapPath, ["probe_id", "focus_id", "id"], ["probe_map", "items"]);
end

function id = bestEntryId(commandText, mapPath, idFields, wrapperFields)
id = "";
items = readItems(mapPath, wrapperFields);
if isempty(items)
    return
end

query = lower(string(commandText));
tokens = commandTokens(query);
bestScore = 0;
for i = 1:numel(items)
    itemText = lower(string(feval('citt.util.jsonEncode', items(i))));
    itemId = firstField(items(i), idFields);
    score = 0;
    if strlength(itemId) > 0 && contains(query, lower(itemId))
        score = score + 100;
    end
    for j = 1:numel(tokens)
        if contains(itemText, tokens(j))
            score = score + strlength(tokens(j));
        end
    end
    if score > bestScore
        bestScore = score;
        id = itemId;
    end
end

if bestScore < 3
    id = "";
end
end

function items = readItems(mapPath, wrapperFields)
items = struct([]);
mapPath = string(mapPath);
if strlength(mapPath) == 0 || exist(mapPath, "file") ~= 2
    return
end
data = jsondecode(fileread(mapPath));
if isstruct(data)
    for i = 1:numel(wrapperFields)
        fieldName = wrapperFields(i);
        if isfield(data, fieldName)
            items = data.(fieldName);
            return
        end
    end
    items = data;
end
end

function tokens = commandTokens(query)
parts = split(regexprep(query, "[^a-z0-9_]+", " "));
parts = strip(parts);
parts(parts == "") = [];
drop = ["open", "please", "show", "highlight", "zoom", "probe", "measure", ...
    "the", "a", "an", "for", "to", "with", "打开", "高亮", "显示", "定位", "测量"];
tokens = strings(0, 1);
if contains(query, "电极")
    tokens(end + 1) = "electrode";
end
if contains(query, "放大") || contains(query, "跨阻")
    tokens(end + 1) = "amplifier";
end
if contains(query, "tia") || contains(query, "transimpedance") || contains(query, "跨阻")
    tokens(end + 1) = "tia";
    tokens(end + 1) = "transimpedance";
    tokens(end + 1) = "voltage";
end
if contains(query, "输入")
    tokens(end + 1) = "input";
end
if contains(query, "恢复") || contains(query, "ecg")
    tokens(end + 1) = "recovered";
    tokens(end + 1) = "ecg";
end
if contains(query, "输出")
    tokens(end + 1) = "output";
end
if contains(query, "浓度")
    tokens(end + 1) = "concentration";
end
if contains(query, "滞后") || contains(query, "膜")
    tokens(end + 1) = "lagged";
    tokens(end + 1) = "membrane";
end
if contains(query, "传感") || contains(query, "传感器")
    tokens(end + 1) = "sensor";
end
if contains(query, "误差") || contains(query, "稳定") || contains(query, "建立")
    tokens(end + 1) = "settling";
    tokens(end + 1) = "error";
end
if contains(query, "digital") || contains(query, "converter") || contains(query, "quantizer") || ...
        contains(query, "代码") || contains(query, "编码") || contains(query, "数字") || contains(query, "模数")
    tokens(end + 1) = "adc";
    tokens(end + 1) = "code";
    tokens(end + 1) = "quantizer";
end
if contains(query, "电压")
    tokens(end + 1) = "voltage";
end
if contains(query, "电流")
    tokens(end + 1) = "current";
end
for i = 1:numel(parts)
    token = string(parts(i));
    if strlength(token) < 2 || any(token == drop)
        continue
    end
    tokens(end + 1) = token; %#ok<AGROW>
end
tokens = unique(tokens);
end

function text = entryText(entry)
parts = strings(0, 1);
fields = string(fieldnames(entry));
for i = 1:numel(fields)
    parts(end + 1) = valueText(entry.(fields(i))); %#ok<AGROW>
end
text = strjoin(parts, " ");
end

function text = valueText(value)
if isempty(value)
    text = "";
elseif ischar(value) || isstring(value)
    text = strjoin(string(value(:))', " ");
elseif iscell(value)
    parts = strings(0, 1);
    for i = 1:numel(value)
        parts(end + 1) = valueText(value{i}); %#ok<AGROW>
    end
    text = strjoin(parts, " ");
elseif isstruct(value)
    parts = strings(0, 1);
    for i = 1:numel(value)
        parts(end + 1) = entryText(value(i)); %#ok<AGROW>
    end
    text = strjoin(parts, " ");
elseif isnumeric(value) || islogical(value)
    text = string(mat2str(value));
else
    text = string(value);
end
end

function measurement = summarizeLoggedMeasurement(modelPath, probeResult)
measurement = struct();
measurement.success = false;
measurement.output_name = measurementOutputName(probeResult);
measurement.unit = measurementUnit(probeResult);
measurement.block_path = "";
measurement.min_V = [];
measurement.max_V = [];
measurement.final_V = [];
measurement.late_peak_to_peak_V = [];
measurement.recovery_time_below_1mV_s = [];
measurement.recovery_time_below_0p5mV_s = [];
measurement.message = "No logged simulation output was available for this measurement.";

parameterMeasurement = summarizeParameterMeasurement(modelPath, probeResult, measurement.output_name);
if isfield(parameterMeasurement, "success") && logical(parameterMeasurement.success)
    measurement = parameterMeasurement;
    return
end

modelPath = string(modelPath);
if strlength(strtrim(modelPath)) == 0 || ~isfile(modelPath)
    measurement.message = "Model file is not available for simulation measurement.";
    return
end

[~, modelName, ~] = fileparts(modelPath);
load_system(char(modelPath));
feval('citt.ensureStopTimeReady', modelName);
simOut = sim(char(modelName));
signal = [];
blockPath = "";
try
    yout = simOut.yout;
    [signal, blockPath] = findLoggedSignal(yout, measurement.output_name, probeResult);
catch
end

if isempty(signal)
    [time, data, blockPath] = findSimulationOutputVariable(simOut, measurement.output_name, probeResult);
else
    time = signal.Time(:);
    data = signal.Data(:);
end
if isempty(data)
    measurement.message = "Simulation completed, but the requested logged output was not found.";
    return
end

if isempty(time) || isempty(data)
    measurement.message = "Logged output was found but contained no samples.";
    return
end

measurement.success = true;
measurement.block_path = blockPath;
measurement.min_V = min(data);
measurement.max_V = max(data);
measurement.final_V = data(end);
lateMask = time >= max(time(end) - 1, time(1));
measurement.late_peak_to_peak_V = max(data(lateMask)) - min(data(lateMask));
measurement.recovery_time_below_1mV_s = sustainedBelowTime(time, data, 1e-3);
measurement.recovery_time_below_0p5mV_s = sustainedBelowTime(time, data, 5e-4);
measurement.message = "Simulation measurement computed from " + blockPath + ".";
end

function measurement = previewOnlyMeasurement(probeResult)
measurement = struct();
measurement.success = false;
measurement.output_name = measurementOutputName(probeResult);
measurement.unit = measurementUnit(probeResult);
measurement.block_path = firstBlockPath(probeResult);
measurement.min_V = [];
measurement.max_V = [];
measurement.final_V = [];
measurement.late_peak_to_peak_V = [];
measurement.recovery_time_below_1mV_s = [];
measurement.recovery_time_below_0p5mV_s = [];
measurement.message = "Preview-only measurement target matched. No simulation was run and no model changes were made.";
end

function measurement = summarizeParameterMeasurement(modelPath, probeResult, outputName)
measurement = struct();
measurement.success = false;

targetText = lower(valueText(probeResult));
if ~isRcParameterProbe(targetText)
    return
end

[rOhm, rSource] = readSimscapeScalar(modelPath, "R1_39p8k", ["R", "Resistance"], 39.8e3);
[cFarad, cSource] = readSimscapeScalar(modelPath, "C1_100nF", ["c", "C", "Capacitance"], 100e-9);
[cMistakeFarad, cMistakeSource] = readSimscapeScalar(modelPath, "C1_MISTAKE_100uF", ["c", "C", "Capacitance"], 100e-6);

tau = rOhm * cFarad;
fc = 1 / (2 * pi * tau);
mag5dB = rcLowpassMagnitudeDb(5, fc);
mag60dB = rcLowpassMagnitudeDb(60, fc);
mag250dB = rcLowpassMagnitudeDb(250, fc);
mistakeFc = 1 / (2 * pi * rOhm * cMistakeFarad);

lines = [
    "Measured from Simscape model parameters:"
    "R1 = " + formatOhms(rOhm) + " (" + rSource + ")."
    "C1 = " + formatFarads(cFarad) + " (" + cSource + ")."
    "tau = R*C = " + string(sprintf("%.4g s", tau)) + "."
    "Cutoff frequency fc = 1/(2*pi*R*C) = " + string(sprintf("%.4f Hz", fc)) + "."
    "At 5 Hz: |Vout/Vin| = " + string(sprintf("%.4f dB", mag5dB)) + " (sensor signal nearly passes)."
    "At 60 Hz: |Vout/Vin| = " + string(sprintf("%.4f dB", mag60dB)) + " (mains ripple is reduced)."
    "At 250 Hz: |Vout/Vin| = " + string(sprintf("%.4f dB", mag250dB)) + " (500 Hz ADC Nyquist edge)."
];

if contains(targetText, "mistake") || contains(targetText, "100uf") || contains(targetText, "100 uf") || contains(targetText, "wrong_capacitor")
    lines(end + 1, 1) = "100 uF mistake branch C = " + formatFarads(cMistakeFarad) + ...
        " (" + cMistakeSource + "), so fc would drop to " + string(sprintf("%.5f Hz", mistakeFc)) + ".";
end

measurement.success = true;
measurement.output_name = outputName;
measurement.block_path = "citt_generated_model/R1_39p8k, citt_generated_model/C1_100nF";
measurement.cutoff_frequency_Hz = fc;
measurement.time_constant_s = tau;
measurement.magnitude_5Hz_dB = mag5dB;
measurement.magnitude_60Hz_dB = mag60dB;
measurement.magnitude_250Hz_dB = mag250dB;
measurement.mistake_cutoff_frequency_Hz = mistakeFc;
measurement.summary_lines = lines;
measurement.message = "Computed from Simscape model parameters.";
end

function yes = isRcParameterProbe(text)
yes = hasAny(text, ["r1_39p8k", "c1_100nf", "cutoff_frequency_from_r1_c1", ...
    "abs_vout_over_vin", "frequency_attenuation", "nyquist", "low-pass", "low pass"]) && ...
    hasAny(text, ["rc", "cutoff", "attenuation", "nyquist", "vout"]);
end

function [value, source] = readSimscapeScalar(modelPath, blockName, paramNames, defaultValue)
value = defaultValue;
source = "prompt default value";
modelPath = string(modelPath);
if strlength(strtrim(modelPath)) == 0 || ~isfile(modelPath)
    return
end

[~, modelName, ~] = fileparts(modelPath);
try
    load_system(char(modelPath));
catch
    return
end

blockPath = string(modelName) + "/" + string(blockName);
for i = 1:numel(paramNames)
    paramName = string(paramNames(i));
    try
        raw = get_param(char(blockPath), char(paramName));
        parsed = parseScalarValue(raw);
        if isfinite(parsed) && parsed > 0
            value = parsed;
            source = blockPath + "." + paramName;
            return
        end
    catch
    end
end
end

function value = parseScalarValue(raw)
value = NaN;
if isnumeric(raw) || islogical(raw)
    values = double(raw(:));
    if ~isempty(values)
        value = values(1);
    end
    return
end
if iscell(raw) && ~isempty(raw)
    value = parseScalarValue(raw{1});
    return
end

rawText = string(raw);
match = regexp(char(rawText), "[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "match", "once");
if isempty(match)
    return
end
value = str2double(match);
if ~isfinite(value)
    return
end

lowerText = lower(rawText);
if contains(lowerText, "kohm") || contains(lowerText, "k ohm")
    value = value * 1e3;
elseif contains(lowerText, "mohm") || contains(lowerText, "megohm")
    value = value * 1e6;
elseif contains(lowerText, "uf") || contains(lowerText, "microf")
    value = value * 1e-6;
elseif contains(lowerText, "nf")
    value = value * 1e-9;
elseif contains(lowerText, "pf")
    value = value * 1e-12;
end
end

function magnitudeDb = rcLowpassMagnitudeDb(frequencyHz, cutoffHz)
magnitude = 1 / sqrt(1 + (frequencyHz / cutoffHz)^2);
magnitudeDb = 20 * log10(magnitude);
end

function text = formatOhms(value)
if abs(value) >= 1e6
    text = string(sprintf("%.4g MOhm", value / 1e6));
elseif abs(value) >= 1e3
    text = string(sprintf("%.4g kOhm", value / 1e3));
else
    text = string(sprintf("%.4g Ohm", value));
end
end

function text = formatFarads(value)
if abs(value) >= 1e-3
    text = string(sprintf("%.4g mF", value / 1e-3));
elseif abs(value) >= 1e-6
    text = string(sprintf("%.4g uF", value / 1e-6));
elseif abs(value) >= 1e-9
    text = string(sprintf("%.4g nF", value / 1e-9));
else
    text = string(sprintf("%.4g F", value));
end
end

function outputName = measurementOutputName(probeResult)
rawText = valueText(probeResult);
variableMatch = regexp(char(rawText), "variable\s+([A-Za-z]\w*)", "tokens", "once", "ignorecase");
if ~isempty(variableMatch)
    outputName = string(variableMatch{1});
    return
end

text = lower(rawText);
match = regexp(text, "output\s+([a-z][a-z0-9_]*_v)", "tokens", "once");
if ~isempty(match)
    outputName = string(match{1});
    return
end

targetId = "";
if isstruct(probeResult) && isfield(probeResult, "target_id")
    targetId = lower(string(probeResult.target_id));
end
targetId = erase(targetId, "probe_");
if contains(targetId, "recovered") && contains(targetId, "ecg")
    outputName = "recovered_ecg_voltage_v";
elseif contains(targetId, "amp") || contains(targetId, "amplifier")
    outputName = "amp_input_voltage_v";
elseif contains(targetId, "electrode")
    outputName = "electrode_voltage_v";
else
    outputName = targetId;
end
end

function unit = measurementUnit(probeResult)
text = lower(valueText(probeResult));
if contains(text, "(a)") || contains(text, " current ") || contains(text, "current through")
    unit = "A";
elseif contains(text, "(v)") || contains(text, " voltage ") || contains(text, "voltage")
    unit = "V";
else
    unit = "unit";
end
end

function path = firstBlockPath(probeResult)
path = "";
if ~isstruct(probeResult) || ~isfield(probeResult, "block_paths")
    return
end
paths = string(probeResult.block_paths(:));
paths = paths(strlength(strtrim(paths)) > 0);
if ~isempty(paths)
    path = paths(1);
end
end

function [signal, blockPath] = findLoggedSignal(yout, outputName, probeResult)
signal = [];
blockPath = "";
bestScore = -Inf;
targetText = lower(valueText(probeResult));
for i = 1:yout.numElements
    element = yout.get(i);
    pathText = loggedBlockPath(element);
    lowerPath = lower(pathText);
    score = 0;
    if strlength(outputName) > 0 && contains(lowerPath, lower(outputName))
        score = score + 20;
    end
    if contains(lowerPath, "recovered") && contains(targetText, "recovered")
        score = score + 8;
    end
    if contains(lowerPath, "amp") && (contains(targetText, "amp") || contains(targetText, "amplifier"))
        score = score + 8;
    end
    if contains(lowerPath, "electrode") && contains(targetText, "electrode")
        score = score + 8;
    end
    if score > bestScore
        bestScore = score;
        blockPath = pathText;
        signal = element.Values;
    end
end
if bestScore <= 0
    signal = [];
    blockPath = "";
end
end

function text = loggedBlockPath(element)
text = "";
try
    text = string(element.BlockPath.getBlock(1));
catch
    try
        text = string(element.BlockPath);
    catch
        text = "";
    end
end
end

function [time, data, variableName] = findSimulationOutputVariable(simOut, outputName, probeResult)
time = [];
data = [];
variableName = "";
try
    names = string(simOut.who);
catch
    names = strings(0, 1);
end
if isempty(names)
    return
end

targetText = lower(valueText(probeResult));
outputName = lower(string(outputName));
bestScore = -Inf;
for i = 1:numel(names)
    name = string(names(i));
    lowerName = lower(name);
    score = 0;
    if strlength(outputName) > 0 && lowerName == outputName
        score = score + 40;
    elseif strlength(outputName) > 0 && contains(lowerName, outputName)
        score = score + 20;
    end
    compactOutput = erase(outputName, ["citt_", "_v", "_voltage"]);
    if strlength(compactOutput) > 0 && contains(lowerName, compactOutput)
        score = score + 10;
    end
    if contains(lowerName, "clamp") && contains(targetText, "clamp")
        score = score + 8;
    end
    if contains(lowerName, "current") || contains(lowerName, "i_") || contains(lowerName, "_i")
        if contains(targetText, "current") || contains(targetText, " i_")
            score = score + 8;
        end
    end
    if contains(lowerName, "voltage") || contains(lowerName, "v_") || contains(lowerName, "_v")
        if contains(targetText, "voltage") || contains(targetText, " v_")
            score = score + 8;
        end
    end
    if score <= bestScore
        continue
    end
    try
        candidate = simOut.get(char(name));
        [candidateTime, candidateData] = simulationOutputData(candidate);
    catch
        candidateTime = [];
        candidateData = [];
    end
    if isempty(candidateTime) || isempty(candidateData)
        continue
    end
    bestScore = score;
    time = candidateTime;
    data = candidateData;
    variableName = "To Workspace variable " + name;
end
if bestScore <= 0
    time = [];
    data = [];
    variableName = "";
end
end

function [time, data] = simulationOutputData(value)
time = [];
data = [];
if isa(value, 'timeseries')
    time = double(value.Time(:));
    data = squeeze(double(value.Data));
    data = data(:);
    return
end
if isstruct(value)
    if isfield(value, "time") && isfield(value, "signals")
        time = double(value.time(:));
        signals = value.signals;
        if isstruct(signals) && isfield(signals, "values")
            data = squeeze(double(signals.values));
            data = data(:);
        end
    elseif isfield(value, "Time") && isfield(value, "Data")
        time = double(value.Time(:));
        data = squeeze(double(value.Data));
        data = data(:);
    end
    return
end
if isnumeric(value)
    values = double(value);
    if size(values, 2) >= 2
        time = values(:, 1);
        data = values(:, 2);
    else
        data = values(:);
        time = (0:numel(data)-1)';
    end
end
end

function timeValue = sustainedBelowTime(time, data, threshold)
timeValue = [];
for i = 1:numel(data)
    if all(abs(data(i:end)) <= threshold)
        timeValue = time(i);
        return
    end
end
end

function value = firstField(entry, fieldNames)
value = "";
for i = 1:numel(fieldNames)
    fieldName = fieldNames(i);
    if isfield(entry, fieldName)
        value = string(entry.(fieldName));
        return
    end
end
end

function value = contextText(context, fieldName, defaultValue)
if isstruct(context) && isfield(context, fieldName) && ~isempty(context.(fieldName))
    value = string(context.(fieldName));
else
    value = string(defaultValue);
end
end

function yes = hasAny(text, needles)
yes = any(contains(text, lower(string(needles))));
end
