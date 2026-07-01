function test_simulation_scenarios_local_model()
%TEST_SIMULATION_SCENARIOS_LOCAL_MODEL Run SimulationInput scenarios on a real model.

addpath(fileparts(fileparts(mfilename("fullpath"))));
if exist("new_system", "file") ~= 2 && exist("new_system", "builtin") ~= 5
    error("CiTT:TestSkipped", "Simulink is unavailable in this MATLAB session.");
end
if exist("Simulink.SimulationInput", "class") ~= 8
    error("CiTT:TestSkipped", "Simulink.SimulationInput is unavailable in this MATLAB session.");
end

config = feval('citt.loadConfig');
prefix = fullfile(config.WorkDir, "test_simulation_scenarios_local");
modelName = "test_citt_simulation_scenarios_model";
modelPath = fullfile(config.WorkDir, modelName + ".slx");
specPath = prefix + "_spec.json";
focusPath = prefix + "_focus.json";
probePath = prefix + "_probe.json";
artifactPaths = [
    string(modelPath)
    string(specPath)
    string(focusPath)
    string(probePath)
    string(prefix + "_scenarios.json")
    string(prefix + "_scenarios.md")
];

cleanupArtifacts(modelName, artifactPaths);
cleanup = onCleanup(@() cleanupArtifacts(modelName, artifactPaths));

writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
writeText(focusPath, feval('citt.util.jsonEncode', localFocusMap(modelName)));
writeText(probePath, feval('citt.util.jsonEncode', localProbeMap(modelName)));
createSignalInterfaceModel(modelName, modelPath);

context = struct();
context.SpecPath = specPath;
context.FocusMapPath = focusPath;
context.ProbeMapPath = probePath;
context.ModelPath = modelPath;
context.LabCsvPath = "";

scenarioReport = feval('citt.runSimulationScenarios', context, struct( ...
    "OutputPath", prefix + "_scenarios.json", ...
    "MarkdownPath", prefix + "_scenarios.md"));

assert(scenarioReport.success, "All local SimulationInput scenarios should pass.");
assert(scenarioReport.summary.not_run == 0, "Local model scenarios should not be NOT_RUN.");
assert(scenarioReport.summary.fail == 0, "Local model scenarios should not fail.");
assert(scenarioReport.summary.pass == numel(scenarioReport.scenarios), "Every scenario should pass.");
assert(all(string({scenarioReport.scenarios.status}) == "PASS"));
hasVout = false;
for i = 1:numel(scenarioReport.scenarios)
    hasVout = hasVout || any(string(scenarioReport.scenarios(i).output_variables) == "Vout");
end
assert(hasVout, "The fixture should emit Vout as simulation evidence.");
end

function createSignalInterfaceModel(modelName, modelPath)
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
if exist(modelPath, "file") == 2
    delete(modelPath);
end

new_system(modelName);
add_block("simulink/Sources/Step", modelName + "/Vin", ...
    "Time", "0.1", "Before", "0", "After", "1");
add_block("simulink/Ports & Subsystems/Subsystem", modelName + "/CiTT_TestInterface");
interfacePath = modelName + "/CiTT_TestInterface";
set_param(interfacePath + "/In1", "Name", "Vin");
set_param(interfacePath + "/Out1", "Name", "Vout");
add_block("simulink/Sinks/To Workspace", modelName + "/VoutLog", ...
    "VariableName", "Vout", "SaveFormat", "Array");
add_line(modelName, "Vin/1", "CiTT_TestInterface/1");
add_line(modelName, "CiTT_TestInterface/1", "VoutLog/1");
set_param(modelName, "StopTime", "1");
save_system(modelName, modelPath);
close_system(modelName, 0);
end

function cleanupArtifacts(modelName, paths)
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
for i = 1:numel(paths)
    if exist(paths(i), "file") == 2
        delete(paths(i));
    end
end
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end

function spec = localSpec()
component = struct("id", "R1", "type", "resistor", "label", "R1", "value", "1 kOhm", "unit", "ohm", "terminals", ["vin", "vout"], "confidence", 1.0);
component(2) = struct("id", "C1", "type", "capacitor", "label", "C1", "value", "1 uF", "unit", "F", "terminals", ["vout", "gnd"], "confidence", 1.0);
spec = struct();
spec.circuit_type = "signal_level_test_interface";
spec.components = component;
spec.nodes = ["vin", "vout", "gnd"];
spec.ground_node = "gnd";
spec.sources = ["Vin"];
spec.requested_outputs = ["Vout"];
spec.likely_analysis = "transient";
spec.assumptions = ["Signal-level fixture used only for SimulationInput test execution."];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
end

function focusMap = localFocusMap(modelName)
item = struct();
item.focus_id = "signal_interface_vout";
item.label = "Signal interface output";
item.explanation = "The test fixture exposes a bounded signal-level Vout for SimulationInput.";
item.model_paths = [modelName + "/CiTT_TestInterface"];
item.block_paths = [modelName + "/CiTT_TestInterface", modelName + "/VoutLog"];
item.related_components = ["R1", "C1"];
item.related_nodes = ["vout"];
item.teaching_question = "What evidence tells us this scenario actually simulated?";
focusMap = struct("focus_map", item);
end

function probeMap = localProbeMap(modelName)
item = struct();
item.probe_id = "fixture_vout";
item.focus_id = "signal_interface_vout";
item.label = "Fixture Vout";
item.model_paths = [modelName + "/CiTT_TestInterface"];
item.block_paths = [modelName + "/VoutLog"];
item.quantity = "voltage";
item.unit = "V";
item.instructions = "Read the Vout variable emitted by To Workspace.";
probeMap = struct("probe_map", item);
end
