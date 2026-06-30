function test_agent_task_generation()
%TEST_AGENT_TASK_GENERATION Verify SATK task text contains required contract.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
specPath = fullfile(config.WorkDir, "test_citt_parse_spec.json");
writeText(specPath, feval('citt.util.jsonEncode', localSpec()));

taskPath = fullfile(config.WorkDir, "test_citt_agent_task.md");
result = feval('citt.buildAgentTask', specPath, struct("TaskPath", taskPath));

assert(result.success);
text = fileread(taskPath);
assert(contains(text, "Simulink Agentic Toolkit"));
assert(contains(text, "model_overview"));
assert(contains(text, "model_read"));
assert(contains(text, "model_edit"));
assert(contains(text, "model_check"));
assert(contains(text, "model_query_params"));
assert(contains(text, "model_resolve_params"));
assert(contains(text, "Simscape-first"));
assert(contains(text, "Electrical Reference"));
assert(contains(text, "Solver Configuration"));
assert(contains(text, "Repo-Local SATK Agent Instructions"));
assert(contains(text, "CiTT-specific SATK agent addendum"));
assert(contains(text, "Simscape Utilization Contract"));
assert(contains(text, "PS-Simulink Converter"));
assert(contains(text, "Prefer plain text"));
assert(contains(text, "LaTeX"));
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
    component("V1", "voltage_source", "Vin", 1, "V", ["n_in", "0"])
    component("R1", "resistor", "R1", 1000, "ohm", ["n_in", "n_out"])
    component("C1", "capacitor", "C1", 1e-6, "F", ["n_out", "0"])
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
spec.likely_analysis = "transient_or_ac";
spec.assumptions = ["Ideal source", "Nominal component values"];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
spec.suggested_simscape_blocks = ["Resistor", "Capacitor", "Electrical Reference", "Solver Configuration", "Voltage Sensor"];
spec.focus_points = focus("rc_output", "RC output node", "Output node sets the measured low-pass response.", ["R1", "C1"], ["n_out"], "Why is n_out the natural probe point?");
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
