function result = buildSimscapeModelFromSpec(specInput, options)
%BUILDSIMSCAPEMODELFROMSPEC Generate and open a real Simscape model.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(specInput)
    specInput = config.LastSpecPath;
end
if nargin < 2 || isempty(options)
    options = struct();
end

modelPath = optionString(options, "ModelPath", config.GeneratedModelPath);
scriptPath = optionString(options, "ScriptPath", config.GeneratedBuildScriptPath);
focusMapPath = optionString(options, "FocusMapPath", config.FocusMapPath);
probeMapPath = optionString(options, "ProbeMapPath", config.ProbeMapPath);
reportPath = optionString(options, "ReportPath", config.AgentReportPath);
writeScript = optionLogical(options, "WriteGeneratedScript", true);
runGeneratedScript = optionLogical(options, "RunGeneratedScript", true);
openModel = optionLogical(options, "OpenModel", true);

[spec, specSource] = readSpec(specInput);
rejectBlockingSpec(spec);

if writeScript
    writeText(scriptPath, generatedRunnerText(config.MatlabRoot, specSource, scriptPath, modelPath, ...
        focusMapPath, probeMapPath, reportPath));
end

if writeScript && runGeneratedScript
    result = [];
    run(char(scriptPath));
    if isempty(result)
        error("CiTT:GeneratedBuildNoResult", "Generated build script did not return a result.");
    end
    result.generated_code_path = scriptPath;
    return
end

result = buildModel(spec, struct( ...
    "SpecSource", specSource, ...
    "ModelPath", modelPath, ...
    "ScriptPath", scriptPath, ...
    "FocusMapPath", focusMapPath, ...
    "ProbeMapPath", probeMapPath, ...
    "ReportPath", reportPath, ...
    "OpenModel", openModel));
end

function result = buildModel(spec, build)
requireSimscape();
load_system("fl_lib");
load_system("ee_lib");
load_system("nesl_utility");
load_system("simulink");

modelPath = string(build.ModelPath);
[modelFolder, modelName, ~] = fileparts(char(modelPath));
if strlength(string(modelFolder)) > 0 && exist(modelFolder, "dir") ~= 7
    mkdir(modelFolder);
end
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

new_system(modelName);
if build.OpenModel
    open_system(modelName);
end
set_param(modelName, "StopTime", "1");

messages = strings(0, 1);
unresolvedValues = strings(0, 1);
buildNotes = ambiguityNotes(spec);
unsupportedComponents = strings(0, 1);
connectionWarnings = strings(0, 1);

components = asCellArray(fieldOr(spec, "components", {}));
connections = asCellArray(fieldOr(spec, "connections", {}));
groundNode = string(fieldOr(spec, "ground_node", "0"));
requestedOutputs = asCellArray(fieldOr(spec, "requested_outputs", {}));

blockInfos = struct([]);
idToIndex = containers.Map("KeyType", "char", "ValueType", "double");
usedNames = strings(0, 1);

for i = 1:numel(components)
    component = components{i};
    if ~isstruct(component)
        continue
    end
    componentId = string(fieldOr(component, "id", "component_" + string(i)));
    componentType = string(fieldOr(component, "type", ""));
    [libraryPath, kind, mappedMessage] = libraryForComponent(componentType);
    if strlength(libraryPath) == 0
        unsupportedComponents(end + 1) = componentId + " (" + componentType + ")"; %#ok<AGROW>
        continue
    end

    blockName = uniqueBlockName(componentId, usedNames);
    usedNames(end + 1) = blockName; %#ok<AGROW>
    blockPath = string(modelName) + "/" + blockName;
    position = blockPosition(i);
    add_block(char(libraryPath), char(blockPath), "Position", position);
    if strlength(mappedMessage) > 0
        messages(end + 1) = mappedMessage; %#ok<AGROW>
    end

    [messages, unresolvedValues] = configureBlock(blockPath, component, kind, messages, unresolvedValues);
    blockInfo = makeBlockInfo(componentId, componentType, blockPath, kind);
    blockInfos = [blockInfos; blockInfo]; %#ok<AGROW>
    idToIndex(char(componentId)) = numel(blockInfos);
end

groundPath = string(modelName) + "/Electrical_Reference";
add_block("fl_lib/Electrical/Electrical Elements/Electrical Reference", char(groundPath), ...
    "Position", [70 500 130 560]);
groundPort = firstPhysicalPort(groundPath);

solverPath = string(modelName) + "/Solver_Configuration";
add_block("nesl_utility/Solver Configuration", char(solverPath), ...
    "Position", [70 600 170 660]);
solverPort = firstPhysicalPort(solverPath);

nodeParent = containers.Map("KeyType", "char", "ValueType", "char");
for i = 1:numel(connections)
    connection = connections{i};
    if ~isstruct(connection)
        continue
    end
    fromKey = endpointKey(string(fieldOr(connection, "from", "")));
    toKey = endpointKey(string(fieldOr(connection, "to", "")));
    if strlength(fromKey) > 0 && strlength(toKey) > 0
        nodeParent = unionKeys(nodeParent, fromKey, toKey);
        labelKey = endpointKey(string(fieldOr(connection, "label", "")));
        if strlength(labelKey) > 0
            nodeParent = unionKeys(nodeParent, fromKey, labelKey);
            nodeParent = unionKeys(nodeParent, toKey, labelKey);
        end
    end
end

nodeParent = unionKeys(nodeParent, endpointKey(groundNode), "__ground_reference__");
portGroups = containers.Map("KeyType", "char", "ValueType", "any");
groundRoot = findRoot(nodeParent, "__ground_reference__");
portGroups = appendPort(portGroups, groundRoot, groundPort);
portGroups = appendPort(portGroups, groundRoot, solverPort);

endpointLabels = allEndpointLabels(connections, groundNode);
for i = 1:numel(endpointLabels)
    key = endpointKey(endpointLabels(i));
    [portHandle, foundPort] = endpointPort(key, blockInfos, idToIndex);
    if foundPort
        root = findRoot(nodeParent, key);
        portGroups = appendPort(portGroups, root, portHandle);
    end
end

[messages, connectionWarnings, portGroups] = addRequestedOutputScopes(modelName, requestedOutputs, ...
    nodeParent, portGroups, groundRoot, messages, connectionWarnings);

groupKeys = string(keys(portGroups));
for i = 1:numel(groupKeys)
    ports = uniqueHandles(portGroups(char(groupKeys(i))));
    if numel(ports) < 2
        continue
    end
    for j = 2:numel(ports)
        try
            add_line(modelName, ports(1), ports(j));
        catch lineError
            connectionWarnings(end + 1) = "Could not connect node " + groupKeys(i) + ": " + string(lineError.message); %#ok<AGROW>
        end
    end
end

try
    save_system(modelName, char(modelPath));
catch saveError
    close_system(modelName, 0);
    rethrow(saveError);
end
if build.OpenModel
    open_system(modelName);
end

focusMap = buildFocusMap(spec, blockInfos, modelName);
probeMap = buildProbeMap(spec, requestedOutputs, modelName);
writeJson(build.FocusMapPath, focusMap);
writeJson(build.ProbeMapPath, probeMap);

result = struct();
result.success = isempty(unsupportedComponents) && isempty(connectionWarnings);
result.model_path = modelPath;
result.generated_code_path = string(build.ScriptPath);
result.focus_map_path = string(build.FocusMapPath);
result.probe_map_path = string(build.ProbeMapPath);
result.agent_report_path = string(build.ReportPath);
result.spec_source = string(build.SpecSource);
result.messages = messages;
result.unresolved_values = unresolvedValues;
result.build_notes = buildNotes;
result.unsupported_components = unsupportedComponents;
result.connection_warnings = connectionWarnings;
result.summary = "Generated and opened a Simscape model from the circuit spec.";

writeReport(build.ReportPath, result);

if ~result.success
    error("CiTT:SimscapeBuildIncomplete", ...
        "Simscape model was generated but needs attention. Unsupported: %s. Connection warnings: %s", ...
        strjoin(unsupportedComponents, ", "), strjoin(connectionWarnings, " | "));
end
end

function requireSimscape()
setup = feval('citt.checkSetup');
missing = strings(0, 1);
if ~setup.simulink_available || ~setup.simulink_license
    missing(end + 1) = "Simulink"; %#ok<AGROW>
end
if ~setup.simscape_available || ~setup.simscape_license
    missing(end + 1) = "Simscape"; %#ok<AGROW>
end
if ~isempty(missing)
    error("CiTT:SimscapeSetupMissing", "Model drawing requires: %s", strjoin(missing, ", "));
end
end

function [libraryPath, kind, message] = libraryForComponent(componentType)
type = lower(string(componentType));
libraryPath = "";
kind = "";
message = "";
if contains(type, "resistor")
    libraryPath = "fl_lib/Electrical/Electrical Elements/Resistor";
    kind = "two_terminal";
elseif contains(type, "capacitor")
    libraryPath = "fl_lib/Electrical/Electrical Elements/Capacitor";
    kind = "two_terminal";
elseif contains(type, "inductor")
    libraryPath = "fl_lib/Electrical/Electrical Elements/Inductor";
    kind = "two_terminal";
elseif contains(type, "current") && contains(type, "sensor") || contains(type, "ammeter")
    libraryPath = "fl_lib/Electrical/Electrical Sensors/Current Sensor";
    kind = "current_sensor";
elseif contains(type, "voltage") && contains(type, "sensor") || contains(type, "voltmeter")
    libraryPath = "fl_lib/Electrical/Electrical Sensors/Voltage Sensor";
    kind = "voltage_sensor";
elseif contains(type, "current") && contains(type, "source")
    libraryPath = "fl_lib/Electrical/Electrical Sources/DC Current Source";
    kind = "two_terminal";
elseif contains(type, "voltage") && contains(type, "source")
    libraryPath = "fl_lib/Electrical/Electrical Sources/DC Voltage Source";
    kind = "two_terminal";
elseif contains(type, "op-amp") || contains(type, "op amp") || contains(type, "amplifier")
    libraryPath = "fl_lib/Electrical/Electrical Elements/Op-Amp";
    kind = "op_amp";
    if ~contains(type, "op")
        message = "Mapped " + componentType + " to the Simscape ideal Op-Amp block.";
    end
end
end

function [messages, unresolvedValues] = configureBlock(blockPath, component, kind, messages, unresolvedValues)
value = fieldOr(component, "value", []);
unit = string(fieldOr(component, "unit", ""));
componentId = string(fieldOr(component, "id", blockPath));
[numericValue, hasNumericValue] = numericScalar(value);
blockType = lower(string(fieldOr(component, "type", "")));
parameterExpression = parameterValueExpression(componentId, value);
if strlength(parameterExpression) == 0 && kind == "two_terminal" && componentNeedsValue(blockType)
    parameterExpression = "CITT_" + matlab.lang.makeValidName(char(componentId)) + "_value";
end

if ~hasNumericValue && strlength(parameterExpression) > 0
    unresolvedValues(end + 1) = componentId + " value parameterized as " + parameterExpression; %#ok<AGROW>
end

try
    switch kind
        case "two_terminal"
            if contains(blockType, "resistor") && hasNumericValue
                set_param(char(blockPath), "R", char(string(numericValue)));
                setUnitIfPresent(blockPath, "R_unit", unit);
            elseif contains(blockType, "resistor") && strlength(parameterExpression) > 0
                set_param(char(blockPath), "R", char(parameterExpression));
                setUnitIfPresent(blockPath, "R_unit", unit);
            elseif contains(blockType, "capacitor") && hasNumericValue
                set_param(char(blockPath), "c", char(string(numericValue)));
                setUnitIfPresent(blockPath, "c_unit", unit);
            elseif contains(blockType, "capacitor") && strlength(parameterExpression) > 0
                set_param(char(blockPath), "c", char(parameterExpression));
                setUnitIfPresent(blockPath, "c_unit", unit);
            elseif contains(blockType, "inductor") && hasNumericValue
                set_param(char(blockPath), "l", char(string(numericValue)));
                setUnitIfPresent(blockPath, "l_unit", unit);
            elseif contains(blockType, "inductor") && strlength(parameterExpression) > 0
                set_param(char(blockPath), "l", char(parameterExpression));
                setUnitIfPresent(blockPath, "l_unit", unit);
            elseif contains(blockType, "voltage") && contains(blockType, "source") && hasNumericValue
                set_param(char(blockPath), "v0", char(string(numericValue)));
                setUnitIfPresent(blockPath, "v0_unit", unit);
            elseif contains(blockType, "voltage") && contains(blockType, "source") && strlength(parameterExpression) > 0
                set_param(char(blockPath), "v0", char(parameterExpression));
                setUnitIfPresent(blockPath, "v0_unit", unit);
            elseif contains(blockType, "current") && contains(blockType, "source") && hasNumericValue
                set_param(char(blockPath), "i0", char(string(numericValue)));
                setUnitIfPresent(blockPath, "i0_unit", unit);
            elseif contains(blockType, "current") && contains(blockType, "source") && strlength(parameterExpression) > 0
                set_param(char(blockPath), "i0", char(parameterExpression));
                setUnitIfPresent(blockPath, "i0_unit", unit);
            end
    end
catch paramError
    messages(end + 1) = "Could not set value for " + componentId + ": " + string(paramError.message); %#ok<AGROW>
end
end

function needsValue = componentNeedsValue(blockType)
needsValue = contains(blockType, "resistor") || contains(blockType, "capacitor") || ...
    contains(blockType, "inductor") || contains(blockType, "source");
end

function expression = parameterValueExpression(componentId, value)
expression = "";
if isempty(value)
    return
end
if ischar(value) || isstring(value)
    raw = strtrim(string(value));
    if strlength(raw) == 0
        return
    end
    lowerRaw = lower(raw);
    if any(lowerRaw == ["unspecified", "unknown", "not specified", "na", "n/a", "[]"])
        expression = "CITT_" + matlab.lang.makeValidName(char(componentId)) + "_value";
        return
    end
    if isParameterExpression(raw)
        expression = raw;
    else
        expression = "CITT_" + matlab.lang.makeValidName(char(componentId)) + "_value";
    end
end
end

function tf = isParameterExpression(value)
value = string(value);
tf = ~isempty(regexp(char(value), "^[A-Za-z]\w*(\s*[\+\-\*/]\s*[A-Za-z0-9_\.]+)*$", "once"));
end

function setUnitIfPresent(blockPath, parameterName, unit)
if strlength(unit) == 0
    return
end
params = get_param(char(blockPath), "DialogParameters");
if isfield(params, parameterName)
    try
        set_param(char(blockPath), char(parameterName), char(unit));
    catch
    end
end
end

function blockInfo = makeBlockInfo(componentId, componentType, blockPath, kind)
blockInfo = struct();
blockInfo.id = string(componentId);
blockInfo.type = string(componentType);
blockInfo.path = string(blockPath);
blockInfo.kind = string(kind);
blockInfo.handles = get_param(char(blockPath), "PortHandles");
end

function position = blockPosition(index)
column = mod(index - 1, 4);
row = floor((index - 1) / 4);
x = 260 + column * 220;
y = 80 + row * 130;
position = [x y x + 120 y + 64];
end

function blockName = uniqueBlockName(componentId, usedNames)
base = matlab.lang.makeValidName(char(componentId));
if strlength(string(base)) == 0
    base = "Component";
end
candidate = string(base);
suffix = 2;
while any(usedNames == candidate)
    candidate = string(base) + "_" + string(suffix);
    suffix = suffix + 1;
end
blockName = candidate;
end

function [portHandle, found] = endpointPort(key, blockInfos, idToIndex)
portHandle = [];
found = false;
[componentId, terminal] = splitEndpointKey(key);
if strlength(componentId) == 0 || ~isKey(idToIndex, char(componentId))
    return
end
info = blockInfos(idToIndex(char(componentId)));
portHandle = terminalPort(info, terminal);
found = ~isempty(portHandle);
end

function portHandle = terminalPort(info, terminal)
terminal = normalizeTerminal(terminal);
handles = info.handles;
kind = string(info.kind);
portHandle = [];
switch kind
    case "op_amp"
        if any(terminal == ["plus", "p", "positive", "noninverting", "inp", "inplus", "in_p"])
            portHandle = handles.LConn(1);
        elseif any(terminal == ["minus", "n", "negative", "inverting", "inn", "inminus", "in_n"])
            portHandle = handles.LConn(2);
        elseif any(terminal == ["out", "output", "o"])
            portHandle = handles.RConn(1);
        end
    case "voltage_sensor"
        if any(terminal == ["plus", "p", "positive", "top", "left", "t1", "1"])
            portHandle = handles.LConn(1);
        elseif any(terminal == ["minus", "n", "negative", "bottom", "right", "t2", "2"])
            portHandle = handles.RConn(2);
        end
    case "current_sensor"
        if any(terminal == ["plus", "p", "positive", "in", "top", "left", "t1", "1"])
            portHandle = handles.LConn(1);
        elseif any(terminal == ["minus", "n", "negative", "out", "bottom", "right", "t2", "2"])
            portHandle = handles.RConn(2);
        end
    otherwise
        if any(terminal == ["plus", "p", "positive", "anode", "top", "left", "t1", "1", "l"])
            portHandle = handles.LConn(1);
        elseif any(terminal == ["minus", "n", "negative", "cathode", "bottom", "right", "t2", "2", "r"])
            portHandle = handles.RConn(1);
        end
end
end

function terminal = normalizeTerminal(terminal)
terminal = lower(string(terminal));
terminal = replace(terminal, "+", "plus");
terminal = replace(terminal, "-", "minus");
terminal = regexprep(terminal, "[^a-z0-9_]", "");
terminal = replace(terminal, "in_p", "inp");
terminal = replace(terminal, "in_n", "inn");
end

function portHandle = firstPhysicalPort(blockPath)
handles = get_param(char(blockPath), "PortHandles");
if ~isempty(handles.LConn)
    portHandle = handles.LConn(1);
elseif ~isempty(handles.RConn)
    portHandle = handles.RConn(1);
else
    portHandle = [];
end
end

function [messages, connectionWarnings, portGroups] = addRequestedOutputScopes(modelName, requestedOutputs, ...
    nodeParent, portGroups, groundRoot, messages, connectionWarnings)
for i = 1:numel(requestedOutputs)
    outputText = string(requestedOutputs{i});
    outputNode = requestedOutputNode(outputText);
    if strlength(outputNode) == 0
        continue
    end
    root = findRoot(nodeParent, endpointKey(outputNode));
    if ~isKey(portGroups, char(root))
        connectionWarnings(end + 1) = "Requested output node is not connected in the model: " + outputText; %#ok<AGROW>
        continue
    end
    ports = uniqueHandles(portGroups(char(root)));
    if isempty(ports)
        continue
    end

    safeName = matlab.lang.makeValidName(char(outputNode));
    y = 640 + i * 95;
    sensorPath = string(modelName) + "/VSensor_" + string(safeName);
    converterPath = string(modelName) + "/PS2SL_" + string(safeName);
    scopePath = string(modelName) + "/Scope_" + string(safeName);
    add_block("fl_lib/Electrical/Electrical Sensors/Voltage Sensor", char(sensorPath), ...
        "Position", [850 y 930 y + 70]);
    add_block("nesl_utility/PS-Simulink Converter", char(converterPath), ...
        "Position", [990 y + 8 1090 y + 62]);
    add_block("simulink/Sinks/Scope", char(scopePath), ...
        "Position", [1140 y + 10 1210 y + 60]);

    sensorHandles = get_param(char(sensorPath), "PortHandles");
    converterHandles = get_param(char(converterPath), "PortHandles");
    scopeHandles = get_param(char(scopePath), "PortHandles");
    portGroups = appendPort(portGroups, root, sensorHandles.LConn(1));
    portGroups = appendPort(portGroups, groundRoot, sensorHandles.RConn(2));
    try
        add_line(modelName, sensorHandles.RConn(1), converterHandles.LConn(1));
        add_line(modelName, converterHandles.Outport(1), scopeHandles.Inport(1), "autorouting", "on");
        messages(end + 1) = "Added voltage sensor and Scope for " + outputText + "."; %#ok<AGROW>
    catch scopeError
        connectionWarnings(end + 1) = "Could not add output scope for " + outputText + ": " + string(scopeError.message); %#ok<AGROW>
    end
end
end

function node = requestedOutputNode(outputText)
node = strtrim(string(outputText));
tokens = regexp(char(node), "^[Vv]\(([^)]+)\)$", "tokens", "once");
if ~isempty(tokens)
    node = string(tokens{1});
end
end

function labels = allEndpointLabels(connections, groundNode)
labels = strings(0, 1);
labels(end + 1) = groundNode;
for i = 1:numel(connections)
    connection = connections{i};
    if ~isstruct(connection)
        continue
    end
    labels(end + 1) = string(fieldOr(connection, "from", "")); %#ok<AGROW>
    labels(end + 1) = string(fieldOr(connection, "to", "")); %#ok<AGROW>
    labels(end + 1) = string(fieldOr(connection, "label", "")); %#ok<AGROW>
end
labels = labels(strlength(labels) > 0);
labels = unique(labels);
end

function key = endpointKey(endpoint)
endpoint = strtrim(string(endpoint));
if strlength(endpoint) == 0
    key = "";
    return
end
endpoint = replace(endpoint, ".", ":");
parts = split(endpoint, ":");
if numel(parts) >= 2
    key = string(parts(1)) + ":" + string(parts(2));
else
    key = endpoint;
end
end

function [componentId, terminal] = splitEndpointKey(key)
parts = split(string(key), ":");
if numel(parts) >= 2
    componentId = string(parts(1));
    terminal = string(parts(2));
else
    componentId = "";
    terminal = "";
end
end

function parent = unionKeys(parent, left, right)
left = char(string(left));
right = char(string(right));
if strlength(string(left)) == 0 || strlength(string(right)) == 0
    return
end
rootLeft = findRoot(parent, left);
rootRight = findRoot(parent, right);
if ~strcmp(rootLeft, rootRight)
    parent(rootRight) = rootLeft;
end
end

function root = findRoot(parent, key)
key = char(string(key));
if ~isKey(parent, key)
    parent(key) = key;
    root = key;
    return
end
root = parent(key);
while isKey(parent, root) && ~strcmp(parent(root), root)
    root = parent(root);
end
end

function groups = appendPort(groups, key, portHandle)
if isempty(portHandle)
    return
end
key = char(string(key));
if isKey(groups, key)
    groups(key) = [groups(key), portHandle];
else
    groups(key) = portHandle;
end
end

function handles = uniqueHandles(handles)
if isempty(handles)
    return
end
handles = unique(handles, "stable");
end

function focusMap = buildFocusMap(spec, blockInfos, modelName)
focusItems = asCellArray(fieldOr(spec, "focus_points", {}));
items = struct([]);
for i = 1:numel(focusItems)
    focus = focusItems{i};
    if ~isstruct(focus)
        continue
    end
    relatedComponents = asStringArray(fieldOr(focus, "related_components", strings(0, 1)));
    blockPaths = strings(0, 1);
    for j = 1:numel(relatedComponents)
        path = blockPathForComponent(relatedComponents(j), blockInfos);
        if strlength(path) > 0
            blockPaths(end + 1) = path; %#ok<AGROW>
        end
    end
    item = struct();
    item.focus_id = string(fieldOr(focus, "id", "focus_" + string(i)));
    item.label = string(fieldOr(focus, "label", item.focus_id));
    item.explanation = string(fieldOr(focus, "reason", ""));
    item.model_paths = string(modelName);
    item.block_paths = blockPaths;
    item.line_handles_or_descriptions = strings(0, 1);
    item.related_components = relatedComponents;
    item.related_nodes = asStringArray(fieldOr(focus, "related_nodes", strings(0, 1)));
    item.teaching_question = string(fieldOr(focus, "teaching_question", ""));
    items = [items; item]; %#ok<AGROW>
end
focusMap = items;
end

function probeMap = buildProbeMap(spec, requestedOutputs, modelName)
focusItems = asCellArray(fieldOr(spec, "focus_points", {}));
items = struct([]);
for i = 1:max(1, numel(requestedOutputs))
    outputText = "";
    if i <= numel(requestedOutputs)
        outputText = string(requestedOutputs{i});
    end
    focusId = "model_output";
    label = "Requested output";
    if ~isempty(focusItems) && isstruct(focusItems{1})
        focusId = string(fieldOr(focusItems{1}, "id", focusId));
        label = string(fieldOr(focusItems{1}, "label", label));
    end
    item = struct();
    item.probe_id = "probe_" + string(i);
    item.focus_id = focusId;
    item.label = label;
    item.target_type = "voltage";
    item.model_paths = string(modelName);
    item.block_paths = strings(0, 1);
    item.quantity = outputText;
    item.unit = "V";
    item.suggested_sensor_or_logging = "Voltage Sensor -> PS-Simulink Converter -> Scope";
    item.instructions = "Use the generated voltage sensor and Scope, or add a Simscape Voltage Sensor at the requested node.";
    items = [items; item]; %#ok<AGROW>
end
probeMap = items;
end

function path = blockPathForComponent(componentId, blockInfos)
path = "";
for i = 1:numel(blockInfos)
    if blockInfos(i).id == string(componentId)
        path = blockInfos(i).path;
        return
    end
end
end

function text = generatedRunnerText(matlabRoot, specSource, scriptPath, modelPath, focusMapPath, probeMapPath, reportPath)
lines = [
    "% Generated by CiTT. Run this file in MATLAB to rebuild the Simscape model."
    "addpath(" + matlabString(matlabRoot) + ");"
    "result = feval('citt.buildSimscapeModelFromSpec', " + matlabString(specSource) + ", struct( ..."
    "    ""ScriptPath"", " + matlabString(scriptPath) + ", ..."
    "    ""ModelPath"", " + matlabString(modelPath) + ", ..."
    "    ""FocusMapPath"", " + matlabString(focusMapPath) + ", ..."
    "    ""ProbeMapPath"", " + matlabString(probeMapPath) + ", ..."
    "    ""ReportPath"", " + matlabString(reportPath) + ", ..."
    "    ""WriteGeneratedScript"", false, ..."
    "    ""RunGeneratedScript"", false, ..."
    "    ""OpenModel"", true));"
    "disp(result.summary);"
];
text = strjoin(lines, newline);
end

function text = matlabString(value)
escaped = strrep(char(string(value)), """", """""");
text = """" + string(escaped) + """";
end

function [spec, source] = readSpec(specInput)
if isstruct(specInput)
    spec = specInput;
    source = "MATLAB struct";
    return
end
path = string(specInput);
if strlength(path) == 0 || exist(path, "file") ~= 2
    error("CiTT:SpecMissing", "Circuit spec JSON was not found: %s", path);
end
spec = jsondecode(fileread(path));
source = path;
end

function rejectBlockingSpec(spec)
problems = strings(0, 1);
if isfield(spec, "unsupported_or_unclear_regions") && ~isempty(spec.unsupported_or_unclear_regions)
    text = valueToText(spec.unsupported_or_unclear_regions);
    if strlength(strtrim(text)) > 0
        problems(end + 1) = "unsupported_or_unclear_regions: " + text; %#ok<AGROW>
    end
end
if ~isempty(problems)
    error("CiTT:AmbiguousCircuitSpec", ...
        "Circuit spec has unclear or unsupported regions, so CiTT will not draw a misleading Simscape model. Clarify first: %s", ...
        strjoin(problems, " | "));
end
end

function notes = ambiguityNotes(spec)
notes = strings(0, 1);
if isfield(spec, "ambiguities") && ~isempty(spec.ambiguities)
    text = valueToText(spec.ambiguities);
    if strlength(strtrim(text)) > 0
        notes(end + 1) = "Gemini ambiguity note: " + text; %#ok<AGROW>
    end
end
end

function value = optionString(options, fieldName, defaultValue)
if isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function value = optionLogical(options, fieldName, defaultValue)
if isfield(options, fieldName)
    value = logical(options.(fieldName));
else
    value = logical(defaultValue);
end
end

function value = fieldOr(data, fieldName, defaultValue)
if isstruct(data) && isfield(data, fieldName)
    value = data.(fieldName);
else
    value = defaultValue;
end
end

function values = asCellArray(value)
if isempty(value)
    values = {};
elseif iscell(value)
    values = value(:)';
elseif isstruct(value)
    values = cell(1, numel(value));
    for i = 1:numel(value)
        values{i} = value(i);
    end
elseif isstring(value)
    values = cellstr(value(:)');
elseif ischar(value)
    values = {value};
else
    values = num2cell(value(:)');
end
end

function values = asStringArray(value)
if isempty(value)
    values = strings(0, 1);
elseif iscell(value)
    values = strings(numel(value), 1);
    for i = 1:numel(value)
        values(i) = string(value{i});
    end
elseif isstring(value)
    values = value(:);
elseif ischar(value)
    values = string(value);
else
    values = string(value(:));
end
end

function [numericValue, ok] = numericScalar(value)
ok = false;
numericValue = [];
if isempty(value)
    return
end
if isnumeric(value) && isscalar(value) && isfinite(value)
    numericValue = value;
    ok = true;
elseif ischar(value) || isstring(value)
    candidate = str2double(string(value));
    if isfinite(candidate)
        numericValue = candidate;
        ok = true;
    end
end
end

function text = valueToText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function writeJson(path, value)
writeText(path, feval('citt.util.jsonEncode', value));
end

function writeReport(path, result)
lines = [
    "# CiTT Simscape Build Report"
    ""
    "Model: " + result.model_path
    "Generated code: " + result.generated_code_path
    "Success: " + string(result.success)
    ""
    "Messages:"
    listLines(result.messages)
    ""
    "Build notes:"
    listLines(result.build_notes)
    ""
    "Unresolved values:"
    listLines(result.unresolved_values)
    ""
    "Unsupported components:"
    listLines(result.unsupported_components)
    ""
    "Connection warnings:"
    listLines(result.connection_warnings)
];
writeText(path, strjoin(lines, newline));
end

function values = listLines(values)
if isempty(values) || all(strlength(string(values)) == 0)
    values = "none";
else
    values = string(values);
    values = values(:);
end
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid < 0
    error("CiTT:WriteFailed", "Could not write: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end
