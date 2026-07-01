function report = run_ui_examples_20_computer_use()
%RUN_UI_EXAMPLES_20_COMPUTER_USE Drive the real CiTT UI through 20 student paths.
%
% This is intentionally not part of run_all. It opens the MATLAB UI, restores
% the current teaching task, exports screenshots, and runs pixel/CV checks.

testRoot = fileparts(mfilename("fullpath"));
repoRoot = fileparts(fileparts(testRoot));
addpath(fullfile(repoRoot, "matlab"));

config = feval('citt.loadConfig');
examples = uiExamples();
timestamp = string(datetime("now", "Format", "yyyyMMdd_HHmmss"));
outDir = fullfile(config.WorkDir, "ui_qa_student_paths", "computer_use_20_" + timestamp);
if exist(outDir, "dir") ~= 7
    mkdir(outDir);
end

activeTaskId = activeTeachingTaskId(config);
if strlength(activeTaskId) == 0
    error("CiTT:NoTeachingTask", "No saved teaching task is available for UI computer-use QA.");
end

previousRestore = string(getenv("CITT_RESTORE_ACTIVE_TASK"));
setenv("CITT_RESTORE_ACTIVE_TASK", "1");
app = [];
cleanup = onCleanup(@() cleanupApp(app, previousRestore));

app = citt;
prepareFigure(app.Figure);
pauseForUi();
app.TestHooks.selectTask(activeTaskId);
app.TestHooks.navigate("teach");
pauseForUi();

results = repmat(emptyResult(), numel(examples), 1);
for i = 1:numel(examples)
    example = examples(i);
    app.TestHooks.selectTask(activeTaskId);
    app.TestHooks.navigate("teach");
    pauseForUi();
    advanceToStep(app, example.step);

    answerText = "I think the visible model evidence should connect the value, unit, and measured probe for " + example.expected + ".";
    app.TestHooks.setStudentAnswer(answerText);
    app.TestHooks.reveal();
    pauseForUi();
    app.TestHooks.zoomLearningModel(1.35);
    pauseForUi();
    revealPath = fullfile(outDir, sprintf("%02d_reveal.png", i));
    captureFigure(app.Figure, revealPath);
    revealCv = auditUiScreenshot(revealPath);

    app.TestHooks.chatSubmit(example.phrase);
    pauseForUi();
    app.TestHooks.zoomLearningModel(1.35);
    pauseForUi();
    measurePath = fullfile(outDir, sprintf("%02d_measure.png", i));
    captureFigure(app.Figure, measurePath);
    measureCv = auditUiScreenshot(measurePath);

    state = app.TestHooks.state();
    actual = lastProbeTarget(state);
    measurementMessage = lastMeasurementMessage(state);
    matched = actual == example.expected;
    previewOnly = contains(measurementMessage, "Preview-only measurement target matched");
    passed = matched && previewOnly && revealCv.pass && measureCv.pass;

    results(i) = struct( ...
        "index", i, ...
        "phrase", example.phrase, ...
        "expected", example.expected, ...
        "actual", actual, ...
        "step", example.step, ...
        "reveal_screenshot", string(revealPath), ...
        "measure_screenshot", string(measurePath), ...
        "reveal_cv", revealCv, ...
        "measure_cv", measureCv, ...
        "preview_only", previewOnly, ...
        "passed", passed);

    fprintf("[%02d/20] %s -> %s expected %s | cv=%d/%d | preview=%d | pass=%d\n", ...
        i, example.phrase, actual, example.expected, revealCv.pass, measureCv.pass, previewOnly, passed);
end

report = struct();
report.success = all([results.passed]);
report.generated_at = string(datetime("now"));
report.active_task_id = activeTaskId;
report.output_dir = string(outDir);
report.results = results;
report.summary = struct( ...
    "passed", sum([results.passed]), ...
    "failed", sum(~[results.passed]), ...
    "screenshots", numel(results) * 2);

jsonPath = fullfile(outDir, "report.json");
mdPath = fullfile(outDir, "report.md");
writeText(jsonPath, jsonencode(report, "PrettyPrint", true));
writeMarkdown(mdPath, report);
report.report_json = string(jsonPath);
report.report_markdown = string(mdPath);

if ~report.success
    error("CiTT:UiComputerUseFailed", "UI computer-use QA failed. See %s", mdPath);
end
end

function examples = uiExamples()
examples = [
    example("measure concentration signal", "PR_C_PK", 1)
    example("probe oral PK concentration", "PR_C_PK", 1)
    example("测量 PK 浓度", "PR_C_PK", 1)
    example("观察 PK concentration C(t)", "PR_C_PK", 1)
    example("scope lagged concentration after membrane", "PR_C_LAG", 2)
    example("measure membrane lag concentration", "PR_C_LAG", 2)
    example("测量 膜 后 滞后 浓度", "PR_C_LAG", 2)
    example("probe lagged concentration", "PR_C_LAG", 2)
    example("measure sensor current", "PR_I_SENSOR", 3)
    example("probe faradaic current output", "PR_I_SENSOR", 3)
    example("测量 传感器 电流", "PR_I_SENSOR", 3)
    example("measure TIA output voltage", "PR_V_TIA_OUT", 4)
    example("probe transimpedance amplifier output", "PR_V_TIA_OUT", 4)
    example("测量 跨阻 放大 输出 电压", "PR_V_TIA_OUT", 4)
    example("measure ADC code", "PR_ADC_CODE", 5)
    example("probe digital converter code", "PR_ADC_CODE", 5)
    example("测量 ADC 数字 代码", "PR_ADC_CODE", 5)
    example("measure settling error", "PR_SETTLING_ERROR", 6)
    example("probe final settling error voltage", "PR_SETTLING_ERROR", 6)
    example("测量 稳定 误差", "PR_SETTLING_ERROR", 6)
];
end

function value = example(phrase, expected, step)
value = struct("phrase", string(phrase), "expected", string(expected), "step", step);
end

function result = emptyResult()
cv = emptyCv();
result = struct( ...
    "index", 0, ...
    "phrase", "", ...
    "expected", "", ...
    "actual", "", ...
    "step", 0, ...
    "reveal_screenshot", "", ...
    "measure_screenshot", "", ...
    "reveal_cv", cv, ...
    "measure_cv", cv, ...
    "preview_only", false, ...
    "passed", false);
end

function value = emptyCv()
value = struct( ...
    "pass", false, ...
    "width", 0, ...
    "height", 0, ...
    "model_nonwhite", 0, ...
    "model_edges", 0, ...
    "model_edge_bbox_width", 0, ...
    "model_edge_bbox_height", 0, ...
    "learning_nonwhite", 0, ...
    "learning_edges", 0, ...
    "zoom_controls_nonwhite", 0, ...
    "zoom_controls_edges", 0, ...
    "green_control_ratio", 0);
end

function activeTaskId = activeTeachingTaskId(config)
activeTaskId = "";
historyPath = config.TaskHistoryPath;
if exist(historyPath, "file") ~= 2
    return
end
history = jsondecode(fileread(historyPath));
tasks = history.tasks;
preferred = "";
if isfield(history, "active_task_id")
    preferred = string(history.active_task_id);
end
for pass = 1:2
    for i = 1:numel(tasks)
        id = string(tasks(i).id);
        if pass == 1 && id ~= preferred
            continue
        end
        stage = lower(string(tasks(i).stage));
        if any(stage == ["teach", "probe", "evidence"]) && ...
                exist(string(tasks(i).model_path), "file") == 2 && ...
                exist(config.TeachingPlanPath, "file") == 2 && ...
                exist(config.ProbeMapPath, "file") == 2
            activeTaskId = id;
            return
        end
    end
end
end

function prepareFigure(fig)
try
    fig.WindowState = "normal";
catch
end
try
    fig.Position = [40 40 1440 900];
catch
end
drawnow;
end

function pauseForUi()
drawnow;
pause(0.8);
drawnow;
end

function advanceToStep(app, stepIndex)
for i = 2:stepIndex
    app.TestHooks.nextStep();
    pauseForUi();
end
end

function captureFigure(fig, path)
drawnow;
pause(0.2);
try
    exportapp(fig, path);
catch
    frame = getframe(fig);
    imwrite(frame.cdata, path);
end
end

function cv = auditUiScreenshot(path)
img = imread(path);
if size(img, 3) == 4
    img = img(:, :, 1:3);
end
img = double(img);
[height, width, ~] = size(img);

model = cropRatio(img, 100, 70, 1340, 376);
learning = cropRatio(img, 100, 389, 1340, 774);
zoomControls = cropRatio(img, 1130, 390, 1338, 438);
controls = cropRatio(img, 1100, 690, 1340, 870);

[modelNonwhite, modelEdges, bboxWidth, bboxHeight] = regionMetrics(model);
[learningNonwhite, learningEdges] = regionMetrics(learning);
[zoomControlsNonwhite, zoomControlsEdges] = regionMetrics(zoomControls);
greenControlRatio = greenRatio(controls);

cv = struct( ...
    "pass", width >= 1200 && height >= 760 && ...
        modelNonwhite > 0.015 && modelEdges > 0.003 && ...
        bboxWidth > 0.35 && bboxHeight > 0.15 && ...
        learningNonwhite > 0.025 && learningEdges > 0.004 && ...
        zoomControlsNonwhite > 0.03 && zoomControlsEdges > 0.01 && ...
        greenControlRatio > 0.004, ...
    "width", width, ...
    "height", height, ...
    "model_nonwhite", modelNonwhite, ...
    "model_edges", modelEdges, ...
    "model_edge_bbox_width", bboxWidth, ...
    "model_edge_bbox_height", bboxHeight, ...
    "learning_nonwhite", learningNonwhite, ...
    "learning_edges", learningEdges, ...
    "zoom_controls_nonwhite", zoomControlsNonwhite, ...
    "zoom_controls_edges", zoomControlsEdges, ...
    "green_control_ratio", greenControlRatio);
end

function region = cropRatio(img, x1, y1, x2, y2)
[height, width, ~] = size(img);
xStart = max(1, round(x1 / 1440 * width));
xEnd = min(width, round(x2 / 1440 * width));
yStart = max(1, round(y1 / 900 * height));
yEnd = min(height, round(y2 / 900 * height));
region = img(yStart:yEnd, xStart:xEnd, :);
end

function [nonwhite, edgeRatio, bboxWidth, bboxHeight] = regionMetrics(region)
nearWhite = region(:, :, 1) > 245 & region(:, :, 2) > 245 & region(:, :, 3) > 245;
nonwhite = 1 - mean(nearWhite(:));
lum = 0.299 * region(:, :, 1) + 0.587 * region(:, :, 2) + 0.114 * region(:, :, 3);
edges = false(size(lum));
edges(:, 2:end) = edges(:, 2:end) | abs(diff(lum, 1, 2)) > 18;
edges(2:end, :) = edges(2:end, :) | abs(diff(lum, 1, 1)) > 18;
edgeRatio = mean(edges(:));
[ys, xs] = find(edges);
if isempty(xs)
    bboxWidth = 0;
    bboxHeight = 0;
else
    bboxWidth = (max(xs) - min(xs) + 1) / size(region, 2);
    bboxHeight = (max(ys) - min(ys) + 1) / size(region, 1);
end
end

function ratio = greenRatio(region)
greenMask = region(:, :, 2) > 90 & region(:, :, 1) < 120 & region(:, :, 3) < 140;
ratio = mean(greenMask(:));
end

function target = lastProbeTarget(state)
target = "";
if isfield(state, "LastProbe") && isstruct(state.LastProbe) && isfield(state.LastProbe, "target_id")
    target = string(state.LastProbe.target_id);
end
end

function message = lastMeasurementMessage(state)
message = "";
if ~isfield(state, "LastProbe") || ~isstruct(state.LastProbe)
    return
end
probe = state.LastProbe;
if isfield(probe, "measurement") && isstruct(probe.measurement) && isfield(probe.measurement, "message")
    message = string(probe.measurement.message);
end
end

function writeMarkdown(path, report)
fid = fopen(path, "w");
assert(fid > 0, "Could not write UI QA markdown report.");
cleaner = onCleanup(@() fclose(fid));
fprintf(fid, "# 20 Example UI Computer-Use QA\n\n");
fprintf(fid, "- Success: %s\n", string(report.success));
fprintf(fid, "- Passed: %d\n", report.summary.passed);
fprintf(fid, "- Failed: %d\n", report.summary.failed);
fprintf(fid, "- Screenshots: %d\n\n", report.summary.screenshots);
fprintf(fid, "| # | Phrase | Expected | Actual | Step | CV | Preview | Screenshot |\n");
fprintf(fid, "|---|---|---|---|---:|---|---|---|\n");
for i = 1:numel(report.results)
    row = report.results(i);
    [~, shotName, ext] = fileparts(row.measure_screenshot);
    fprintf(fid, "| %d | `%s` | `%s` | `%s` | %d | %s/%s | %s | `%s` |\n", ...
        row.index, row.phrase, row.expected, row.actual, row.step, ...
        string(row.reveal_cv.pass), string(row.measure_cv.pass), string(row.preview_only), shotName + ext);
end
clear cleaner
end

function writeText(path, text)
fid = fopen(path, "w");
assert(fid > 0, "Could not write %s.", string(path));
cleaner = onCleanup(@() fclose(fid));
fprintf(fid, "%s", string(text));
clear cleaner
end

function cleanupApp(app, previousRestore)
try
    if ~isempty(app) && isfield(app, "Figure") && isvalid(app.Figure)
        delete(app.Figure);
    end
catch
end
setenv("CITT_RESTORE_ACTIVE_TASK", char(previousRestore));
end
