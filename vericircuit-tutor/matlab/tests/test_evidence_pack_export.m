function test_evidence_pack_export()
%TEST_EVIDENCE_PACK_EXPORT Verify proposal evidence pack export.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');

specPath = fullfile(config.WorkDir, "test_evidence_spec.json");
focusPath = fullfile(config.WorkDir, "test_evidence_focus_map.json");
probePath = fullfile(config.WorkDir, "test_evidence_probe_map.json");
modelPath = fullfile(config.WorkDir, "test_evidence_model.slx");
packPath = fullfile(config.WorkDir, "test_citt_evidence_pack.md");

writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
writeText(focusPath, feval('citt.util.jsonEncode', localFocusMap()));
writeText(probePath, feval('citt.util.jsonEncode', localProbeMap()));
writeText(modelPath, "placeholder model artifact for exporter test");

context = struct();
context.ImagePath = "";
context.PromptText = "RC anti-aliasing filter for ECG ADC lab";
context.Spec = [];
context.SpecPath = specPath;
context.AgentTaskPath = fullfile(config.WorkDir, "test_agent_task.md");
context.AgentRun = struct("mode", "test", "success", true);
context.ModelPath = modelPath;
context.FocusMapPath = focusPath;
context.ProbeMapPath = probePath;
context.LastModelCheck = struct( ...
    "success", true, ...
    "model_path", modelPath, ...
    "report_path", fullfile(config.WorkDir, "test_model_check_report.md"), ...
    "messages", ["Diagram update completed."; "Model checksum captured."], ...
    "error", "");
context.LastSimulation = struct( ...
    "success", true, ...
    "model_path", modelPath, ...
    "summary_path", fullfile(config.WorkDir, "test_simulation_summary.json"), ...
    "messages", ["Simulation completed."], ...
    "output_variables", ["logsout"]);
context.LastProbe = struct("success", true, "target_id", "output_node");
context.LabCsvPath = "";
context.LastLabDelta = localLabDelta();
context.EvidencePackPath = packPath;

result = feval('citt.exportEvidencePack', context, struct("OutputPath", packPath));
assert(result.success);
assert(exist(packPath, "file") == 2);

text = string(fileread(packPath));
assert(contains(text, "# CiTT Performance Evidence Pack"));
assert(contains(text, "## 6. Requirement Pass/Fail Table"));
assert(contains(text, "## 12. Risk Table"));
assert(contains(text, "## 13. BMES Functional Proof Draft"));
assert(contains(text, "PASS"));
assert(result.status_summary.pass >= 6);
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
spec.circuit_type = "rc_antialias_adc";
spec.components = component;
spec.nodes = ["vin", "vout", "gnd"];
spec.requested_outputs = ["cutoff_frequency", "vout"];
spec.likely_analysis = "ac_frequency_response";
spec.assumptions = ["educational ECG front-end model"];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
end

function focusMap = localFocusMap()
item = struct();
item.focus_id = "output_node";
item.label = "Output node";
item.explanation = "Low-pass output before ADC sampling.";
item.model_paths = ["test_evidence_model/Output Sensor"];
item.block_paths = ["test_evidence_model/Voltage Sensor"];
item.related_components = ["R1", "C1"];
item.related_nodes = ["vout"];
item.teaching_question = "Why does this node define the anti-aliasing output?";
focusMap = struct("focus_map", item);
end

function probeMap = localProbeMap()
item = struct();
item.probe_id = "probe_vout";
item.label = "Probe Vout";
item.target_paths = ["test_evidence_model/Output Sensor"];
item.quantity = "voltage";
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

cause = struct();
cause.id = "component_tolerance";
cause.label = "component tolerance";
cause.explanation = "Compare actual resistor/capacitor values against nominal values.";
cause.severity = "check";

report = struct();
report.success = true;
report.csv_path = "";
report.report_path = "";
report.rows = row;
report.likely_causes = cause;
report.next_probe_suggestion = "Probe vout.";
end
