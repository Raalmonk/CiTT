function results = run_all()
%RUN_ALL Run the default CiTT MATLAB test layers.

addpath(fileparts(mfilename("fullpath")));
unitResults = run_unit();
localResults = run_simulink_local();
results = [unitResults(:); localResults(:)];

statuses = string({results.status});
fprintf("CiTT MATLAB tests: %d passed, %d skipped, %d failed.\n", ...
    sum(statuses == "passed"), sum(statuses == "skipped"), sum(statuses == "failed"));
if any(statuses == "failed")
    error("CiTT:TestsFailed", "One or more default CiTT tests failed.");
end
end
