function results = run_named_tests(testFiles, suiteName)
%RUN_NAMED_TESTS Run function-style CiTT tests with diagnostics.

if nargin < 2 || isempty(suiteName)
    suiteName = "default";
end

results = repmat(struct( ...
    "suite", "", ...
    "name", "", ...
    "status", "", ...
    "passed", false, ...
    "duration_seconds", 0, ...
    "diagnostic", ""), 0, 1);

for i = 1:numel(testFiles)
    name = string(testFiles{i});
    fprintf("[%s] Running %s...\n", suiteName, name);
    started = tic;
    try
        feval(char(name));
        results(end + 1, 1) = resultRow(suiteName, name, "passed", true, toc(started), ""); %#ok<AGROW>
    catch testError
        if string(testError.identifier) == "CiTT:TestSkipped"
            fprintf("[%s] Skipped %s: %s\n", suiteName, name, testError.message);
            results(end + 1, 1) = resultRow(suiteName, name, "skipped", false, toc(started), string(testError.message)); %#ok<AGROW>
        else
            diagnostic = string(getReport(testError, "extended", "hyperlinks", "off"));
            fprintf(2, "[%s] Failed %s: %s\n", suiteName, name, testError.message);
            results(end + 1, 1) = resultRow(suiteName, name, "failed", false, toc(started), diagnostic); %#ok<AGROW>
        end
    end
end

printSummary(results, suiteName);
if any(string({results.status}) == "failed")
    error("CiTT:TestsFailed", "One or more %s tests failed.", suiteName);
end
end

function row = resultRow(suiteName, name, status, passed, duration, diagnostic)
row = struct( ...
    "suite", string(suiteName), ...
    "name", string(name), ...
    "status", string(status), ...
    "passed", logical(passed), ...
    "duration_seconds", double(duration), ...
    "diagnostic", string(diagnostic));
end

function printSummary(results, suiteName)
statuses = string({results.status});
fprintf("[%s] Summary: %d passed, %d skipped, %d failed.\n", suiteName, ...
    sum(statuses == "passed"), sum(statuses == "skipped"), sum(statuses == "failed"));
end
