function test_probe_preview_measurement_no_sim()
%TEST_PROBE_PREVIEW_MEASUREMENT_NO_SIM Natural measure commands should return quickly.

config = feval('citt.loadConfig');
modelName = "citt_test_probe_preview";
modelPath = fullfile(config.WorkDir, modelName + ".slx");
probePath = fullfile(config.WorkDir, "test_probe_preview_map.json");

cleanupArtifacts(modelName, [string(modelPath), string(probePath)]);
cleanup = onCleanup(@() cleanupArtifacts(modelName, [string(modelPath), string(probePath)]));

new_system(modelName);
add_block("simulink/Sources/Constant", modelName + "/source_voltage", "Value", "1");
add_block("simulink/Sinks/Terminator", modelName + "/sink");
add_line(modelName, "source_voltage/1", "sink/1");
save_system(modelName, modelPath);

probe = struct();
probe.probe_id = "PR_SOURCE_VOLTAGE";
probe.focus_id = "FP_SOURCE";
probe.label = "source voltage";
probe.target_type = "Simulink source output";
probe.model_paths = string(modelName);
probe.block_paths = string(modelName + "/source_voltage");
probe.quantity = "source voltage";
probe.unit = "V";
probe.suggested_sensor_or_logging = "Use the existing source output for preview.";
probe.instructions = "Preview only; do not run simulation.";

writeJson(probePath, probe);

state = feval('citt.appState');
state.ModelPath = string(modelPath);
state.SpecPath = "";
state.ProbeMapPath = string(probePath);

started = tic;
result = feval('citt.runNaturalCommand', "measure source voltage", state);
elapsed = toc(started);

assert(result.action == "measure");
assert(result.success, "Preview measure should match a probe target.");
assert(elapsed < 5, "Preview measure should not run a blocking simulation.");
assert(isfield(result.details, "measurement"), "Preview measure should include a user-facing measurement summary.");
assert(~result.details.measurement.success, "Preview-only measurement should not claim numeric simulation evidence.");
assert(contains(result.details.measurement.message, "Preview-only measurement target matched"));
assert(result.details.measurement.block_path == string(modelName + "/source_voltage"));
end

function writeJson(path, value)
fid = fopen(path, "w");
assert(fid > 0, "Could not write probe test JSON.");
cleaner = onCleanup(@() fclose(fid));
fprintf(fid, "%s", jsonencode(value, "PrettyPrint", true));
clear cleaner
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
