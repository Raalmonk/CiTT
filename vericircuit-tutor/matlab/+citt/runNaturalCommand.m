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
    result.action = "place_probe";
    result.details = feval('citt.addProbe', modelPath, probeId, probeMapPath, specPath);
    result.success = result.details.success;
    result.message = "Placed or highlighted probe: " + probeId;
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

function value = contextText(context, fieldName, fallback)
if isstruct(context) && isfield(context, fieldName) && ~isempty(context.(fieldName))
    value = string(context.(fieldName));
else
    value = string(fallback);
end
end

function yes = hasAny(text, needles)
yes = any(contains(text, lower(string(needles))));
end
