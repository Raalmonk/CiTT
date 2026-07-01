function test_satk_teaching_evidence_layer()
%TEST_SATK_TEACHING_EVIDENCE_LAYER Verify SATK teaching evidence artifacts.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');

prefix = fullfile(config.WorkDir, "test_satk_layer");
specPath = prefix + "_spec.json";
focusPath = prefix + "_focus.json";
probePath = prefix + "_probe.json";
modelPath = prefix + "_model.slx";
artifactPaths = [
    string(specPath)
    string(focusPath)
    string(probePath)
    string(modelPath)
    string(prefix + "_tests.feature")
    string(prefix + "_manifest.json")
    string(prefix + "_model_test_task.md")
    string(prefix + "_review.json")
    string(prefix + "_review.md")
    string(prefix + "_trace.json")
    string(prefix + "_trace.md")
    string(prefix + "_objectives.yaml")
    string(prefix + "_scenario_spec.json")
    string(prefix + "_scenarios.json")
    string(prefix + "_scenarios.md")
];
cleanup = onCleanup(@() cleanupFiles(artifactPaths));

writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
writeText(focusPath, feval('citt.util.jsonEncode', localFocusMap()));
writeText(probePath, feval('citt.util.jsonEncode', localProbeMap()));

context = struct();
context.SpecPath = specPath;
context.FocusMapPath = focusPath;
context.ProbeMapPath = probePath;
context.ModelPath = modelPath;
context.TeachingPlan = localTeachingPlan();
context.LastAssessment = struct("classification", "developing", "hint_levels_used", 1);

generated = feval('citt.generateModelTests', context, struct( ...
    "FeaturePath", prefix + "_tests.feature", ...
    "ManifestPath", prefix + "_manifest.json"));
assert(generated.success);
assert(exist(generated.feature_path, "file") == 2);
assert(contains(string(fileread(generated.feature_path)), "CiTT_TestInterface"));

task = feval('citt.buildModelTestTask', context, struct("TaskPath", prefix + "_model_test_task.md"));
assert(task.success);
taskText = string(fileread(task.task_path));
assert(contains(taskText, "testing-simulink-models"));
assert(contains(taskText, "model_test"));

review = feval('citt.runTeachingModelReview', context, struct( ...
    "OutputPath", prefix + "_review.json", ...
    "MarkdownPath", prefix + "_review.md"));
assert(isfield(review, "checks"));
assert(numel(review.checks) == 8);
assert(exist(review.markdown_path, "file") == 2);

trace = feval('citt.buildLearningTraceability', context, struct( ...
    "OutputPath", prefix + "_trace.json", ...
    "MarkdownPath", prefix + "_trace.md"));
assert(trace.success);
assert(~isempty(trace.objectives));
assert(exist(trace.markdown_path, "file") == 2);

objectives = feval('citt.exportLearningObjectives', struct("LastLearningTraceability", trace), struct( ...
    "YamlPath", prefix + "_objectives.yaml"));
assert(objectives.success);
assert(exist(objectives.yaml_path, "file") == 2);

scenarioSpec = feval('citt.buildSimulationScenarios', context, struct("OutputPath", prefix + "_scenario_spec.json"));
assert(scenarioSpec.success);
assert(numel(scenarioSpec.scenarios) >= 2);

scenarioReport = feval('citt.runSimulationScenarios', context, struct( ...
    "OutputPath", prefix + "_scenarios.json", ...
    "MarkdownPath", prefix + "_scenarios.md"));
assert(isfield(scenarioReport, "scenarios"));
assert(exist(scenarioReport.markdown_path, "file") == 2);
assert(~scenarioReport.success, "Missing model scenarios must not be reported as successful.");
assert(scenarioReport.summary.not_run > 0, "Missing model scenarios should be counted as NOT_RUN.");
scenarioMarkdown = string(fileread(scenarioReport.markdown_path));
assert(contains(scenarioMarkdown, "Success: false"));

dataset = feval('citt.validateTeachingTasks');
assert(dataset.success);
assert(numel(dataset.tasks) >= 3);
end

function cleanupFiles(paths)
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
component = struct("id", "R1", "type", "resistor", "label", "R1", "value", "39.8 kOhm", "unit", "ohm", "terminals", ["vin", "vout"], "confidence", 1.0);
component(2) = struct("id", "C1", "type", "capacitor", "label", "C1", "value", "100 nF", "unit", "F", "terminals", ["vout", "gnd"], "confidence", 1.0);
spec = struct();
spec.circuit_type = "rc_lowpass";
spec.components = component;
spec.connections = struct("from", "R1.right", "to", "C1.top", "label", "vout", "confidence", 1.0);
spec.nodes = ["vin", "vout", "gnd"];
spec.ground_node = "gnd";
spec.sources = ["Vin"];
spec.requested_outputs = ["Vout", "cutoff_frequency"];
spec.likely_analysis = "transient_or_ac";
spec.assumptions = ["educational model"];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
spec.suggested_simscape_blocks = ["Resistor", "Capacitor", "Voltage Sensor"];
spec.focus_points = struct("id", "cutoff_time_constant", "label", "RC time constant", ...
    "reason", "R and C set the pole.", "related_components", ["R1", "C1"], ...
    "related_nodes", ["vout"], "teaching_question", "Why does R*C set cutoff?");
spec.teaching_focus_points = spec.focus_points;
end

function focusMap = localFocusMap()
item = struct();
item.focus_id = "cutoff_time_constant";
item.label = "RC time constant";
item.explanation = "R1 and C1 set the low-pass pole.";
item.model_paths = ["test_satk_layer_model/CiTT_PhysicalCircuit"];
item.block_paths = ["test_satk_layer_model/R1", "test_satk_layer_model/C1"];
item.related_components = ["R1", "C1"];
item.related_nodes = ["vout"];
item.teaching_question = "Why does R*C set cutoff?";
focusMap = struct("focus_map", item);
end

function probeMap = localProbeMap()
item = struct();
item.probe_id = "vout_measurement";
item.focus_id = "cutoff_time_constant";
item.label = "Vout measurement";
item.model_paths = ["test_satk_layer_model/CiTT_TestInterface"];
item.block_paths = ["test_satk_layer_model/Vout"];
item.quantity = "voltage";
item.unit = "V";
item.instructions = "Measure Vout through a PS-Simulink Converter.";
probeMap = struct("probe_map", item);
end

function plan = localTeachingPlan()
step = struct();
step.step_id = "step_01";
step.focus_id = "cutoff_time_constant";
step.title = "RC cutoff";
step.student_question = "Why does R*C set cutoff?";
plan = struct("steps", step);
end
