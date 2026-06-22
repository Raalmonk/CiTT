%VERIFY_INSTALLED_EXAMPLES Install CiTT .mltbx and reproduce release examples.
% This is a post-package validation script. It intentionally uses the
% installed Add-On path for CiTT, while reading example inputs from the repo.

releaseDir = fileparts(mfilename("fullpath"));
repoRoot = canonicalPath(fullfile(releaseDir, ".."));
toolboxFile = fullfile(releaseDir, "CiTT_BMES_2026.mltbx");
evidenceRoot = fullfile(repoRoot, "submission_assets", "live_gui_evidence");
outputRoot = fullfile(releaseDir, "example_repro");

if exist(outputRoot, "dir") == 7
    rmdir(outputRoot, "s");
end
mkdir(outputRoot);

uninstallExistingCiTT();
removeRepoPaths(repoRoot);
rehash toolboxcache;
rehash;

summary = struct();
summary.started_at = string(datetime("now"));
summary.toolbox_file = string(toolboxFile);
summary.output_root = string(outputRoot);
summary.examples = struct([]);

installedInfo = [];
try
    installedInfo = matlab.addons.toolbox.installToolbox(toolboxFile);
    rehash toolboxcache;
    rehash;

    cittPath = string(which("citt"));
    assert(strlength(cittPath) > 0, "Installed citt was not found on the MATLAB path.");
    assert(contains(cittPath, "MATLAB Add-Ons"), "citt resolved outside MATLAB Add-Ons: " + cittPath);

    setupReport = citt.checkSetup;
    summary.installed_citt_path = cittPath;
    summary.installed_work_dir = setupReport.work_dir;
    summary.setup_guidance = setupReport.guidance;

    app = citt;
    assert(isstruct(app) && isfield(app, "Figure") && isvalid(app.Figure), ...
        "citt did not return an app struct with a valid Figure.");
    drawnow;
    pause(0.5);
    guiScreenshotPath = fullfile(outputRoot, "installed_gui_smoke.png");
    try
        exportapp(app.Figure, guiScreenshotPath);
        summary.gui_screenshot = string(guiScreenshotPath);
    catch screenshotError
        summary.gui_screenshot = "";
        summary.gui_screenshot_warning = string(screenshotError.message);
    end
    delete(app.Figure);
    summary.gui_launch = "passed";

    summary.examples = [summary.examples; verifyRcExample(evidenceRoot, outputRoot)];
    summary.examples = [summary.examples; verifyTevcExample(evidenceRoot, outputRoot)];
    summary.examples = [summary.examples; verifyMixedSignalExample(evidenceRoot, outputRoot)];

    summary.status = "passed";
catch ME
    summary.status = "failed";
    summary.error_identifier = string(ME.identifier);
    summary.error_message = string(ME.message);
    writeSummary(outputRoot, summary);
    cleanupInstall(installedInfo);
    rethrow(ME);
end

summary.finished_at = string(datetime("now"));
writeSummary(outputRoot, summary);
cleanupInstall(installedInfo);
fprintf("Installed CiTT examples verification: %s\n", summary.status);
fprintf("Summary: %s\n", fullfile(outputRoot, "verification_summary.md"));

function example = verifyRcExample(evidenceRoot, outputRoot)
exampleName = "benchmark_01_textbook_rc";
exampleDir = fullfile(outputRoot, exampleName);
mkdir(exampleDir);

problemPath = fullfile(evidenceRoot, exampleName, "problem_statement.md");
assert(isfile(problemPath), "Missing RC problem statement.");

spec = rcSpec();
specPath = fullfile(exampleDir, "citt_spec_reproduced.json");
writeJson(specPath, spec);

modelPath = fullfile(exampleDir, "rc_reproduced_model.slx");
buildResult = citt.buildLocalSimscapeFallback(specPath, struct( ...
    "ScriptPath", fullfile(exampleDir, "rc_reproduced_build.m"), ...
    "ModelPath", modelPath, ...
    "FocusMapPath", fullfile(exampleDir, "citt_focus_map.json"), ...
    "ProbeMapPath", fullfile(exampleDir, "citt_probe_map.json"), ...
    "ReportPath", fullfile(exampleDir, "citt_agent_report.md"), ...
    "OpenModel", false));
assert(buildResult.success, "RC local model reproduction failed.");
assert(isfile(modelPath), "RC reproduced model file missing.");

modelCheck = citt.runModelCheck(modelPath, struct("ReportPath", fullfile(exampleDir, "citt_model_check_report.md")));
assert(modelCheck.success, "RC model check failed.");

bode = citt.runBodeAnalysis(struct("SpecPath", specPath, "ModelPath", modelPath), struct( ...
    "OutputPath", fullfile(exampleDir, "citt_bode_report.json"), ...
    "MarkdownPath", fullfile(exampleDir, "citt_bode_report.md"), ...
    "PlotPath", fullfile(exampleDir, "citt_bode_plot.png"), ...
    "FrequencyHz", [5 39.9887 60 250]));
assert(bode.success, "RC Bode reproduction failed.");
assert(isfile(bode.plot_path), "RC Bode plot missing.");

teaching = citt.buildTeachingPlan(specPath, buildResult.focus_map_path, modelCheck, [], ...
    struct("OutputPath", fullfile(exampleDir, "citt_teaching_plan.json")));
assert(teaching.success && teaching.step_count > 0, "RC teaching plan reproduction failed.");

context = baseEvidenceContext(problemPath, specPath, modelPath, buildResult.focus_map_path, buildResult.probe_map_path);
context.LastModelCheck = modelCheck;
context.LastProbe = struct("success", true, "target_id", "probe_vout");
context.LastRequirements = struct("rows", []);
pack = citt.exportEvidencePack(context, struct("OutputPath", fullfile(exampleDir, "citt_evidence_pack.md")));
assert(pack.success && isfile(pack.pack_path), "RC evidence pack reproduction failed.");

closeModel(modelPath);
example = exampleResult(exampleName, exampleDir, "passed");
example.model_path = string(modelPath);
example.bode_plot = string(bode.plot_path);
example.teaching_steps = teaching.step_count;
end

function example = verifyTevcExample(evidenceRoot, outputRoot)
exampleName = "benchmark_02_tevc_equilibrium";
sourceDir = fullfile(evidenceRoot, exampleName);
artifactDir = fullfile(sourceDir, "artifacts");
exampleDir = fullfile(outputRoot, exampleName);
mkdir(exampleDir);

problemPath = fullfile(sourceDir, "problem_statement.md");
modelPath = fullfile(artifactDir, "citt_generated_model_tevc.slx");
focusPath = fullfile(artifactDir, "citt_focus_map.json");
probePath = fullfile(artifactDir, "citt_probe_map.json");
assert(isfile(problemPath), "Missing TEVC problem statement.");
assert(isfile(modelPath), "Missing TEVC model artifact.");
assert(isfile(focusPath), "Missing TEVC focus map.");
assert(isfile(probePath), "Missing TEVC probe map.");

specPath = fullfile(exampleDir, "citt_spec_reproduced.json");
writeJson(specPath, tevcSpec());

openResult = citt.openOrCreateModel(modelPath);
assert(openResult.success, "TEVC model did not open.");

modelCheck = citt.runModelCheck(modelPath, struct("ReportPath", fullfile(exampleDir, "citt_model_check_report.md")));
assert(modelCheck.success, "TEVC model check failed.");

teaching = citt.buildTeachingPlan(specPath, focusPath, modelCheck, [], ...
    struct("OutputPath", fullfile(exampleDir, "citt_teaching_plan.json")));
assert(teaching.success && teaching.step_count >= 3, "TEVC teaching plan reproduction failed.");

context = baseEvidenceContext(problemPath, specPath, modelPath, focusPath, probePath);
context.LastModelCheck = modelCheck;
context.LastProbe = struct("success", true, "target_id", "probe_vm");
context.LastRequirements = struct("rows", []);
pack = citt.exportEvidencePack(context, struct("OutputPath", fullfile(exampleDir, "citt_evidence_pack.md")));
assert(pack.success && isfile(pack.pack_path), "TEVC evidence pack reproduction failed.");

closeModel(modelPath);
example = exampleResult(exampleName, exampleDir, "passed");
example.model_path = string(modelPath);
example.teaching_steps = teaching.step_count;
end

function example = verifyMixedSignalExample(evidenceRoot, outputRoot)
exampleName = "benchmark_03_mixed_signal";
sourceDir = fullfile(evidenceRoot, exampleName);
artifactDir = fullfile(sourceDir, "artifacts");
exampleDir = fullfile(outputRoot, exampleName);
mkdir(exampleDir);

problemPath = fullfile(sourceDir, "problem_statement.md");
specPath = fullfile(artifactDir, "citt_spec_parameterized.json");
modelPath = fullfile(artifactDir, "citt_generated_model.slx");
focusPath = fullfile(artifactDir, "citt_focus_map.json");
probePath = fullfile(artifactDir, "citt_probe_map.json");
metricsPath = fullfile(artifactDir, "benchmark_03_simulation_metrics.json");
paramsPath = fullfile(artifactDir, "benchmark03_educational_params.m");
assert(isfile(problemPath), "Missing mixed-signal problem statement.");
assert(isfile(specPath), "Missing mixed-signal parameterized spec.");
assert(isfile(modelPath), "Missing mixed-signal model artifact.");
assert(isfile(focusPath), "Missing mixed-signal focus map.");
assert(isfile(probePath), "Missing mixed-signal probe map.");
assert(isfile(metricsPath), "Missing mixed-signal metrics JSON.");

if isfile(paramsPath)
    run(paramsPath);
end

openResult = citt.openOrCreateModel(modelPath);
assert(openResult.success, "Mixed-signal model did not open.");

modelCheck = citt.runModelCheck(modelPath, struct("ReportPath", fullfile(exampleDir, "citt_model_check_report.md")));
assert(modelCheck.success, "Mixed-signal model check failed.");

teaching = citt.buildTeachingPlan(specPath, focusPath, modelCheck, metricsPath, ...
    struct("OutputPath", fullfile(exampleDir, "citt_teaching_plan.json")));
assert(teaching.success && teaching.step_count >= 5, "Mixed-signal teaching plan reproduction failed.");

context = baseEvidenceContext(problemPath, specPath, modelPath, focusPath, probePath);
context.LastModelCheck = modelCheck;
context.LastSimulation = jsondecode(fileread(metricsPath));
context.LastProbe = struct("success", true, "target_id", "probe_vm");
context.LastRequirements = struct("rows", []);
pack = citt.exportEvidencePack(context, struct("OutputPath", fullfile(exampleDir, "citt_evidence_pack.md")));
assert(pack.success && isfile(pack.pack_path), "Mixed-signal evidence pack reproduction failed.");

closeModel(modelPath);
example = exampleResult(exampleName, exampleDir, "passed");
example.model_path = string(modelPath);
example.teaching_steps = teaching.step_count;
example.metrics_path = string(metricsPath);
end

function context = baseEvidenceContext(problemPath, specPath, modelPath, focusPath, probePath)
context = struct();
context.ImagePath = "";
context.PromptText = string(fileread(problemPath));
context.Spec = [];
context.SpecPath = string(specPath);
context.AgentTaskPath = "";
context.AgentRun = struct("mode", "installed_example_repro", "success", true);
context.ModelPath = string(modelPath);
context.FocusMapPath = string(focusPath);
context.ProbeMapPath = string(probePath);
context.LastModelCheck = [];
context.LastSimulation = [];
context.LastProbe = [];
context.LabCsvPath = "";
context.LastLabDelta = [];
context.LastRequirements = struct("rows", []);
context.LastSweep = [];
context.LastFaults = [];
context.LastExplainability = [];
context.LastAssessment = [];
context.LastEconomics = [];
context.LastScopeGuardrail = [];
end

function spec = rcSpec()
spec = struct();
spec.circuit_type = "rc_low_pass_anti_aliasing";
spec.components = [
    component("V1", "voltage_source", 1, "V", ["positive", "negative"])
    component("R1", "resistor", 39.8e3, "Ohm", ["left", "right"])
    component("C1", "capacitor", 100e-9, "F", ["top", "bottom"])
];
spec.nodes = ["n_in", "n_out", "0"];
spec.connections = [
    connection("V1.positive", "R1.left", "n_in")
    connection("R1.right", "C1.top", "n_out")
    connection("V1.negative", "C1.bottom", "0")
];
spec.ground_node = "0";
spec.sources = ["V1"];
spec.requested_outputs = ["V(n_out)"];
spec.likely_analysis = "ac_frequency_response";
spec.assumptions = ["500 Hz ADC", "first-order educational RC stage"];
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
spec.suggested_simscape_blocks = ["Resistor", "Capacitor", "Electrical Reference", "Solver Configuration", "Voltage Sensor"];
spec.focus_points = struct("focus_id", "rc_output", "label", "RC output node", ...
    "explanation", "The low-pass output is the node between R1 and C1.", ...
    "model_paths", strings(0, 1), "block_paths", strings(0, 1), ...
    "related_components", ["R1", "C1"], "related_nodes", "n_out", ...
    "teaching_question", "Why is n_out the correct place to probe the filtered signal?");
end

function spec = tevcSpec()
spec = struct();
spec.circuit_type = "two_electrode_voltage_clamp_equilibrium";
spec.components = [
    component("V_c", "voltage_source", "V_c", "V", ["positive", "negative"])
    component("BUF1", "ideal_buffer", "ideal", "", ["input", "output"])
    component("AMP1", "finite_gain_amplifier", 100, "V/V", ["plus", "minus", "output"])
    component("R_o", "resistor", 10, "Ohm", ["left", "right"])
    component("R_m", "resistor", 10, "Ohm", ["top", "bottom"])
    component("R_e", "resistor", "R_e", "Ohm", ["left", "right"])
];
spec.nodes = ["n_vc", "n_buffer_out", "n_feedback_sense", "n_amp_out", "n_vm", "n_ref"];
spec.requested_outputs = ["Vm", "amplifier_output", "clamp_current"];
spec.likely_analysis = "dc_equilibrium_feedback";
spec.assumptions = ["Membrane capacitance and ion-channel dynamics ignored at equilibrium."];
spec.ambiguities = ["V_c and R_e are symbolic in the source benchmark."];
spec.unsupported_or_unclear_regions = strings(0, 1);
end

function c = component(id, type, value, unit, terminals)
c = struct("id", id, "type", type, "label", id, "value", value, ...
    "unit", unit, "terminals", terminals, "confidence", 1.0);
end

function c = connection(from, to, label)
c = struct("from", from, "to", to, "label", label, "confidence", 1.0);
end

function example = exampleResult(name, outputDir, status)
example = struct();
example.name = string(name);
example.status = string(status);
example.output_dir = string(outputDir);
example.model_path = "";
example.bode_plot = "";
example.teaching_steps = 0;
example.metrics_path = "";
end

function writeSummary(outputRoot, summary)
writeJson(fullfile(outputRoot, "verification_summary.json"), summary);

lines = [
    "# Installed CiTT Examples Verification"
    ""
    "Status: `" + summary.status + "`"
    "Started: `" + fieldText(summary, "started_at") + "`"
    "Finished: `" + fieldText(summary, "finished_at") + "`"
    "Installed citt: `" + fieldText(summary, "installed_citt_path") + "`"
    "Installed work dir: `" + fieldText(summary, "installed_work_dir") + "`"
    ""
    "## Examples"
    ""
];
if isfield(summary, "examples")
    for i = 1:numel(summary.examples)
        item = summary.examples(i);
        lines(end + 1) = "- `" + item.name + "`: `" + item.status + "` -> `" + item.output_dir + "`"; %#ok<AGROW>
    end
end
if isfield(summary, "error_message")
    lines = [lines; ""; "## Error"; ""; summary.error_message];
end
writeText(fullfile(outputRoot, "verification_summary.md"), strjoin(lines, newline));
end

function text = fieldText(value, fieldName)
text = "";
if isstruct(value) && isfield(value, fieldName)
    text = string(value.(fieldName));
end
end

function writeJson(path, value)
writeText(path, jsonencode(value, PrettyPrint=true));
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
assert(fid >= 0, "Could not write " + string(path));
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end

function path = canonicalPath(pathValue)
path = char(java.io.File(pathValue).getCanonicalPath());
end

function removeRepoPaths(repoRoot)
pathsToRemove = [
    string(fullfile(repoRoot, "matlab"))
    string(repoRoot)
    string(canonicalPath(fullfile(tempdir, "citt_bmes_release_stage", "CiTT_BMES_2026_Source", "matlab")))
];
pathParts = string(split(path, pathsep));
for i = 1:numel(pathsToRemove)
    if any(pathParts == pathsToRemove(i))
        rmpath(char(pathsToRemove(i)));
    end
end
end

function uninstallExistingCiTT()
installed = matlab.addons.toolbox.installedToolboxes;
for i = 1:numel(installed)
    name = "";
    guid = "";
    if isfield(installed(i), "Name")
        name = string(installed(i).Name);
    end
    if isfield(installed(i), "Guid")
        guid = string(installed(i).Guid);
    end
    if name == "CiTT BMES 2026" || guid == "3f5672d7-3c0d-4e5d-87e9-a4927e278f9b"
        matlab.addons.toolbox.uninstallToolbox(installed(i));
    end
end
end

function cleanupInstall(installedInfo)
try
    bdclose("all");
catch
end
try
    if isstruct(installedInfo) && ~isempty(installedInfo)
        matlab.addons.toolbox.uninstallToolbox(installedInfo);
    end
catch cleanupError
    warning("CiTT:CleanupFailed", "%s", cleanupError.message);
end
rehash toolboxcache;
rehash;
end

function closeModel(modelPath)
try
    [~, modelName, ~] = fileparts(modelPath);
    if bdIsLoaded(modelName)
        close_system(modelName, 0);
    end
catch
end
end
