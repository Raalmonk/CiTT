function results = run_all()
%RUN_ALL Run CiTT MATLAB plugin smoke tests.

testFiles = {
    "test_real_config"
    "test_agent_task_generation"
    "test_simscape_model_generation"
    "test_teaching_plan_contract"
    "test_lab_delta"
};

results = struct([]);
for i = 1:numel(testFiles)
    name = testFiles{i};
    fprintf("Running %s...\n", name);
    feval(name);
    results = [results; struct("name", string(name), "passed", true)]; %#ok<AGROW>
end

fprintf("CiTT MATLAB tests passed: %d\n", numel(results));
end
