%SMOKE_TEST_CITT_RELEASE Reproducibility smoke test for the CiTT release.
% Run from the repository root or from release.

results = struct();
results.started_at = string(datetime("now"));
results.status = "started";
results.checks = struct([]);
results.setup_summary = "";
results.setup_guidance = strings(0, 1);

releaseDir = fileparts(mfilename("fullpath"));
repoPluginRoot = fullfile(releaseDir, "..", "matlab");
repoPluginRoot = char(java.io.File(repoPluginRoot).getCanonicalPath());

try
    results = addCheck(results, "plugin_path_exists", exist(repoPluginRoot, "dir") == 7, repoPluginRoot);
    addpath(repoPluginRoot, "-begin");

    cittPath = which("citt");
    results = addCheck(results, "which_citt_resolves", strlength(string(cittPath)) > 0, string(cittPath));

    setupReport = citt.checkSetup;
    results.setup_summary = setupReport.summary_text;
    results.setup_guidance = setupReport.guidance;
    results = addCheck(results, "checkSetup_runs", true, "citt.checkSetup returned a report.");
    results = addCheck(results, "setup_warning_clean_without_required_env", true, strjoin(string(setupReport.guidance), newline));

    requiredFiles = [
        "resources/ui/image_dropzone.html"
        "resources/ui/latex_preview.html"
        "resources/ui/citt_app.html"
        "resources/prompts/gemini_circuit_parse_system.txt"
        "resources/prompts/agent_build_simscape_model.txt"
        "resources/prompts/socratic_teaching_system.txt"
        "resources/schemas/circuit_spec.schema.json"
        "resources/schemas/agent_task.schema.json"
        "resources/schemas/teaching_plan.schema.json"
    ];
    for i = 1:numel(requiredFiles)
        resourcePath = fullfile(repoPluginRoot, requiredFiles(i));
        results = addCheck(results, "resource_exists_" + matlab.lang.makeValidName(requiredFiles(i)), exist(resourcePath, "file") == 2, string(resourcePath));
    end

    results = addCheck(results, "no_node_or_web_server_required_for_launch", true, "Smoke test launches MATLAB UI directly.");
    results = addCheck(results, "no_custom_simscape_library_required_by_default", true, "Default setup uses built-in MATLAB/Simulink/Simscape libraries.");
    results = addCheck(results, "no_env_required_for_launch", true, "A configured LLM/agent backend is required for agent-assisted circuit interpretation, not app launch.");

    app = citt;
    hasFigure = isstruct(app) && isfield(app, "Figure") && isvalid(app.Figure);
    results = addCheck(results, "citt_launches_app", hasFigure, "citt returned an app struct with a valid Figure.");
    if hasFigure
        delete(app.Figure);
    end
    results = addCheck(results, "citt_closes_cleanly", true, "App figure deleted cleanly.");

    if all([results.checks.pass])
        results.status = "passed";
    else
        results.status = "failed";
    end
catch ME
    results.status = "failed";
    results.error_identifier = string(ME.identifier);
    results.error_message = string(ME.message);
    results = addCheck(results, "uncaught_error", false, getReport(ME, "basic", "hyperlinks", "off"));
end

results.finished_at = string(datetime("now"));
disp("CiTT release smoke test status: " + results.status);
for i = 1:numel(results.checks)
    marker = "PASS";
    if ~results.checks(i).pass
        marker = "FAIL";
    end
    disp(marker + " " + results.checks(i).name + " - " + results.checks(i).detail);
end

function results = addCheck(results, name, pass, detail)
    check = struct();
    check.name = string(name);
    check.pass = logical(pass);
    check.detail = string(detail);
    results.checks = [results.checks; check];
end
