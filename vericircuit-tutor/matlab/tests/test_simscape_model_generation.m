function test_simscape_model_generation()
%TEST_SIMSCAPEMODELGENERATION Verify Build Model creates real artifacts.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
uniqueName = "test_citt_generated_model_" + string(feature('getpid'));
specPath = fullfile(config.WorkDir, uniqueName + "_spec.json");
scriptPath = fullfile(config.WorkDir, uniqueName + "_build.m");
modelPath = fullfile(config.WorkDir, uniqueName + ".slx");
focusPath = fullfile(config.WorkDir, uniqueName + "_focus.json");
probePath = fullfile(config.WorkDir, uniqueName + "_probe.json");
reportPath = fullfile(config.WorkDir, uniqueName + "_report.md");

writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
result = feval('citt.buildSimscapeModelFromSpec', specPath, struct( ...
    "ScriptPath", scriptPath, ...
    "ModelPath", modelPath, ...
    "FocusMapPath", focusPath, ...
    "ProbeMapPath", probePath, ...
    "ReportPath", reportPath, ...
    "OpenModel", false));

assert(result.success);
assert(exist(scriptPath, "file") == 2);
assert(exist(modelPath, "file") == 2);
assert(exist(focusPath, "file") == 2);
assert(exist(probePath, "file") == 2);
assert(exist(reportPath, "file") == 2);

[~, modelName, ~] = fileparts(modelPath);
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

symbolicName = "test_citt_symbolic_model_" + string(feature('getpid'));
symbolicSpecPath = fullfile(config.WorkDir, symbolicName + "_spec.json");
symbolicModelPath = fullfile(config.WorkDir, symbolicName + ".slx");
symbolicScriptPath = fullfile(config.WorkDir, symbolicName + "_build.m");
symbolicFocusPath = fullfile(config.WorkDir, symbolicName + "_focus.json");
symbolicProbePath = fullfile(config.WorkDir, symbolicName + "_probe.json");
symbolicReportPath = fullfile(config.WorkDir, symbolicName + "_report.md");
symbolicSpec = localSpec();
symbolicSpec.components(1).value = "V_c";
symbolicSpec.components(2).value = "unspecified";
symbolicSpec.ambiguities = ["The exact value of Vc is intentionally symbolic."];
writeText(symbolicSpecPath, feval('citt.util.jsonEncode', symbolicSpec));
symbolicResult = feval('citt.buildSimscapeModelFromSpec', symbolicSpecPath, struct( ...
    "ScriptPath", symbolicScriptPath, ...
    "ModelPath", symbolicModelPath, ...
    "FocusMapPath", symbolicFocusPath, ...
    "ProbeMapPath", symbolicProbePath, ...
    "ReportPath", symbolicReportPath, ...
    "OpenModel", false));

assert(symbolicResult.success);
assert(exist(symbolicModelPath, "file") == 2);
assert(any(contains(symbolicResult.unresolved_values, "V_c")));
assert(any(contains(symbolicResult.unresolved_values, "CITT_R1_value")));
assert(~isempty(symbolicResult.build_notes));

[~, symbolicModelName, ~] = fileparts(symbolicModelPath);
if bdIsLoaded(symbolicModelName)
    close_system(symbolicModelName, 0);
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
spec = struct();
spec.circuit_type = "rc_low_pass";
spec.components = [
    component("V1", "voltage_source", "Vin", 1, "V", ["positive", "negative"])
    component("R1", "resistor", "R1", 1000, "Ohm", ["left", "right"])
    component("C1", "capacitor", "C1", 1e-6, "F", ["top", "bottom"])
];
spec.nodes = ["n_in", "n_out", "0"];
spec.connections = [
    connection("V1.positive", "R1.left", "n_in")
    connection("R1.right", "C1.top", "n_out")
    connection("V1.negative", "C1.bottom", "0")
];
spec.ground_node = "0";
spec.sources = ["V1"];
spec.requested_outputs = ["V(n_out)"];
spec.likely_analysis = "transient";
spec.assumptions = strings(0, 1);
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
spec.suggested_simscape_blocks = ["Resistor", "Capacitor", "Electrical Reference", "Solver Configuration", "Voltage Sensor"];
spec.focus_points = focus("rc_output", "RC output node", "Output node for the low-pass response.", ["R1", "C1"], ["n_out"], "Why is n_out the natural probe point?");
spec.teaching_focus_points = spec.focus_points;
end

function c = component(id, type, label, value, unit, terminals)
c = struct("id", id, "type", type, "label", label, "value", value, ...
    "unit", unit, "terminals", terminals, "confidence", 1.0);
end

function c = connection(from, to, label)
c = struct("from", from, "to", to, "label", label, "confidence", 1.0);
end

function f = focus(id, label, reason, components, nodes, question)
f = struct("id", id, "label", label, "reason", reason, ...
    "related_components", components, "related_nodes", nodes, ...
    "teaching_question", question);
end
