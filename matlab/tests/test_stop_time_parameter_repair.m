function test_stop_time_parameter_repair()
%TEST_STOP_TIME_PARAMETER_REPAIR Undefined StopTime symbols are prepared.

config = feval('citt.loadConfig');
modelName = "citt_test_stop_time_parameter";
modelPath = fullfile(config.WorkDir, modelName + ".slx");
reportPath = fullfile(config.WorkDir, "test_stop_time_model_check.md");
summaryPath = fullfile(config.WorkDir, "test_stop_time_simulation.json");

if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
if exist(modelPath, "file") == 2
    delete(modelPath);
end

new_system(modelName);
cleanup = onCleanup(@() cleanupModel(modelName));
add_block("simulink/Sources/Step", modelName + "/step", "Time", "t_step");
add_block("simulink/Math Operations/Gain", modelName + "/gain", "Gain", "A_clamp_gain");
add_block("simulink/Sinks/Terminator", modelName + "/y");
add_line(modelName, "step/1", "gain/1");
add_line(modelName, "gain/1", "y/1");
set_param(modelName, "StopTime", "t_stop");
save_system(modelName, modelPath);
close_system(modelName, 0);

checked = feval('citt.runModelCheck', modelPath, struct("ReportPath", reportPath));
assert(checked.success, "Model check should pass after StopTime preparation.");
assert(any(contains(checked.messages, "t_stop")), "Model check should report the prepared StopTime symbol.");
assert(isfield(checked, "simscape_audit"), "Model check should return a Simscape audit struct.");
assert(checked.simscape_audit.total_blocks > 0, "Simscape audit should count model blocks.");
assert(any(contains(checked.simscape_audit.warnings, "No Simscape-like library blocks")), ...
    "Pure Simulink test model should report that no Simscape physical path was detected.");

open_system(modelPath);
workspace = get_param(modelName, "ModelWorkspace");
preparedStopTime = evalin(workspace, "t_stop");
preparedStepTime = evalin(workspace, "t_step");
preparedClampGain = evalin(workspace, "A_clamp_gain");
assert(abs(preparedStopTime - 0.1) < eps, "t_stop should be prepared in the model workspace.");
assert(abs(preparedStepTime - 0.01) < eps, "t_step should be prepared in the model workspace.");
assert(abs(preparedClampGain - 10) < eps, "A_clamp_gain should be prepared in the model workspace.");
save_system(modelName, modelPath);
close_system(modelName, 0);

simulated = feval('citt.runSimulation', modelPath, struct("SummaryPath", summaryPath));
assert(simulated.success, "Simulation should pass after StopTime preparation.");
assert(isfield(simulated, "simscape_logging"), "Simulation summary should include Simscape logging status.");
end

function cleanupModel(modelName)
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
end
