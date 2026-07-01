function test_tutor_turn_planner_contract()
%TEST_TUTOR_TURN_PLANNER_CONTRACT Verify dynamic tutor decisions update student evidence.

repoMatlabRoot = fileparts(fileparts(mfilename("fullpath")));
addpath(repoMatlabRoot);
config = feval('citt.loadConfig');
if strlength(strtrim(config.AgentCommand)) == 0
    error("CiTT:TestSkipped", ...
        "No user-selected CITT_AGENT_COMMAND is configured; real tutor CLI contract test skipped.");
end

prefix = fullfile(config.WorkDir, "test_tutor_turn");
specPath = prefix + "_spec.json";
focusPath = prefix + "_focus.json";
probePath = prefix + "_probe.json";
tracePath = prefix + "_trace.json";
traceMarkdownPath = prefix + "_trace.md";
cleanup = onCleanup(@() cleanupFiles([string(specPath), string(focusPath), string(probePath), ...
    string(tracePath), string(traceMarkdownPath)]));

writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
writeText(focusPath, feval('citt.util.jsonEncode', localFocusMap()));
writeText(probePath, feval('citt.util.jsonEncode', localProbeMap()));

state = struct();
state.TeachingPlan = localTeachingPlan();
state.TeachingStepIndex = 1;
state.HintLevel = 0;
state.StudentModel = feval('citt.defaultStudentModel');
state.SpecPath = specPath;
state.FocusMapPath = focusPath;
state.ProbeMapPath = probePath;
state.ModelPath = "";

turn = feval('citt.runTutorTurn', state, struct( ...
    "StudentText", "The output is across the resistor because it is first.", ...
    "Action", "student_message", ...
    "ExecuteTools", false));

assert(turn.intent == "answer");
assert(strlength(strtrim(turn.message)) > 0);
assert(ismember(turn.student_level, ["novice", "developing", "advanced"]));
assert(ismember(turn.pedagogical_move, ["ask", "hint", "probe", "highlight", "simulate", "compare", "reveal", "advance", "remediate"]));
assert(ismember(turn.tool_action, ["none", "highlight_focus", "measure_probe", "run_simulation", "run_bode", "next_step", "reveal"]));
assert(numel(turn.student_model.turns) == 1);

state.StudentModel = turn.student_model;
trace = feval('citt.buildLearningTraceability', state, struct( ...
    "OutputPath", tracePath, ...
    "MarkdownPath", traceMarkdownPath));
assert(trace.success);
assert(trace.student_model.turn_count == 1);
assert(trace.objectives(1).student_evidence.tutor_turn_count == 1);
assert(strlength(strtrim(trace.objectives(1).student_evidence.latest_pedagogical_move)) > 0);
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
component = struct("id", "R1", "type", "resistor", "value", "39.8 kOhm");
component(2) = struct("id", "C1", "type", "capacitor", "value", "100 nF");

spec = struct();
spec.circuit_type = "rc_lowpass";
spec.components = component;
spec.nodes = ["vin", "vout", "gnd"];
spec.ground_node = "gnd";
spec.requested_outputs = ["Vout", "cutoff_frequency"];
spec.likely_analysis = "transient_or_ac";
spec.assumptions = ["educational model"];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
end

function focusMap = localFocusMap()
item = struct();
item.focus_id = "output_node";
item.label = "Output node";
item.explanation = "The low-pass output is the capacitor node relative to ground.";
item.block_paths = ["test_model/R1", "test_model/C1", "test_model/Vout Sensor"];
item.related_components = ["R1", "C1"];
item.related_nodes = ["vout", "gnd"];
item.teaching_question = "Where is Vout measured in this low-pass model?";
focusMap = struct("focus_map", item);
end

function probeMap = localProbeMap()
item = struct();
item.probe_id = "vout_measurement";
item.focus_id = "output_node";
item.label = "Vout measurement";
item.block_paths = ["test_model/Vout Sensor"];
item.quantity = "voltage";
item.unit = "V";
probeMap = struct("probe_map", item);
end

function plan = localTeachingPlan()
step = struct();
step.id = "step_01";
step.focus_id = "output_node";
step.title = "Output node";
step.concept = "Vout is measured at the capacitor node relative to ground.";
step.student_question = "Where is Vout measured in this low-pass model?";
step.expected_reasoning = "Name the capacitor node and electrical reference.";
step.reveal_hint = "Look for the Vout probe and its reference node.";
step.common_mistake = "Treating resistor voltage as the requested output.";
step.optional_value_reference = "";
plan = struct("steps", step);
end
