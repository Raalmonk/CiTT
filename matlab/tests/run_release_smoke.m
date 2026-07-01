function results = run_release_smoke()
%RUN_RELEASE_SMOKE Run the MATLAB app launch/release smoke script.

repoRoot = fileparts(fileparts(fileparts(mfilename("fullpath"))));
scriptPath = fullfile(repoRoot, "release", "smoke_test_citt_release.m");
suiteName = "release_smoke";
started = tic;

try
    run(scriptPath);
    status = "passed";
    passed = true;
    diagnostic = "";
catch smokeError
    status = "failed";
    passed = false;
    diagnostic = string(getReport(smokeError, "extended", "hyperlinks", "off"));
end

results = struct( ...
    "suite", suiteName, ...
    "name", "smoke_test_citt_release", ...
    "status", status, ...
    "passed", passed, ...
    "duration_seconds", toc(started), ...
    "diagnostic", diagnostic);

fprintf("[%s] Summary: %d passed, 0 skipped, %d failed.\n", suiteName, passed, ~passed);
if ~passed
    error("CiTT:TestsFailed", "Release smoke test failed.");
end
end
