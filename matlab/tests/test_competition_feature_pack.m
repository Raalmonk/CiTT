function test_competition_feature_pack()
%TEST_COMPETITION_FEATURE_PACK Smoke test the BMES competition feature set.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');

prefix = fullfile(config.WorkDir, "test_competition_pack");
specPath = prefix + "_spec.json";
focusPath = prefix + "_focus.json";
probePath = prefix + "_probe.json";
writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
writeText(focusPath, feval('citt.util.jsonEncode', localFocusMap()));
writeText(probePath, feval('citt.util.jsonEncode', localProbeMap()));

context = struct();
context.SpecPath = specPath;
context.Spec = [];
context.FocusMapPath = focusPath;
context.ProbeMapPath = probePath;
context.LastModelCheck = struct("success", true, "report_path", prefix + "_check.md", "messages", ["ok"]);
context.LastSimulation = struct("success", true, "summary_path", prefix + "_sim.json", ...
    "output_variables", ["logsout"], "sampling_frequency_hz", 500, "highest_signal_frequency_hz", 150, ...
    "clipping_detected", false, "attenuation_60hz_db", -14.2);
context.LastLabDelta = localLabDelta();

requirements = feval('citt.runRequirementChecks', context, struct( ...
    "OutputPath", prefix + "_requirements.json", ...
    "MarkdownPath", prefix + "_requirements.md"));
sweep = feval('citt.runParameterSweep', context, struct( ...
    "OutputPath", prefix + "_sweep.json", ...
    "MarkdownPath", prefix + "_sweep.md"));
faults = feval('citt.runFaultInjection', context, struct( ...
    "OutputPath", prefix + "_faults.json", ...
    "MarkdownPath", prefix + "_faults.md"));
explainability = feval('citt.buildExplainabilityMap', context, struct( ...
    "OutputPath", prefix + "_explain.json", ...
    "MarkdownPath", prefix + "_explain.md"));
assessment = feval('citt.runLearningAssessment', struct( ...
    "concept", "cutoff output node capacitor", ...
    "before_answer", "I am not sure where the output is.", ...
    "after_answer", "The output node is after the resistor and capacitor, so the cutoff depends on R and C.", ...
    "hint_levels_used", 2), struct( ...
    "OutputPath", prefix + "_assessment.json", ...
    "MarkdownPath", prefix + "_assessment.md"));
economics = feval('citt.buildEconomicsPlan', struct( ...
    "Students", 24, ...
    "OutputPath", prefix + "_economics.json", ...
    "MarkdownPath", prefix + "_economics.md"));
scope = feval('citt.buildScopeGuardrail', context, struct( ...
    "OutputPath", prefix + "_scope.json", ...
    "MarkdownPath", prefix + "_scope.md"));

assert(requirements.success);
assert(sweep.success);
assert(~isempty(sweep.rows));
assert(faults.success);
assert(numel(faults.rows) >= 8);
assert(explainability.success);
assert(~isempty(explainability.actions));
assert(assessment.success);
assert(assessment.learning_gain > 0);
assert(economics.success);
assert(economics.deployment.students == 24);
assert(scope.success);
assert(scope.patient_connected_trigger_detected);
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
component = struct("id", "R1", "type", "resistor", "value", "10 kOhm");
component(2) = struct("id", "C1", "type", "capacitor", "value", "0.39 uF");

spec = struct();
spec.circuit_type = "ecg_rc_antialias_adc";
spec.components = component;
spec.nodes = ["vin", "vout", "gnd"];
spec.requested_outputs = ["cutoff_frequency", "vout"];
spec.likely_analysis = "ac_frequency_response";
spec.cutoff_frequency_hz = 40;
spec.sampling_frequency_hz = 500;
spec.highest_signal_frequency_hz = 150;
spec.assumptions = ["educational ECG front-end model"];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
end

function focusMap = localFocusMap()
item = struct();
item.focus_id = "output_node";
item.label = "Output node";
item.explanation = "Low-pass output before ADC sampling.";
item.model_paths = ["test_model/Output Sensor"];
item.block_paths = ["test_model/Voltage Sensor"];
item.related_components = ["R1", "C1"];
item.related_nodes = ["vout"];
item.teaching_question = "Why does this output node define the anti-aliasing response?";
focusMap = struct("focus_map", item);
end

function probeMap = localProbeMap()
item = struct();
item.probe_id = "probe_vout";
item.focus_id = "output_node";
item.label = "Probe Vout";
item.target_paths = ["test_model/Output Sensor"];
item.quantity = "voltage";
item.instructions = "Place voltage sensor at vout.";
probeMap = struct("probe_map", item);
end

function report = localLabDelta()
row = struct();
row.quantity = "fc_hz";
row.hand_value = 40;
row.simulation_value = 39.8;
row.measured_value = 41.2;
row.unit = "Hz";
row.absolute_difference = 1.4;
row.percent_difference = 3.52;

report = struct();
report.success = true;
report.csv_path = "";
report.report_path = "";
report.rows = row;
end
