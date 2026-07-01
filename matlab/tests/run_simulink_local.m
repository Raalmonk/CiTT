function results = run_simulink_local()
%RUN_SIMULINK_LOCAL Run tests that need local Simulink but no external agent.

testRoot = fileparts(mfilename("fullpath"));
addpath(testRoot);
addpath(fileparts(testRoot));
testFiles = {
    "test_stop_time_parameter_repair"
    "test_simulation_scenarios_local_model"
    "test_probe_preview_measurement_no_sim"
    "test_probe_preview_examples_20"
};

if exist("new_system", "file") ~= 2 && exist("new_system", "builtin") ~= 5
    results = skippedResults(testFiles, "simulink_local", "Simulink is unavailable in this MATLAB session.");
    printSkippedSummary(results, "simulink_local");
    return
end

results = run_named_tests(testFiles, "simulink_local");
end

function results = skippedResults(testFiles, suiteName, reason)
results = repmat(struct( ...
    "suite", "", ...
    "name", "", ...
    "status", "", ...
    "passed", false, ...
    "duration_seconds", 0, ...
    "diagnostic", ""), 0, 1);
for i = 1:numel(testFiles)
    results(end + 1, 1) = struct( ...
        "suite", string(suiteName), ...
        "name", string(testFiles{i}), ...
        "status", "skipped", ...
        "passed", false, ...
        "duration_seconds", 0, ...
        "diagnostic", string(reason)); %#ok<AGROW>
end
end

function printSkippedSummary(results, suiteName)
fprintf("[%s] Summary: 0 passed, %d skipped, 0 failed.\n", suiteName, numel(results));
end
