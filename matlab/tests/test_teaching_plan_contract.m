function test_teaching_plan_contract()
%TEST_TEACHING_PLAN_CONTRACT Verify teaching plan requires generated focus map.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
specPath = fullfile(config.WorkDir, "test_citt_teaching_spec.json");
focusPath = fullfile(config.WorkDir, "test_citt_focus_map.json");
planPath = fullfile(config.WorkDir, "test_citt_teaching_plan.json");

writeText(specPath, feval('citt.util.jsonEncode', localSpec()));
writeText(focusPath, feval('citt.util.jsonEncode', localFocusMap()));

built = feval('citt.buildTeachingPlan', specPath, focusPath, [], [], struct("OutputPath", planPath));
assert(built.success);
assert(built.step_count == 1);
assert(exist(planPath, "file") == 2);
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
spec.requested_outputs = ["V(n_out)"];
spec.likely_analysis = "transient_or_ac";
end

function focusMap = localFocusMap()
item = struct();
item.focus_id = "rc_output";
item.label = "RC output node";
item.explanation = "Generated focus map point.";
item.model_paths = ["citt_generated_model/RC Output"];
item.block_paths = ["citt_generated_model/Voltage Sensor"];
item.line_handles_or_descriptions = strings(0, 1);
item.related_components = ["R1", "C1"];
item.related_nodes = ["n_out"];
item.teaching_question = "Why is this the output node?";
focusMap = struct("focus_map", item);
end
