function app = openHtmlApp()
%OPENHTMLAPP Launch the local HTML/CSS CiTT shell backed by MATLAB callbacks.

state = feval('citt.appState');
state.LastSetupReport = feval('citt.checkSetup');
state = clearTaskState(state);
activeTaskId = "";
taskHistory = loadTaskHistory();

app = struct();
app.Figure = uifigure( ...
    "Name", "CiTT", ...
    "Position", [50 40 1320 860]);
app.Figure.Color = [0.055 0.06 0.075];
app.Figure.CloseRequestFcn = @(src, ~) onCloseApp(src);
try
    app.Figure.WindowState = "maximized";
catch
end

grid = uigridlayout(app.Figure, [1 1]);
grid.Padding = [0 0 0 0];
grid.RowSpacing = 0;
grid.ColumnSpacing = 0;

handles = struct();
handles.web = uihtml(grid, ...
    "HTMLSource", fullfile(state.Config.MatlabRoot, "resources", "ui", "citt_app.html"), ...
    "DataChangedFcn", @(src, ~) onWebMessage(src));
handles.web.Layout.Row = 1;
handles.web.Layout.Column = 1;

agentPollTimer = [];
activePage = "read";
busy = false;
busyText = "";
pipelineMessage = "Ready for circuit input.";
pipelineProgress = 0;
lastNewTaskPosix = 0;

lastInputStatus = "";
lastAgentOutput = "";
lastAgentStatus = "Build model from the parsed circuit.";
lastModelOutput = "";
lastModelStatus = "Open, check, or simulate the generated model.";
lastModelPreviewStatus = "No model preview yet.";
lastTeachOutput = "";
lastTeachStatus = "Waiting for teaching plan.";
lastProbeOutput = "";
lastProbeStatus = "Select a focus or probe target.";
lastDeltaOutput = "";
lastDeltaStatus = "Compare lab data after probes are available.";
lastVerificationOutput = "";
lastVerificationStatus = "Evidence actions are ready.";
lastAssessmentOutput = "";
lastAssessmentStatus = "Learning and planning reports are ready.";
lastEvidenceOutput = "";
lastEvidenceStatus = "Export an evidence pack when the model has enough proof.";
lastSettingsStatus = "Settings are loaded from the local CiTT work folder.";

ensureActiveTask();
restoreActiveTaskIfAvailable();

app.Handles = handles;
app.State = state;

    function onWebMessage(src)
        message = src.Data;
        if isempty(message) || ~isstruct(message) || ~isfield(message, "kind")
            return
        end
        if string(message.kind) ~= "action"
            return
        end

        action = fieldText(message, "action");
        payload = struct();
        if isfield(message, "payload") && isstruct(message.payload)
            payload = message.payload;
        end

        trackedAction = shouldRecordAction(action);
        if trackedAction
            appendTaskEvent(action, "started", taskEventSummary(action));
        end

        try
            switch action
                case "ready"
                    sendState();
                case "new_task"
                    onNewTask();
                case "select_task"
                    onSelectTask(payloadText(payload, "taskId", ""));
                case "save_settings"
                    onSaveSettings(payload);
                case "navigate"
                    activePage = payloadText(payload, "page", activePage);
                    sendState();
                case "sync"
                    syncPayload(payload);
                    sendState();
                case "select_image"
                    onSelectImage();
                case "drop_image"
                    onImageDropped(payload);
                case "read"
                    syncPayload(payload);
                    onParseWithGemini();
                case "run_pipeline"
                    syncPayload(payload);
                    onRunPipeline();
                case "open_spec"
                    onOpenSpec();
                case "prepare_build"
                    onGenerateAgentTask();
                case "build_model"
                    onRunAgent();
                case "open_task"
                    onOpenTask();
                case "refresh_setup"
                    onRefreshSetup();
                case "select_model"
                    onSelectModel();
                case "open_model"
                    syncPayload(payload);
                    onOpenModel();
                case "refresh_model_snapshot"
                    syncPayload(payload);
                    onRefreshModelSnapshot();
                case "check_model"
                    syncPayload(payload);
                    onCheckModel();
                case "run_simulation"
                    syncPayload(payload);
                    onRunSimulation();
                case "bode_plot"
                    syncPayload(payload);
                    onRunBodeAnalysis();
                case "run_command"
                    syncPayload(payload);
                    onRunCommand(payloadText(payload, "command", ""));
                case "start_teaching"
                    onStartTeaching();
                case "select_teaching_image"
                    onSelectTeachingImage();
                case "next_hint"
                    syncPayload(payload);
                    onNextHint();
                case "reveal"
                    syncPayload(payload);
                    onReveal();
                case "highlight_focus"
                    syncPayload(payload);
                    onHighlightCurrent(payloadText(payload, "focus", ""));
                case "zoom_focus"
                    syncPayload(payload);
                    onZoomCurrent(payloadText(payload, "focus", ""));
                case "clear_highlights"
                    onRunNaturalClearHighlights();
                case "add_probe"
                    syncPayload(payload);
                    onAddProbe(payloadText(payload, "probe", ""));
                case "select_csv"
                    onSelectCsv();
                case "compare_delta"
                    syncPayload(payload);
                    onCompareLabDelta();
                case "analyze_lab_error"
                    syncPayload(payload);
                    onAnalyzeLabError();
                case "requirements"
                    onRunRequirements();
                case "sweep"
                    onRunSweep();
                case "faults"
                    onRunFaults();
                case "build_explainability"
                    onBuildExplainability();
                case "highlight_explainability"
                    syncPayload(payload);
                    onHighlightExplainability(payloadText(payload, "explainAction", ""));
                case "assessment"
                    syncPayload(payload);
                    onRunAssessment(payload);
                case "economics"
                    syncPayload(payload);
                    onBuildEconomics(payload);
                case "scope"
                    onBuildScopeGuardrail();
                case "export_evidence"
                    syncPayload(payload);
                    onExportEvidencePack();
                case "open_evidence"
                    syncPayload(payload);
                    onOpenEvidencePack();
                otherwise
                    sendToast("Unknown action: " + action, "warning");
            end
            if trackedAction
                appendTaskEvent(action, "completed", pipelineMessage);
                saveActiveTask(action);
                saveTaskHistory();
                sendState();
            end
        catch err
            busy = false;
            busyText = "";
            if trackedAction
                appendTaskEvent(action, "failed", string(err.message));
                saveActiveTask(action);
                saveTaskHistory();
            end
            sendToast(string(err.message), "error");
            sendState();
        end
    end

    function syncPayload(payload)
        if isfield(payload, "prompt")
            state.PromptText = string(payload.prompt);
        end
        if isfield(payload, "imagePath")
            state.ImagePath = string(payload.imagePath);
        end
        if isfield(payload, "modelPath")
            state.ModelPath = string(payload.modelPath);
        end
        if isfield(payload, "studentAnswer")
            state.StudentAnswer = string(payload.studentAnswer);
        end
        if isfield(payload, "teachingImagePath")
            state.TeachingImagePath = string(payload.teachingImagePath);
        end
        if isfield(payload, "labCsvPath")
            state.LabCsvPath = string(payload.labCsvPath);
        end
        if isfield(payload, "opAmpPart")
            state.OpAmpPart = string(payload.opAmpPart);
        end
        if isfield(payload, "evidencePath")
            state.EvidencePackPath = string(payload.evidencePath);
        end
    end

    function onNewTask()
        currentPosix = posixtime(datetime("now"));
        if currentPosix - lastNewTaskPosix < 1.2
            sendState();
            return
        end
        lastNewTaskPosix = currentPosix;
        saveActiveTask("new_task_before_reset");
        saveTaskHistory();
        state = feval('citt.appState');
        state.LastSetupReport = feval('citt.checkSetup');
        state = clearTaskState(state);
        resetUiOutputs();
        activePage = "read";
        busy = false;
        busyText = "";
        setPipeline("Ready for circuit input.", 0);
        activeTaskId = makeTaskId();
        taskHistory = [makeTaskRecord(activeTaskId, "New circuit task"); taskHistory(:)];
        sendState();
    end

    function onSelectTask(taskId)
        taskId = string(taskId);
        index = findTaskIndex(taskId);
        if index == 0
            sendToast("Task not found.", "warning");
            sendState();
            return
        end

        saveActiveTask("select_task_before_switch");
        activeTaskId = taskId;
        restoreTaskSnapshot(taskHistory(index));
        setPipeline("Loaded task history: " + taskHistory(index).title, taskHistory(index).progress);
        sendState();
    end

    function onSaveSettings(payload)
        previousKey = string(getenv("GEMINI_API_KEY"));
        apiKey = payloadText(payload, "geminiApiKey", "");
        if strlength(strtrim(apiKey)) == 0 || contains(apiKey, "*")
            apiKey = previousKey;
        end

        modelName = payloadText(payload, "geminiModel", string(getenv("GEMINI_MODEL")));
        parserBackend = lower(strtrim(payloadText(payload, "parserBackend", state.Config.ParserBackend)));
        agentBackend = lower(strtrim(payloadText(payload, "agentBackend", state.Config.AgentBackend)));
        agentCommand = payloadText(payload, "agentCommand", string(getenv("CITT_AGENT_COMMAND")));
        maxAttempts = payloadNumber(payload, "agentMaxAttempts", 4);
        retryDelay = payloadNumber(payload, "agentRetryDelaySeconds", 20);

        if strlength(strtrim(apiKey)) > 0
            setenv("GEMINI_API_KEY", char(apiKey));
        end
        if strlength(strtrim(modelName)) > 0
            setenv("GEMINI_MODEL", char(modelName));
        end
        if ~ismember(parserBackend, ["codex", "gemini", "local"])
            parserBackend = "codex";
        end
        if ~ismember(agentBackend, ["codex", "gemini"])
            agentBackend = "codex";
        end
        setenv("CITT_PARSER_BACKEND", char(parserBackend));
        setenv("CITT_AGENT_BACKEND", char(agentBackend));
        setenv("CITT_AGENT_COMMAND", char(agentCommand));
        setenv("CITT_AGENT_MAX_ATTEMPTS", char(string(max(1, round(maxAttempts)))));
        setenv("CITT_AGENT_RETRY_DELAY_SECONDS", char(string(max(0, retryDelay))));

        settings = struct( ...
            "gemini_api_key", apiKey, ...
            "gemini_model", modelName, ...
            "parser_backend", parserBackend, ...
            "agent_backend", agentBackend, ...
            "agent_command", agentCommand, ...
            "agent_max_attempts", max(1, round(maxAttempts)), ...
            "agent_retry_delay_seconds", max(0, retryDelay), ...
            "updated_at", string(datetime("now")));
        writeJson(state.Config.SettingsPath, settings);

        state.Config = feval('citt.loadConfig');
        state.LastSetupReport = feval('citt.checkSetup');
        lastSettingsStatus = "Settings saved locally: " + state.Config.SettingsPath;
        sendToast("Settings saved.", "info");
        sendState();
    end

    function onSelectImage()
        [file, folder] = uigetfile({"*.png;*.jpg;*.jpeg;*.gif;*.webp", "Circuit images"; "*.*", "All files"});
        if isequal(file, 0)
            sendState();
            return
        end
        state.ImagePath = string(fullfile(folder, file));
        lastInputStatus = "Image selected: " + state.ImagePath;
        setPipeline("Image ready. Next: Read Circuit.", 12);
        sendState();
    end

    function onSelectTeachingImage()
        [file, folder] = uigetfile({"*.png;*.jpg;*.jpeg;*.gif;*.webp", "Student images"; "*.*", "All files"});
        if isequal(file, 0)
            sendState();
            return
        end
        state.TeachingImagePath = string(fullfile(folder, file));
        lastTeachOutput = "Student image attached for the next hint or reveal." + newline + state.TeachingImagePath;
        sendState();
    end

    function onImageDropped(payload)
        try
            savedPath = saveDroppedImage(payload);
            state.ImagePath = savedPath;
            lastInputStatus = "Image dropped and saved locally:" + newline + savedPath;
            setPipeline("Image ready. Next: Read Circuit.", 12);
        catch dropError
            lastInputStatus = "Could not save dropped image: " + string(dropError.message);
            setPipeline("Image drop failed. Try another file.", 0);
        end
        sendState();
    end

    function onParseWithGemini()
        try
            setBusy("Reading circuit...", 25);
            parsed = feval('citt.parseCircuitWithGemini', state.ImagePath, state.PromptText);
            state.Spec = parsed.spec;
            state.SpecPath = parsed.spec_path;
            lastInputStatus = parseNextStepText(parsed);
            if strlength(specBlockingIssues(parsed.spec)) > 0
                setPipeline("Clarification needed before Build Model.", 35);
            else
                setPipeline("Circuit spec ready. Next: Prepare Build.", 35);
            end
        catch parseError
            lastInputStatus = "Parse failed: " + sanitizeUserError(parseError.message);
            setPipeline("Read failed. Check input or setup.", 10);
        end
        setIdle();
    end

    function onRunPipeline()
        appendTaskEvent("run_pipeline", "started", "Running circuit read, build brief, and model build.");
        try
            if isempty(currentSpecStruct(state))
                onParseWithGemini();
            end
            spec = currentSpecStruct(state);
            if isempty(spec)
                appendTaskEvent("run_pipeline", "failed", "Circuit read did not produce a spec.");
                saveActiveTask("run_pipeline_failed");
                saveTaskHistory();
                sendState();
                return
            end

            readiness = feval('citt.classifyBuildReadiness', spec);
            if ~readiness.build_ready
                appendTaskEvent("run_pipeline", "paused", "Circuit needs clarification before model build.");
                setPipeline("Clarification needed before building.", 35);
                saveActiveTask("run_pipeline_paused");
                saveTaskHistory();
                sendState();
                return
            end

            if ~agentTaskExists(state)
                onGenerateAgentTask();
            end
            if agentTaskExists(state)
                onRunAgent();
            end

            if ~isempty(state.AgentRun) && fieldText(state.AgentRun, "mode") == "external_agent_pending"
                appendTaskEvent("run_pipeline", "running", "Agent is building the Simscape model.");
            elseif modelExists(state)
                appendTaskEvent("run_pipeline", "completed", "Model is available.");
                openModelIfAvailable();
            else
                appendTaskEvent("run_pipeline", "paused", "Model build needs attention.");
            end
            saveActiveTask("run_pipeline");
            saveTaskHistory();
            sendState();
        catch pipelineError
            busy = false;
            busyText = "";
            appendTaskEvent("run_pipeline", "failed", string(pipelineError.message));
            setPipeline("Run failed. Open details for diagnostics.", 20);
            saveActiveTask("run_pipeline_failed");
            saveTaskHistory();
            sendState();
        end
    end

    function onOpenSpec()
        try
            if exist(state.SpecPath, "file") ~= 2
                lastInputStatus = "No spec JSON exists yet. Read a circuit first.";
                sendState();
                return
            end
            edit(char(state.SpecPath));
            lastInputStatus = "Opened spec: " + state.SpecPath;
        catch openError
            lastInputStatus = "Could not open spec: " + string(openError.message);
        end
        sendState();
    end

    function onGenerateAgentTask()
        try
            setBusy("Preparing build brief...", 45);
            generated = feval('citt.buildAgentTask', state.SpecPath);
            state.AgentTaskPath = generated.task_path;
            lastAgentStatus = "Build brief ready.";
            lastAgentOutput = "Build brief ready. Run will hand this task to the configured agent." + newline + generated.task_path;
            setPipeline("Build brief ready. Next: Build Model.", 55);
        catch taskError
            lastAgentStatus = "Build preparation failed.";
            lastAgentOutput = "Build preparation failed: " + string(taskError.message);
            setPipeline("Prepare Build failed. Resolve the listed issue.", 35);
        end
        setIdle();
    end

    function onRunAgent()
        try
            if ~isempty(state.AgentRun) && fieldText(state.AgentRun, "mode") == "external_agent_pending"
                onAgentPollTick();
                return
            end

            setBusy("Starting model build...", 68);
            runResult = feval('citt.runAgentTask', state.AgentTaskPath, struct("SpecPath", state.SpecPath, "Async", true));
            state.AgentRun = runResult;
            applyAgentRunState(runResult);
            if fieldText(runResult, "mode") == "external_agent_pending"
                startAgentPollTimer();
            else
                stopAgentPollTimer();
            end
        catch runError
            lastAgentStatus = "Build failed.";
            lastAgentOutput = "Model build failed: " + string(runError.message);
            setPipeline("Build failed. See Build Log.", 55);
        end
        setIdle();
    end

    function startAgentPollTimer()
        stopAgentPollTimer();
        agentPollTimer = timer( ...
            "ExecutionMode", "fixedSpacing", ...
            "Period", 2, ...
            "BusyMode", "drop", ...
            "TimerFcn", @(~, ~) onAgentPollTick());
        start(agentPollTimer);
    end

    function stopAgentPollTimer()
        try
            if ~isempty(agentPollTimer) && isvalid(agentPollTimer)
                stop(agentPollTimer);
                delete(agentPollTimer);
            end
        catch
        end
        agentPollTimer = [];
    end

    function onAgentPollTick()
        if isempty(state.AgentRun) || fieldText(state.AgentRun, "mode") ~= "external_agent_pending"
            stopAgentPollTimer();
            return
        end

        try
            polled = feval('citt.pollAgentTask', state.AgentRun);
            state.AgentRun = polled;
            applyAgentRunState(polled);
            if fieldText(polled, "mode") ~= "external_agent_pending"
                stopAgentPollTimer();
                if isTruthy(fieldText(polled, "success"))
                    appendTaskEvent("build_model", "completed", "Model build finished.");
                    openModelIfAvailable();
                else
                    appendTaskEvent("build_model", "failed", "Model build did not produce a ready model.");
                end
                saveActiveTask("agent_complete");
                saveTaskHistory();
                setIdle();
            else
                sendState();
            end
        catch pollError
            stopAgentPollTimer();
            lastAgentStatus = "Agent status failed.";
            lastAgentOutput = "Could not poll external agent: " + string(pollError.message);
            setPipeline("Agent status failed. See Build Log.", 58);
            setIdle();
        end
    end

    function applyAgentRunState(runResult)
        runResult = reconcileAgentRunArtifacts(runResult);
        state.AgentRun = runResult;
        if strlength(fieldText(runResult, "produced_model_path")) > 0 && isTruthy(fieldText(runResult, "success"))
            state.ModelPath = runResult.produced_model_path;
        end
        lastAgentOutput = agentRunSummary(runResult);

        mode = fieldText(runResult, "mode");
        if mode == "external_agent_pending"
            lastAgentStatus = "Building model with agent.";
            setPipeline("Building model with agent...", 68);
        elseif isTruthy(fieldText(runResult, "success"))
            if mode == "local_fallback"
                lastAgentStatus = "Local Simscape model built.";
                setPipeline("Local Simscape model built. Next: Check or Simulate.", 78);
            else
                lastAgentStatus = "Model built by SATK agent.";
                setPipeline("Model built by agent. Next: Check or Simulate.", 78);
            end
        elseif mode == "manual_agent"
            lastAgentStatus = "Manual agent required.";
            setPipeline("Manual agent task opened. Run it in an SATK-configured agent.", 58);
        else
            lastAgentStatus = "Build incomplete.";
            setPipeline("Build incomplete. See Build Log.", 58);
        end
    end

    function reconcileStateArtifacts()
        if isempty(state.AgentRun)
            return
        end

        state.AgentRun = reconcileAgentRunArtifacts(state.AgentRun);
        modelPath = fieldText(state.AgentRun, "produced_model_path");
        if strlength(strtrim(modelPath)) > 0 && isExistingFile(modelPath)
            state.ModelPath = string(modelPath);
        end
        lastAgentOutput = agentRunSummary(state.AgentRun);

        if isTruthy(fieldText(state.AgentRun, "success"))
            mode = fieldText(state.AgentRun, "mode");
            if mode == "local_fallback"
                lastAgentStatus = "Local Simscape model built.";
                setPipeline("Local Simscape model built. Next: Check or Simulate.", 78);
            elseif mode ~= "external_agent_pending"
                lastAgentStatus = "Model built by SATK agent.";
                setPipeline("Model built by agent. Next: Check or Simulate.", 78);
            end
        end
    end

    function runResult = reconcileAgentRunArtifacts(runResult)
        if ~isstruct(runResult)
            return
        end
        modelPath = fieldText(runResult, "produced_model_path");
        if strlength(strtrim(modelPath)) == 0
            modelPath = fieldText(runResult, "expected_model_path");
        end
        if strlength(strtrim(modelPath)) == 0
            modelPath = state.Config.GeneratedModelPath;
        end
        focusPath = firstNonempty(fieldText(runResult, "produced_focus_map_path"), fieldText(runResult, "expected_focus_map_path"), state.Config.FocusMapPath);
        probePath = firstNonempty(fieldText(runResult, "produced_probe_map_path"), fieldText(runResult, "expected_probe_map_path"), state.Config.ProbeMapPath);
        reportPath = firstNonempty(fieldText(runResult, "agent_report_path"), fieldText(runResult, "expected_report_path"), state.Config.AgentReportPath);

        artifactsExist = isExistingFile(modelPath) && isExistingFile(focusPath) && ...
            isExistingFile(probePath) && isExistingFile(reportPath);
        if artifactsExist
            runResult.produced_model_path = string(modelPath);
            runResult.produced_focus_map_path = string(focusPath);
            runResult.produced_probe_map_path = string(probePath);
            runResult.agent_report_path = string(reportPath);
            exitStatus = str2double(fieldText(runResult, "exit_status"));
            if exitStatus == 0 || isTruthy(fieldText(runResult, "success"))
                runResult.success = true;
                runResult.summary = "External SATK agent completed and produced CiTT model artifacts.";
            end
        end
    end

    function value = firstNonempty(varargin)
        value = "";
        for i = 1:nargin
            candidate = string(varargin{i});
            if strlength(strtrim(candidate)) > 0
                value = candidate;
                return
            end
        end
    end

    function onOpenTask()
        try
            edit(char(state.AgentTaskPath));
            lastAgentStatus = "Opened build brief.";
        catch openError
            lastAgentOutput = "Could not open task: " + string(openError.message);
        end
        sendState();
    end

    function onRefreshSetup()
        state.LastSetupReport = feval('citt.checkSetup');
        lastAgentStatus = "Setup refreshed.";
        sendState();
    end

    function onSelectModel()
        [file, folder] = uigetfile({"*.slx;*.mdl", "Simulink models"; "*.*", "All files"});
        if isequal(file, 0)
            sendState();
            return
        end
        state.ModelPath = string(fullfile(folder, file));
        lastModelStatus = "Model selected.";
        refreshModelSnapshot("");
        sendState();
    end

    function onOpenModel()
        try
            opened = feval('citt.openOrCreateModel', state.ModelPath);
            lastModelStatus = opened.message;
            lastModelOutput = "Model opened." + newline + opened.model_path;
            setPipeline("Model open in Simulink. Next: Check.", 78);
            refreshModelSnapshot("");
        catch openError
            lastModelStatus = "Open model failed.";
            lastModelOutput = "Open model failed: " + string(openError.message);
        end
        sendState();
    end

    function onRefreshModelSnapshot()
        refreshModelSnapshot("");
        sendState();
    end

    function openModelIfAvailable()
        if strlength(strtrim(state.ModelPath)) == 0 || ~isExistingFile(state.ModelPath)
            return
        end
        try
            opened = feval('citt.openOrCreateModel', state.ModelPath);
            lastModelStatus = opened.message;
            lastModelOutput = "Model opened." + newline + opened.model_path;
            setPipeline("Model opened in Simulink.", 82);
            refreshModelSnapshot("");
        catch openError
            lastModelStatus = "Model built, but opening failed.";
            lastModelOutput = "Could not open model automatically: " + string(openError.message);
        end
    end

    function refreshModelSnapshot(targetSystem)
        try
            outputPath = snapshotPathForActiveTask();
            captured = feval('citt.captureModelSnapshot', state.ModelPath, struct( ...
                "OutputPath", outputPath, ...
                "TargetSystem", string(targetSystem)));
            state.ModelSnapshotPath = captured.image_path;
            lastModelPreviewStatus = captured.message + " " + captured.target_system;
        catch snapshotError
            lastModelPreviewStatus = "Preview update failed: " + string(snapshotError.message);
        end
    end

    function path = snapshotPathForActiveTask()
        ensureActiveTask();
        safeTaskId = regexprep(char(activeTaskId), "[^A-Za-z0-9_\\-]", "_");
        if isempty(safeTaskId)
            safeTaskId = "current";
        end
        path = string(fullfile(state.Config.WorkDir, "citt_model_snapshot_" + string(safeTaskId) + ".png"));
    end

    function target = snapshotTargetFromResult(result)
        target = "";
        if isstruct(result) && isfield(result, "highlighted_paths") && ~isempty(result.highlighted_paths)
            target = string(result.highlighted_paths(1));
        end
    end

    function onCheckModel()
        try
            setBusy("Checking model...", 86);
            checked = feval('citt.runModelCheck', state.ModelPath);
            state.LastModelCheck = checked;
            lastModelStatus = "Model check complete.";
            lastModelOutput = modelCheckSummary(checked);
            setPipeline("Model check complete. Next: Simulate or Teach.", 90);
        catch checkError
            lastModelStatus = "Model check failed.";
            lastModelOutput = string(checkError.message);
            setPipeline("Model check failed. See Model Lab output.", 78);
        end
        setIdle();
    end

    function onRunSimulation()
        try
            setBusy("Running simulation...", 94);
            simulated = feval('citt.runSimulation', state.ModelPath);
            state.LastSimulation = simulated;
            lastModelStatus = "Simulation complete.";
            lastModelOutput = simulationSummary(simulated);
            setPipeline("Simulation complete. Teach and compare are available.", 100);
        catch simError
            lastModelStatus = "Simulation failed.";
            lastModelOutput = string(simError.message);
            setPipeline("Simulation failed. See Model Lab output.", 90);
        end
        setIdle();
    end

    function onRunBodeAnalysis()
        try
            setBusy("Building Bode analysis...", 92);
            bode = feval('citt.runBodeAnalysis', state);
            state.LastBode = bode;
            lastModelStatus = "Bode analysis complete.";
            lastModelOutput = bodeSummary(bode);
            setPipeline("Bode analysis ready.", 94);
        catch bodeError
            lastModelStatus = "Bode analysis failed.";
            lastModelOutput = "Bode analysis failed: " + string(bodeError.message);
            setPipeline("Bode analysis failed. Check spec values or I/O points.", 84);
        end
        setIdle();
    end

    function onRunCommand(commandText)
        try
            setBusy("Running command...", 86);
            commandResult = feval('citt.runNaturalCommand', string(commandText), state);
            lastModelStatus = commandResult.message;
            lastModelOutput = feval('citt.util.jsonEncode', commandResult);
            refreshSnapshotForCommand(commandResult);
            setPipeline("Command complete: " + commandResult.action, 90);
        catch commandError
            lastModelStatus = "Command failed.";
            lastModelOutput = "Command failed: " + string(commandError.message);
            setPipeline("Command failed. Try a more direct phrase.", 78);
        end
        setIdle();
    end

    function refreshSnapshotForCommand(commandResult)
        action = fieldText(commandResult, "action");
        if action ~= "highlight_focus" && action ~= "zoom_focus" && action ~= "clear_highlights"
            return
        end
        targetSystem = "";
        if isfield(commandResult, "details") && isstruct(commandResult.details)
            if action == "zoom_focus"
                targetSystem = fieldText(commandResult.details, "opened_path");
            else
                targetSystem = snapshotTargetFromResult(commandResult.details);
            end
        end
        refreshModelSnapshot(targetSystem);
    end

    function onStartTeaching()
        try
            setBusy("Building teaching plan...", 92);
            built = feval('citt.buildTeachingPlan', state.SpecPath, state.FocusMapPath, state.LastModelCheck, state.LastSimulation);
            state.TeachingPlan = built.plan;
            state.TeachingStepIndex = 1;
            state.HintLevel = 0;
            lastTeachOutput = currentStepQuestion();
            lastTeachStatus = "Teaching plan ready.";
            setPipeline("Teaching plan ready. Work through the focus step.", 92);
        catch teachError
            lastTeachOutput = "Teaching plan failed: " + string(teachError.message);
            lastTeachStatus = "Teaching plan failed.";
            setPipeline("Teaching plan failed. Check focus map output.", 78);
        end
        setIdle();
    end

    function onNextHint()
        if isempty(state.TeachingPlan)
            onStartTeaching();
        end
        try
            validateTeachingImage();
            setBusy("Reading student answer...", 92);
            answer = teachingSubmissionText();
            turn = feval('citt.runSocraticTurn', state.TeachingPlan, state.TeachingStepIndex, answer, ...
                struct("Action", "hint", "HintLevel", state.HintLevel, "AnswerImagePath", state.TeachingImagePath));
            state.HintLevel = turn.next_hint_level;
            lastTeachStatus = "Classification: " + turn.classification;
            lastTeachOutput = turn.message;
        catch hintError
            lastTeachOutput = "Hint failed: " + string(hintError.message);
            lastTeachStatus = "Hint failed.";
        end
        setIdle();
    end

    function onReveal()
        if isempty(state.TeachingPlan)
            onStartTeaching();
        end
        try
            validateTeachingImage();
            turn = feval('citt.runSocraticTurn', state.TeachingPlan, state.TeachingStepIndex, teachingSubmissionText(), ...
                struct("Action", "reveal", "AnswerImagePath", state.TeachingImagePath));
            lastTeachStatus = "Reveal shown for " + turn.step_id;
            lastTeachOutput = turn.message;
        catch revealError
            lastTeachOutput = "Reveal failed: " + string(revealError.message);
            lastTeachStatus = "Reveal failed.";
        end
        sendState();
    end

    function onHighlightCurrent(focusId)
        if strlength(strtrim(focusId)) == 0
            focusId = firstOrEmpty(focusValues());
        end
        try
            highlighted = feval('citt.highlightFocus', state.ModelPath, state.FocusMapPath, focusId);
            lastTeachStatus = "Highlighted: " + string(highlighted.success);
            lastTeachOutput = focusActionSummary("Highlight", highlighted);
            refreshModelSnapshot(snapshotTargetFromResult(highlighted));
        catch highlightError
            lastTeachStatus = "Highlight failed.";
            lastTeachOutput = "Highlight failed: " + string(highlightError.message);
        end
        sendState();
    end

    function onZoomCurrent(focusId)
        if strlength(strtrim(focusId)) == 0
            focusId = firstOrEmpty(focusValues());
        end
        try
            zoomed = feval('citt.zoomToFocus', state.ModelPath, state.FocusMapPath, focusId);
            lastTeachStatus = zoomed.message;
            lastTeachOutput = focusActionSummary("Zoom", zoomed);
            refreshModelSnapshot(fieldText(zoomed, "opened_path"));
        catch zoomError
            lastTeachStatus = "Zoom failed.";
            lastTeachOutput = "Zoom failed: " + string(zoomError.message);
        end
        sendState();
    end

    function onRunNaturalClearHighlights()
        try
            cleared = feval('citt.clearHighlights', state.ModelPath);
            lastTeachStatus = "Highlights cleared.";
            lastTeachOutput = "Model focus cleared." + newline + "Model: " + fieldText(cleared, "model_name");
            refreshModelSnapshot("");
        catch clearError
            lastTeachStatus = "Clear failed.";
            lastTeachOutput = "Could not clear highlights: " + string(clearError.message);
        end
        sendState();
    end

    function onAddProbe(targetId)
        if strlength(strtrim(targetId)) == 0
            targetId = firstOrEmpty(probeValues());
        end
        try
            probed = feval('citt.addProbe', state.ModelPath, targetId, state.ProbeMapPath, state.SpecPath);
            state.LastProbe = probed;
            lastProbeStatus = "Probe plan success: " + string(probed.success);
            lastProbeOutput = probePlanSummary(probed);
            setPipeline("Probe ready. Next: compare lab delta or export evidence.", 100);
        catch probeError
            lastProbeStatus = "Probe failed.";
            lastProbeOutput = "Probe failed: " + string(probeError.message);
        end
        sendState();
    end

    function onSelectCsv()
        [file, folder] = uigetfile({"*.csv", "CSV files"; "*.*", "All files"});
        if isequal(file, 0)
            sendState();
            return
        end
        state.LabCsvPath = string(fullfile(folder, file));
        lastDeltaStatus = "CSV selected.";
        sendState();
    end

    function onCompareLabDelta()
        try
            delta = feval('citt.compareLabDelta', struct(), struct(), state.LabCsvPath, struct("Context", state));
            state.LastLabDelta = delta;
            lastDeltaStatus = "Lab error rows: " + string(numel(delta.rows)) + " | causes: " + string(numel(delta.likely_causes));
            lastDeltaOutput = labErrorSummary(delta);
            setPipeline("Lab delta comparison ready.", 100);
        catch deltaError
            lastDeltaStatus = "Lab Delta failed.";
            lastDeltaOutput = "Lab Delta failed: " + string(deltaError.message);
        end
        sendState();
    end

    function onAnalyzeLabError()
        try
            setBusy("Analyzing lab error...", 94);
            analyzed = feval('citt.analyzeLabError', state.LabCsvPath, state);
            state.LastLabDelta = analyzed;
            lastDeltaStatus = "Lab error causes: " + string(numel(analyzed.likely_causes));
            lastDeltaOutput = labErrorSummary(analyzed);
            setPipeline("Lab error analysis ready.", 100);
        catch labError
            lastDeltaStatus = "Lab error analysis failed.";
            lastDeltaOutput = "Lab error analysis failed: " + string(labError.message);
            setPipeline("Lab error analysis failed. Check CSV format.", 90);
        end
        setIdle();
    end

    function onRunRequirements()
        try
            setBusy("Checking requirements...", 96);
            checked = feval('citt.runRequirementChecks', state);
            state.LastRequirements = checked;
            lastVerificationStatus = "Requirement check complete.";
            lastVerificationOutput = requirementRunSummary(checked);
            setPipeline("Requirement table ready.", 100);
        catch requirementError
            lastVerificationStatus = "Requirement check failed.";
            lastVerificationOutput = "Requirement check failed: " + string(requirementError.message);
        end
        setIdle();
    end

    function onRunSweep()
        try
            setBusy("Running tolerance sweep...", 96);
            swept = feval('citt.runParameterSweep', state);
            state.LastSweep = swept;
            lastVerificationStatus = "Sweep complete.";
            lastVerificationOutput = sweepSummary(swept);
            setPipeline("Tolerance sweep ready.", 100);
        catch sweepError
            lastVerificationStatus = "Sweep failed.";
            lastVerificationOutput = "Sweep failed: " + string(sweepError.message);
        end
        setIdle();
    end

    function onRunFaults()
        try
            setBusy("Building fault scenarios...", 96);
            faults = feval('citt.runFaultInjection', state);
            state.LastFaults = faults;
            lastVerificationStatus = "Fault scenarios ready.";
            lastVerificationOutput = faultSummary(faults);
            setPipeline("Fault injection report ready.", 100);
        catch faultError
            lastVerificationStatus = "Fault generation failed.";
            lastVerificationOutput = "Fault generation failed: " + string(faultError.message);
        end
        setIdle();
    end

    function onBuildExplainability()
        try
            setBusy("Building explainability map...", 96);
            explained = feval('citt.buildExplainabilityMap', state);
            state.LastExplainability = explained;
            lastVerificationStatus = "Explainability map ready.";
            lastVerificationOutput = explainabilitySummary(explained);
            setPipeline("Explainability map ready.", 100);
        catch explainError
            lastVerificationStatus = "Explainability map failed.";
            lastVerificationOutput = "Explainability map failed: " + string(explainError.message);
        end
        setIdle();
    end

    function onHighlightExplainability(actionId)
        if strlength(strtrim(actionId)) == 0
            actionId = firstOrEmpty(explainabilityValues());
        end
        try
            highlighted = feval('citt.highlightExplainabilityAction', ...
                state.ModelPath, state.Config.ExplainabilityMapPath, actionId, state.FocusMapPath);
            lastVerificationStatus = highlighted.message;
            lastVerificationOutput = feval('citt.util.jsonEncode', highlighted);
        catch highlightError
            lastVerificationStatus = "Explainability highlight failed.";
            lastVerificationOutput = "Explainability highlight failed: " + string(highlightError.message);
        end
        sendState();
    end

    function onRunAssessment(payload)
        request = struct();
        request.concept = payloadText(payload, "assessmentConcept", "cutoff frequency output node");
        request.before_answer = payloadText(payload, "beforeAnswer", "");
        request.after_answer = payloadText(payload, "afterAnswer", "");
        request.hint_levels_used = payloadNumber(payload, "hintLevels", 0);
        try
            setBusy("Scoring learning gain...", 96);
            assessed = feval('citt.runLearningAssessment', request);
            state.LastAssessment = assessed;
            lastAssessmentStatus = "Assessment complete.";
            lastAssessmentOutput = assessmentSummary(assessed);
            setPipeline("Assessment evidence ready.", 100);
        catch assessmentError
            lastAssessmentStatus = "Assessment failed.";
            lastAssessmentOutput = "Assessment failed: " + string(assessmentError.message);
        end
        setIdle();
    end

    function onBuildEconomics(payload)
        students = payloadNumber(payload, "students", 30);
        try
            setBusy("Building cost plan...", 96);
            plan = feval('citt.buildEconomicsPlan', struct("Students", students));
            state.LastEconomics = plan;
            lastAssessmentStatus = "Cost plan ready.";
            lastAssessmentOutput = economicsSummary(plan);
            setPipeline("Economics plan ready.", 100);
        catch economicsError
            lastAssessmentStatus = "Cost plan failed.";
            lastAssessmentOutput = "Cost plan failed: " + string(economicsError.message);
        end
        setIdle();
    end

    function onBuildScopeGuardrail()
        try
            setBusy("Building scope guardrail...", 96);
            guardrail = feval('citt.buildScopeGuardrail', state);
            state.LastScopeGuardrail = guardrail;
            lastAssessmentStatus = "Scope guardrail ready.";
            lastAssessmentOutput = scopeSummary(guardrail);
            setPipeline("Scope guardrail ready.", 100);
        catch scopeError
            lastAssessmentStatus = "Scope guardrail failed.";
            lastAssessmentOutput = "Scope guardrail failed: " + string(scopeError.message);
        end
        setIdle();
    end

    function onExportEvidencePack()
        try
            setBusy("Exporting evidence pack...", 100);
            exported = feval('citt.exportEvidencePack', state, struct("OutputPath", state.EvidencePackPath));
            state.LastEvidencePack = exported;
            lastEvidenceStatus = "Evidence pack exported.";
            lastEvidenceOutput = evidencePackSummary(exported);
            setPipeline("Evidence pack exported.", 100);
        catch evidenceError
            lastEvidenceStatus = "Evidence pack export failed.";
            lastEvidenceOutput = "Evidence Pack failed: " + string(evidenceError.message);
            setPipeline("Evidence pack failed. See output.", 92);
        end
        setIdle();
    end

    function onOpenEvidencePack()
        try
            if exist(state.EvidencePackPath, "file") ~= 2
                lastEvidenceOutput = "No evidence pack exists yet. Click Export Evidence Pack first.";
                sendState();
                return
            end
            edit(char(state.EvidencePackPath));
            lastEvidenceStatus = "Opened evidence pack.";
        catch openError
            lastEvidenceOutput = "Could not open evidence pack: " + string(openError.message);
        end
        sendState();
    end

    function sendState()
        reconcileStateArtifacts();

        ui = struct();
        ui.kind = "state";
        ui.activePage = activePage;
        ui.busy = busy;
        ui.busyText = busyText;
        ui.pipelineMessage = pipelineMessage;
        ui.pipelineProgress = pipelineProgress;
        ui.runStatus = runStatusState();
        ui.status = compactStatus(state);
        [nextLabel, nextAction, nextDestination] = nextActionForState(state);
        ui.nextAction = struct("label", nextLabel, "action", nextAction, "destination", nextDestination);

        ui.paths = struct( ...
            "imagePath", state.ImagePath, ...
            "prompt", state.PromptText, ...
            "specPath", state.SpecPath, ...
            "agentTaskPath", state.AgentTaskPath, ...
            "modelPath", state.ModelPath, ...
            "modelSnapshotPath", state.ModelSnapshotPath, ...
            "teachingImagePath", state.TeachingImagePath, ...
            "studentAnswer", fieldText(state, "StudentAnswer"), ...
            "labCsvPath", state.LabCsvPath, ...
            "opAmpPart", fieldText(state, "OpAmpPart"), ...
            "evidencePath", state.EvidencePackPath);

        ui.setup = setupState(state.LastSetupReport);
        ui.read = struct( ...
            "inputStatus", emptyText(lastInputStatus, inputStatusText(state)), ...
            "specSummary", currentSpecPreview(state), ...
            "readiness", readinessSummaryText(state), ...
            "trace", readAdvancedText(state));
        ui.build = struct( ...
            "steps", buildStepsState(state), ...
            "agentStatus", lastAgentStatus, ...
            "agentOutput", emptyText(lastAgentOutput, "Build log will appear here."), ...
            "modelStatus", lastModelStatus, ...
            "modelOutput", emptyText(lastModelOutput, "Model output will appear here."), ...
            "setupReport", setupOverviewText(state.LastSetupReport), ...
            "paths", pathStatusText(state));
        ui.teach = struct( ...
            "steps", teachingStepsText(state), ...
            "currentStep", currentStepText(), ...
            "output", emptyText(lastTeachOutput, currentStepQuestion()), ...
            "status", lastTeachStatus, ...
            "focusItems", focusValues());
        ui.probe = struct( ...
            "probeItems", probeValues(), ...
            "probeStatus", lastProbeStatus, ...
            "probeOutput", emptyText(lastProbeOutput, "Probe output will appear here."), ...
            "deltaStatus", lastDeltaStatus, ...
            "deltaOutput", emptyText(lastDeltaOutput, "Lab Delta output will appear here."));
        ui.evidence = struct( ...
            "verificationStatus", lastVerificationStatus, ...
            "verificationOutput", emptyText(lastVerificationOutput, "Proof reports will appear here."), ...
            "assessmentStatus", lastAssessmentStatus, ...
            "assessmentOutput", emptyText(lastAssessmentOutput, "Plan and learning reports will appear here."), ...
            "evidenceStatus", lastEvidenceStatus, ...
            "evidenceOutput", emptyText(lastEvidenceOutput, "Evidence pack output will appear here."), ...
            "contents", evidenceContentsText(state), ...
            "verificationReports", verificationReportText(state), ...
            "assessmentReports", assessmentReportText(state), ...
            "explainabilityItems", explainabilityValues());
        ui.tasks = taskListState();
        ui.thread = threadState();
        ui.modelPreview = modelPreviewState();
        ui.assumptions = assumptionsState();
        ui.sources = sourceState();
        ui.workflowSteps = workflowStepState();
        ui.environment = environmentState();
        ui.settings = settingsState();
        ui.settingsStatus = lastSettingsStatus;

        try
            handles.web.Data = ui;
            drawnow limitrate;
        catch
        end
    end

    function sendToast(message, tone)
        try
            handles.web.Data = struct("kind", "toast", "message", string(message), "tone", string(tone));
            drawnow limitrate;
        catch
        end
    end

    function setBusy(message, value)
        busy = true;
        busyText = string(message);
        setPipeline(message, value);
        sendState();
    end

    function setIdle()
        busy = false;
        busyText = "";
        sendState();
    end

    function setPipeline(message, value)
        pipelineMessage = string(message);
        if nargin >= 2 && ~isempty(value)
            pipelineProgress = max(0, min(100, round(double(value))));
        end
    end

    function onCloseApp(fig)
        stopAgentPollTimer();
        saveActiveTask("close_app");
        saveTaskHistory();
        try
            delete(fig);
        catch
        end
    end

    function resetUiOutputs()
        lastInputStatus = "";
        lastAgentOutput = "";
        lastAgentStatus = "Build model from the parsed circuit.";
        lastModelOutput = "";
        lastModelStatus = "Open, check, or simulate the generated model.";
        lastModelPreviewStatus = "No model preview yet.";
        lastTeachOutput = "";
        lastTeachStatus = "Waiting for teaching plan.";
        lastProbeOutput = "";
        lastProbeStatus = "Select a focus or probe target.";
        lastDeltaOutput = "";
        lastDeltaStatus = "Compare lab data after probes are available.";
        lastVerificationOutput = "";
        lastVerificationStatus = "Evidence actions are ready.";
        lastAssessmentOutput = "";
        lastAssessmentStatus = "Learning and planning reports are ready.";
        lastEvidenceOutput = "";
        lastEvidenceStatus = "Export an evidence pack when the model has enough proof.";
        lastSettingsStatus = "Settings are loaded from the local CiTT work folder.";
    end

    function currentState = clearTaskState(currentState)
        currentState.ImagePath = "";
        currentState.PromptText = "";
        currentState.Spec = [];
        currentState.SpecPath = "";
        currentState.AgentTaskPath = "";
        currentState.AgentRun = [];
        currentState.ModelPath = "";
        currentState.ModelSnapshotPath = "";
        currentState.TeachingPlan = [];
        currentState.TeachingStepIndex = 1;
        currentState.HintLevel = 0;
        currentState.TeachingImagePath = "";
        currentState.LastModelCheck = [];
        currentState.LastSimulation = [];
        currentState.LastBode = [];
        currentState.LastProbe = [];
        currentState.LabCsvPath = "";
        currentState.OpAmpPart = "";
        currentState.LastLabDelta = [];
        currentState.EvidencePackPath = currentState.Config.EvidencePackPath;
        currentState.LastEvidencePack = [];
        currentState.LastRequirements = [];
        currentState.LastSweep = [];
        currentState.LastFaults = [];
        currentState.LastExplainability = [];
        currentState.LastAssessment = [];
        currentState.LastEconomics = [];
        currentState.LastScopeGuardrail = [];
    end

    function tasks = loadTaskHistory()
        tasks = emptyTasks();
        path = state.Config.TaskHistoryPath;
        if exist(path, "file") ~= 2
            return
        end
        try
            data = jsondecode(fileread(path));
            if isfield(data, "active_task_id")
                activeTaskId = string(data.active_task_id);
            end
            if isfield(data, "tasks")
                tasks = normalizeTasks(data.tasks);
            end
        catch
            tasks = emptyTasks();
        end
    end

    function saveTaskHistory()
        tasksToSave = persistableTasks();
        data = struct( ...
            "version", 1, ...
            "active_task_id", activeTaskId, ...
            "updated_at", nowText(), ...
            "tasks", tasksToSave);
        writeJson(state.Config.TaskHistoryPath, data);
    end

    function tasks = persistableTasks()
        tasks = emptyTasks();
        for i = 1:numel(taskHistory)
            if hasMeaningfulTask(taskHistory(i))
                tasks(end + 1, 1) = taskHistory(i); %#ok<AGROW>
            end
        end
    end

    function ensureActiveTask()
        if ~isempty(taskHistory) && strlength(activeTaskId) > 0 && findTaskIndex(activeTaskId) > 0
            return
        end
        if ~isempty(taskHistory)
            activeTaskId = string(taskHistory(1).id);
            return
        end
        activeTaskId = makeTaskId();
        taskHistory = makeTaskRecord(activeTaskId, "New circuit task");
    end

    function restoreActiveTaskIfAvailable()
        index = findTaskIndex(activeTaskId);
        if index > 0 && hasMeaningfulTask(taskHistory(index))
            restoreTaskSnapshot(taskHistory(index));
            setPipeline(taskHistory(index).summary, taskHistory(index).progress);
        end
    end

    function saveActiveTask(reason)
        ensureActiveTask();
        index = findTaskIndex(activeTaskId);
        if index == 0
            return
        end
        task = taskHistory(index);
        task.title = taskTitleFromState();
        task.updated_at = nowText();
        task.status = "active";
        task.stage = taskStageFromState();
        task.summary = taskSummaryFromState(reason);
        task.progress = pipelineProgress;
        task.prompt = state.PromptText;
        task.image_path = state.ImagePath;
        task.spec_path = state.SpecPath;
        task.agent_task_path = state.AgentTaskPath;
        task.model_path = state.ModelPath;
        task.model_snapshot_path = state.ModelSnapshotPath;
        task.evidence_path = state.EvidencePackPath;
        taskHistory(index) = task;
    end

    function appendTaskEvent(action, status, summary)
        ensureActiveTask();
        index = findTaskIndex(activeTaskId);
        if index == 0
            return
        end
        event = struct( ...
            "time", nowText(), ...
            "action", actionLabel(action), ...
            "status", string(status), ...
            "summary", string(summary));
        events = normalizeEvents(taskHistory(index).events);
        taskHistory(index).events = [events(:); event];
    end

    function record = makeTaskRecord(taskId, title)
        record = struct( ...
            "id", string(taskId), ...
            "title", string(title), ...
            "created_at", nowText(), ...
            "updated_at", nowText(), ...
            "status", "active", ...
            "stage", "read", ...
            "summary", "Ready for circuit input.", ...
            "progress", 0, ...
            "prompt", "", ...
            "image_path", "", ...
            "spec_path", state.SpecPath, ...
            "agent_task_path", state.AgentTaskPath, ...
            "model_path", state.ModelPath, ...
            "model_snapshot_path", state.ModelSnapshotPath, ...
            "evidence_path", state.EvidencePackPath, ...
            "events", emptyEvents());
    end

    function tasks = normalizeTasks(rawTasks)
        tasks = emptyTasks();
        if isempty(rawTasks) || ~isstruct(rawTasks)
            return
        end
        for i = 1:numel(rawTasks)
            task = makeTaskRecord(taskField(rawTasks(i), "id", makeTaskId()), taskField(rawTasks(i), "title", "Saved task"));
            task.created_at = taskField(rawTasks(i), "created_at", task.created_at);
            task.updated_at = taskField(rawTasks(i), "updated_at", task.updated_at);
            task.status = taskField(rawTasks(i), "status", task.status);
            task.stage = taskField(rawTasks(i), "stage", task.stage);
            task.summary = taskField(rawTasks(i), "summary", task.summary);
            task.progress = taskNumber(rawTasks(i), "progress", task.progress);
            task.prompt = taskField(rawTasks(i), "prompt", "");
            task.image_path = taskField(rawTasks(i), "image_path", "");
            task.spec_path = taskField(rawTasks(i), "spec_path", state.SpecPath);
            task.agent_task_path = taskField(rawTasks(i), "agent_task_path", state.AgentTaskPath);
            task.model_path = taskField(rawTasks(i), "model_path", state.ModelPath);
            task.model_snapshot_path = taskField(rawTasks(i), "model_snapshot_path", state.ModelSnapshotPath);
            task.evidence_path = taskField(rawTasks(i), "evidence_path", state.EvidencePackPath);
            if isfield(rawTasks(i), "events")
                task.events = normalizeEvents(rawTasks(i).events);
            end
            tasks(end + 1, 1) = task; %#ok<AGROW>
        end
    end

    function events = normalizeEvents(rawEvents)
        events = emptyEvents();
        if isempty(rawEvents) || ~isstruct(rawEvents)
            return
        end
        for i = 1:numel(rawEvents)
            event = struct( ...
                "time", taskField(rawEvents(i), "time", ""), ...
                "action", taskField(rawEvents(i), "action", ""), ...
                "status", taskField(rawEvents(i), "status", ""), ...
                "summary", taskField(rawEvents(i), "summary", ""));
            events(end + 1, 1) = event; %#ok<AGROW>
        end
    end

    function tasks = emptyTasks()
        tasks = repmat(struct( ...
            "id", "", ...
            "title", "", ...
            "created_at", "", ...
            "updated_at", "", ...
            "status", "", ...
            "stage", "", ...
            "summary", "", ...
            "progress", 0, ...
            "prompt", "", ...
            "image_path", "", ...
            "spec_path", "", ...
            "agent_task_path", "", ...
            "model_path", "", ...
            "model_snapshot_path", "", ...
            "evidence_path", "", ...
            "events", emptyEvents()), 0, 1);
    end

    function events = emptyEvents()
        events = repmat(struct("time", "", "action", "", "status", "", "summary", ""), 0, 1);
    end

    function index = findTaskIndex(taskId)
        index = 0;
        for i = 1:numel(taskHistory)
            if string(taskHistory(i).id) == string(taskId)
                index = i;
                return
            end
        end
    end

    function restoreTaskSnapshot(task)
        resetUiOutputs();
        state.PromptText = taskField(task, "prompt", "");
        state.ImagePath = taskField(task, "image_path", "");
        state.SpecPath = taskField(task, "spec_path", state.SpecPath);
        state.AgentTaskPath = taskField(task, "agent_task_path", state.AgentTaskPath);
        state.ModelPath = taskField(task, "model_path", state.ModelPath);
        state.ModelSnapshotPath = taskField(task, "model_snapshot_path", state.ModelSnapshotPath);
        state.EvidencePackPath = taskField(task, "evidence_path", state.EvidencePackPath);
        state.Spec = [];
        if exist(state.SpecPath, "file") == 2
            try
                state.Spec = jsondecode(fileread(state.SpecPath));
            catch
                state.Spec = [];
            end
        end
        lastInputStatus = "Loaded saved task: " + taskField(task, "title", "Saved task");
    end

    function items = taskListState()
        items = repmat(struct( ...
            "id", "", ...
            "title", "", ...
            "summary", "", ...
            "stage", "", ...
            "updatedAt", "", ...
            "progress", 0, ...
            "active", false), 0, 1);
        for i = 1:numel(taskHistory)
            if ~hasMeaningfulTask(taskHistory(i))
                continue
            end
            item = struct( ...
                "id", string(taskHistory(i).id), ...
                "title", string(taskHistory(i).title), ...
                "summary", string(taskHistory(i).summary), ...
                "stage", string(taskHistory(i).stage), ...
                "updatedAt", string(taskHistory(i).updated_at), ...
                "progress", taskHistory(i).progress, ...
                "active", string(taskHistory(i).id) == activeTaskId);
            items(end + 1, 1) = item; %#ok<AGROW>
        end
    end

    function thread = threadState()
        messages = emptyThreadMessages();
        spec = currentSpecStruct(state);
        if strlength(strtrim(state.PromptText)) > 0 || strlength(strtrim(state.ImagePath)) > 0
            messages = appendThreadMessage(messages, "user", "Circuit input", inputThreadText(), "input");
        end
        if ~isempty(spec) || strlength(strtrim(lastInputStatus)) > 0
            messages = appendThreadMessage(messages, "assistant", "Circuit read", readSummaryLine(), "read", readDetailText());
        end
        if hasBuildThreadOutput()
            messages = appendThreadMessage(messages, "assistant", "Model build", buildSummaryLine(), "build", buildThreadText());
        end
        if ~isempty(state.TeachingPlan) || strlength(strtrim(lastTeachOutput)) > 0
            messages = appendThreadMessage(messages, "assistant", "Teaching", teachSummaryLine(), "teach", teachThreadText());
        end
        if ~isempty(state.LastProbe) || ~isempty(state.LastLabDelta) || strlength(strtrim(lastProbeOutput + lastDeltaOutput)) > 0
            messages = appendThreadMessage(messages, "assistant", "Probe and lab delta", probeSummaryLine(), "probe", probeThreadText());
        end
        if hasEvidenceThreadOutput()
            messages = appendThreadMessage(messages, "assistant", "Evidence", evidenceSummaryLine(), "evidence", evidenceThreadText());
        end
        thread = struct( ...
            "taskId", activeTaskId, ...
            "title", taskTitleFromState(), ...
            "subtitle", pipelineMessage, ...
            "messages", messages);
    end

    function tf = hasBuildThreadOutput()
        tf = ~isempty(state.AgentRun) || agentTaskExists(state) || modelExists(state) || ...
            ~isempty(state.LastModelCheck) || ~isempty(state.LastSimulation) || ...
            strlength(strtrim(lastAgentOutput + lastModelOutput)) > 0;
    end

    function tf = hasEvidenceThreadOutput()
        tf = ~isempty(state.LastEvidencePack) || ~isempty(state.LastRequirements) || ...
            ~isempty(state.LastSweep) || ~isempty(state.LastFaults) || ...
            ~isempty(state.LastExplainability) || ~isempty(state.LastAssessment) || ...
            ~isempty(state.LastEconomics) || ~isempty(state.LastScopeGuardrail) || ...
            strlength(strtrim(lastVerificationOutput + lastAssessmentOutput + lastEvidenceOutput)) > 0;
    end

    function tf = hasTaskEvents(taskId)
        index = findTaskIndex(taskId);
        tf = index > 0 && ~isempty(taskHistory(index).events);
    end

    function tf = hasMeaningfulTask(task)
        tf = false;
        if ~isstruct(task)
            return
        end
        tf = strlength(strtrim(taskField(task, "prompt", ""))) > 0 || ...
            strlength(strtrim(taskField(task, "image_path", ""))) > 0 || ...
            strlength(strtrim(taskField(task, "model_path", ""))) > 0 || ...
            strlength(strtrim(taskField(task, "model_snapshot_path", ""))) > 0 || ...
            hasTaskEventList(task);
    end

    function tf = hasTaskEventList(task)
        tf = false;
        if ~isstruct(task) || ~isfield(task, "events")
            return
        end
        events = normalizeEvents(task.events);
        for eventIndex = 1:numel(events)
            action = lower(strtrim(string(events(eventIndex).action)));
            summary = lower(strtrim(string(events(eventIndex).summary)));
            if action == "" || action == "new task" || action == "new_task"
                continue
            end
            if contains(summary, "started a new citt task")
                continue
            end
            tf = true;
            return
        end
    end

    function messages = emptyThreadMessages()
        messages = repmat(struct("role", "", "title", "", "body", "", "tone", "", "detail", ""), 0, 1);
    end

    function messages = appendThreadMessage(messages, role, title, body, tone, detail)
        if nargin < 6
            detail = "";
        end
        if strlength(strtrim(string(body))) == 0
            body = "No output yet.";
        end
        messages(end + 1, 1) = struct( ...
            "role", string(role), ...
            "title", string(title), ...
            "body", string(body), ...
            "tone", string(tone), ...
            "detail", string(detail));
    end

    function sources = sourceState()
        sources = repmat(struct("label", "", "path", "", "status", ""), 0, 1);
        sources = appendSource(sources, "Circuit image", state.ImagePath);
        sources = appendSource(sources, "Spec JSON", state.SpecPath);
        sources = appendSource(sources, "Agent task", state.AgentTaskPath);
        sources = appendSource(sources, "Simscape model", state.ModelPath);
        sources = appendSource(sources, "Model preview", state.ModelSnapshotPath);
        sources = appendSource(sources, "Focus map", state.FocusMapPath);
        sources = appendSource(sources, "Probe map", state.ProbeMapPath);
        sources = appendSource(sources, "Evidence pack", state.EvidencePackPath);
        sources = appendSource(sources, "Settings", state.Config.SettingsPath);
        sources = appendSource(sources, "Task history", state.Config.TaskHistoryPath);
    end

    function preview = modelPreviewState()
        path = string(state.ModelSnapshotPath);
        available = strlength(strtrim(path)) > 0 && isExistingFile(path);
        updatedAt = "";
        if available
            fileInfo = dir(char(path));
            if ~isempty(fileInfo)
                updatedAt = string(datetime(fileInfo.datenum, "ConvertFrom", "datenum", "Format", "yyyy-MM-dd HH:mm:ss"));
            end
        end
        preview = struct( ...
            "available", available, ...
            "path", path, ...
            "updatedAt", updatedAt, ...
            "status", lastModelPreviewStatus, ...
            "focusItems", focusValues());
    end

    function assumptions = assumptionsState()
        spec = currentSpecStruct(state);
        if isempty(spec)
            assumptions = struct( ...
                "status", "waiting", ...
                "text", "Assumptions will appear after CiTT reads a circuit.", ...
                "summary", "No assumptions yet.");
            return
        end
        readiness = feval('citt.classifyBuildReadiness', spec);
        notes = specBuildNotes(spec);
        blocking = readiness.blocking_text;
        lines = strings(0, 1);
        if strlength(strtrim(notes)) > 0
            lines(end + 1) = notes;
        end
        if strlength(strtrim(blocking)) > 0
            lines(end + 1) = "Needs clarification" + newline + blocking;
        end
        if isempty(lines)
            text = "No extra assumptions were needed.";
        else
            text = strjoin(lines, sprintf("\n\n"));
        end
        if readiness.build_ready
            status = "Build-ready";
        else
            status = "Needs clarification";
        end
        assumptions = struct( ...
            "status", status, ...
            "text", text, ...
            "summary", getSpecText(spec, "circuit_type", "Circuit"));
    end

    function sources = appendSource(sources, label, pathValue)
        pathValue = string(pathValue);
        status = "missing";
        if strlength(strtrim(pathValue)) == 0
            status = "not set";
        elseif isExistingFile(pathValue) || exist(pathValue, "dir") == 7
            status = "available";
        end
        sources(end + 1, 1) = struct("label", string(label), "path", pathValue, "status", status);
    end

    function steps = workflowStepState()
        spec = currentSpecStruct(state);
        steps = repmat(struct("label", "", "status", "", "detail", ""), 0, 1);
        steps = appendWorkflowStep(steps, "Read", stepStatus(~isempty(spec), strlength(state.PromptText) > 0 || strlength(state.ImagePath) > 0), currentSpecPreview(state));
        steps = appendWorkflowStep(steps, "Prepare", stepStatus(agentTaskExists(state), ~isempty(spec)), state.AgentTaskPath);
        steps = appendWorkflowStep(steps, "Build", stepStatus(modelExists(state), agentTaskExists(state)), lastAgentStatus);
        steps = appendWorkflowStep(steps, "Check", stepStatus(~isempty(state.LastModelCheck), modelExists(state)), lastModelStatus);
        if ~isempty(state.TeachingPlan)
            totalTeachSteps = numel(state.TeachingPlan.steps);
            for i = 1:numel(state.TeachingPlan.steps)
                teachStep = state.TeachingPlan.steps(i);
                if i < state.TeachingStepIndex
                    status = "done";
                elseif i == state.TeachingStepIndex
                    status = "ready";
                else
                    status = "waiting";
                end
                label = "Teach " + string(i) + " / " + string(totalTeachSteps) + ": " + string(teachStep.title);
                detail = string(teachStep.focus_id) + " - " + string(teachStep.student_question);
                steps = appendWorkflowStep(steps, label, status, detail);
            end
        else
            steps = appendWorkflowStep(steps, "Teach", stepStatus(false, ~isempty(state.LastModelCheck)), lastTeachStatus);
        end
        steps = appendWorkflowStep(steps, "Probe", stepStatus(~isempty(state.LastProbe), modelExists(state)), lastProbeStatus);
        steps = appendWorkflowStep(steps, "Evidence", stepStatus(~isempty(state.LastEvidencePack), true), lastEvidenceStatus);
    end

    function steps = appendWorkflowStep(steps, label, status, detail)
        steps(end + 1, 1) = struct("label", string(label), "status", string(status), "detail", string(detail));
    end

    function status = stepStatus(done, available)
        if done
            status = "done";
        elseif available
            status = "ready";
        else
            status = "waiting";
        end
    end

    function env = environmentState()
        setup = state.LastSetupReport;
        env = struct( ...
            "status", compactStatus(state), ...
            "workDir", state.Config.WorkDir, ...
            "matlabVersion", fieldText(setup, "matlab_version"), ...
            "geminiModel", fieldText(setup, "gemini_model"), ...
            "agent", setupAgentText(setup), ...
            "setupText", setupOverviewText(setup));
    end

    function status = runStatusState()
        pending = ~isempty(state.AgentRun) && fieldText(state.AgentRun, "mode") == "external_agent_pending";
        active = busy || pending;
        text = pipelineMessage;
        if busy && strlength(strtrim(busyText)) > 0
            text = busyText;
        elseif pending
            text = "Building model with agent...";
        end
        status = struct( ...
            "active", active, ...
            "text", string(text), ...
            "progress", pipelineProgress, ...
            "detail", runDetailText(), ...
            "streamActive", pending, ...
            "stream", agentLiveText());
    end

    function text = agentLiveText()
        text = "";
        if isempty(state.AgentRun) || fieldText(state.AgentRun, "mode") ~= "external_agent_pending"
            return
        end
        stdoutTail = tailText(fieldText(state.AgentRun, "stdout"), 42);
        stderrTail = tailText(fieldText(state.AgentRun, "stderr"), 18);
        parts = strings(0, 1);
        parts(end + 1) = "Using " + emptyText(fieldText(state.AgentRun, "agent_name"), "agent");
        attemptText = fieldText(state.AgentRun, "agent_attempts");
        attemptNumber = str2double(char(attemptText));
        if ~isnan(attemptNumber) && attemptNumber > 0
            parts(end + 1) = "Attempt " + string(attemptNumber);
        else
            parts(end + 1) = "Starting first attempt";
        end
        if strlength(strtrim(stdoutTail)) > 0
            parts(end + 1) = "Latest stdout" + newline + stdoutTail;
        end
        if strlength(strtrim(stderrTail)) > 0
            parts(end + 1) = "Latest stderr" + newline + stderrTail;
        end
        if numel(parts) <= 2 && strlength(strtrim(stdoutTail + stderrTail)) == 0
            parts(end + 1) = "Waiting for CLI output...";
        end
        text = strjoin(parts, sprintf("\n\n"));
    end

    function text = runDetailText()
        pieces = strings(0, 1);
        if strlength(strtrim(lastInputStatus)) > 0
            pieces(end + 1) = "Read" + newline + lastInputStatus;
        end
        if strlength(strtrim(lastAgentOutput)) > 0
            pieces(end + 1) = "Build" + newline + lastAgentOutput;
        end
        if strlength(strtrim(lastModelOutput)) > 0
            pieces(end + 1) = "Model" + newline + lastModelOutput;
        end
        if hasTaskEvents(activeTaskId)
            pieces(end + 1) = "Timeline" + newline + taskTimelineText();
        end
        if isempty(pieces)
            text = "";
        else
            text = strjoin(pieces, sprintf("\n\n"));
        end
    end

    function settings = settingsState()
        settings = struct( ...
            "hasApiKey", strlength(string(getenv("GEMINI_API_KEY"))) > 0, ...
            "geminiApiKey", maskSecret(getenv("GEMINI_API_KEY")), ...
            "geminiModel", string(getenv("GEMINI_MODEL")), ...
            "parserBackend", state.Config.ParserBackend, ...
            "agentBackend", state.Config.AgentBackend, ...
            "agentCommand", string(getenv("CITT_AGENT_COMMAND")), ...
            "agentMaxAttempts", string(getenv("CITT_AGENT_MAX_ATTEMPTS")), ...
            "agentRetryDelaySeconds", string(getenv("CITT_AGENT_RETRY_DELAY_SECONDS")), ...
            "settingsPath", state.Config.SettingsPath);
        if strlength(settings.geminiModel) == 0
            settings.geminiModel = state.Config.GeminiModel;
        end
        if strlength(settings.agentMaxAttempts) == 0
            settings.agentMaxAttempts = string(state.Config.AgentMaxAttempts);
        end
        if strlength(settings.agentRetryDelaySeconds) == 0
            settings.agentRetryDelaySeconds = string(state.Config.AgentRetryDelaySeconds);
        end
    end

    function text = inputThreadText()
        parts = strings(0, 1);
        if strlength(strtrim(state.PromptText)) > 0
            parts(end + 1) = string(state.PromptText);
        end
        if strlength(strtrim(state.ImagePath)) > 0
            parts(end + 1) = "Attached image: " + fileNameOnly(state.ImagePath);
        end
        if isempty(parts)
            text = "No input yet.";
        else
            text = strjoin(parts, sprintf("\n\n"));
        end
    end

    function text = readSummaryLine()
        spec = currentSpecStruct(state);
        if isempty(spec)
            text = emptyText(lastInputStatus, "I have not read the circuit yet.");
            return
        end
        circuitType = getSpecText(spec, "circuit_type", "the circuit");
        outputs = emptyText(joinValue(getSpecValue(spec, "requested_outputs")), "the requested outputs");
        readiness = feval('citt.classifyBuildReadiness', spec);
        if readiness.build_ready
            suffix = "It is ready to build.";
        else
            suffix = "It needs clarification before building.";
        end
        text = "I read this as " + circuitType + ". Target: " + outputs + ". " + suffix;
    end

    function text = readDetailText()
        text = strjoin([
            emptyText(lastInputStatus, "Circuit read details.")
            ""
            currentSpecPreview(state)
            ""
            readinessSummaryText(state)
        ], newline);
    end

    function text = buildSummaryLine()
        pending = ~isempty(state.AgentRun) && fieldText(state.AgentRun, "mode") == "external_agent_pending";
        if pending
            text = "Building the Simscape model with the configured agent. This can take a few minutes.";
        elseif modelExists(state)
            text = "The Simscape model is available. I tried to open it in Simulink.";
        elseif agentTaskExists(state)
            text = "The build brief is ready. Run will hand it to the model-building agent.";
        elseif strlength(strtrim(lastAgentStatus)) > 0
            text = lastAgentStatus;
        else
            text = "Model build has not started.";
        end
    end

    function text = teachSummaryLine()
        if ~isempty(state.TeachingPlan)
            text = "Teaching is ready with a focus-linked prompt.";
        else
            text = lastTeachStatus;
        end
    end

    function text = probeSummaryLine()
        if ~isempty(state.LastLabDelta)
            text = "Lab delta comparison is ready.";
        elseif ~isempty(state.LastProbe)
            text = "Probe results are ready.";
        else
            text = lastProbeStatus;
        end
    end

    function text = evidenceSummaryLine()
        if ~isempty(state.LastEvidencePack)
            text = "Evidence pack is ready.";
        else
            text = lastEvidenceStatus;
        end
    end

    function text = buildThreadText()
        text = strjoin([
            "Agent"
            lastAgentStatus
            emptyText(lastAgentOutput, "No build log yet.")
            ""
            "Model"
            lastModelStatus
            emptyText(lastModelOutput, "No model output yet.")
        ], newline);
    end

    function text = teachThreadText()
        text = strjoin([
            currentStepText()
            ""
            "Status: " + lastTeachStatus
            emptyText(lastTeachOutput, "Teaching output will appear here.")
        ], newline);
    end

    function text = probeThreadText()
        text = strjoin([
            "Probe"
            lastProbeStatus
            emptyText(lastProbeOutput, "Probe output will appear here.")
            ""
            "Lab delta"
            lastDeltaStatus
            emptyText(lastDeltaOutput, "Lab delta output will appear here.")
        ], newline);
    end

    function text = evidenceThreadText()
        text = strjoin([
            "Verification"
            lastVerificationStatus
            emptyText(lastVerificationOutput, "Proof reports will appear here.")
            ""
            "Assessment"
            lastAssessmentStatus
            emptyText(lastAssessmentOutput, "Learning reports will appear here.")
            ""
            "Evidence pack"
            lastEvidenceStatus
            emptyText(lastEvidenceOutput, "Evidence pack output will appear here.")
        ], newline);
    end

    function text = taskTimelineText()
        index = findTaskIndex(activeTaskId);
        if index == 0 || isempty(taskHistory(index).events)
            text = "No recorded actions yet.";
            return
        end
        events = normalizeEvents(taskHistory(index).events);
        startIndex = max(1, numel(events) - 20 + 1);
        lines = strings(numel(events) - startIndex + 1, 1);
        cursor = 1;
        for i = startIndex:numel(events)
            lines(cursor) = events(i).time + "  " + events(i).status + "  " + events(i).action + newline + "  " + events(i).summary;
            cursor = cursor + 1;
        end
        text = strjoin(lines, sprintf("\n\n"));
    end

    function tf = shouldRecordAction(action)
        ignored = ["ready", "navigate", "sync", "new_task", "select_task", "save_settings", "run_pipeline"];
        tf = ~any(string(action) == ignored);
    end

    function text = taskEventSummary(action)
        text = "Running " + actionLabel(action) + ".";
    end

    function label = actionLabel(action)
        action = string(action);
        switch action
            case "select_image"
                label = "Select image";
            case "drop_image"
                label = "Drop image";
            case "read"
                label = "Read Circuit";
            case "run_pipeline"
                label = "Run workflow";
            case "prepare_build"
                label = "Prepare model";
            case "build_model"
                label = "Build model";
            case "refresh_model_snapshot"
                label = "Refresh preview";
            case "check_model"
                label = "Check model";
            case "run_simulation"
                label = "Run simulation";
            case "start_teaching"
                label = "Start teaching";
            case "next_hint"
                label = "Next hint";
            case "analyze_lab_error"
                label = "Analyze lab error";
            case "export_evidence"
                label = "Export evidence";
            otherwise
                label = replace(action, "_", " ");
        end
    end

    function title = taskTitleFromState()
        spec = currentSpecStruct(state);
        if ~isempty(spec)
            title = getSpecText(spec, "circuit_type", "Circuit task");
            return
        end
        prompt = strtrim(string(state.PromptText));
        if strlength(prompt) > 0
            lines = splitlines(prompt);
            title = extractBefore(lines(1) + "                                                    ", 44);
            title = strtrim(title);
            return
        end
        title = "New circuit task";
    end

    function summary = taskSummaryFromState(reason)
        summary = pipelineMessage;
        if strlength(strtrim(summary)) == 0
            summary = "Last action: " + string(reason);
        end
    end

    function stage = taskStageFromState()
        if ~isempty(state.LastEvidencePack)
            stage = "evidence";
        elseif ~isempty(state.LastProbe) || ~isempty(state.LastLabDelta)
            stage = "probe";
        elseif ~isempty(state.TeachingPlan)
            stage = "teach";
        elseif modelExists(state)
            stage = "build";
        elseif agentTaskExists(state)
            stage = "prepare";
        else
            stage = "read";
        end
    end

    function value = taskField(task, fieldName, defaultValue)
        value = string(defaultValue);
        if isstruct(task) && isfield(task, fieldName)
            raw = task.(fieldName);
            if ~isempty(raw)
                value = string(raw);
            end
        end
    end

    function value = taskNumber(task, fieldName, defaultValue)
        value = defaultValue;
        if isstruct(task) && isfield(task, fieldName)
            try
                value = double(task.(fieldName));
            catch
                value = defaultValue;
            end
        end
    end

    function text = maskSecret(value)
        value = string(value);
        if strlength(value) == 0
            text = "";
            return
        end
        if strlength(value) <= 8
            text = "********";
        else
            text = extractBefore(value, 5) + "..." + extractAfter(value, strlength(value) - 4);
        end
    end

    function text = sanitizeUserError(message)
        text = string(message);
        text = regexprep(text, "key=[^""'\s&]+", "key=***");
        text = regexprep(text, "(GEMINI_API_KEY=)[^""'\s]+", "$1***");
        if contains(lower(text), "tls connect error") || contains(lower(text), "secure connection")
            text = text + newline + newline + ...
                "This is a network/TLS handshake failure before Gemini returned a response. Try again once, then check VPN/proxy/certificates if it repeats.";
        end
    end

    function id = makeTaskId()
        id = "task_" + string(posixtime(datetime("now"))) + "_" + string(randi(99999));
        id = replace(id, ".", "_");
    end

    function text = nowText()
        text = string(datetime("now", "Format", "yyyy-MM-dd HH:mm:ss"));
    end

    function writeJson(path, value)
        folder = fileparts(char(path));
        if exist(folder, "dir") ~= 7
            mkdir(folder);
        end
        fid = fopen(char(path), "w");
        if fid < 0
            error("CiTT:WriteJsonFailed", "Could not write JSON: %s", path);
        end
        cleanup = onCleanup(@() fclose(fid));
        fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
    end

    function [label, action, destination] = nextActionForState(currentState)
        spec = currentSpecStruct(currentState);
        hasInput = strlength(strtrim(currentState.ImagePath)) > 0 || ...
            strlength(strtrim(currentState.PromptText)) > 0;
        if isempty(spec) && ~hasInput && exist(currentState.SpecPath, "file") ~= 2
            label = "Add Input";
            action = "select";
            destination = "read";
            return
        end
        if isempty(spec) && exist(currentState.SpecPath, "file") ~= 2
            label = "Read Circuit";
            action = "read";
            destination = "read";
            return
        end
        if ~isempty(spec)
            readiness = feval('citt.classifyBuildReadiness', spec);
            if ~readiness.build_ready
                label = "Clarify Read";
                action = "select";
                destination = "read";
                return
            end
        end
        if ~agentTaskExists(currentState)
            label = "Prepare Model";
            action = "prepare_build";
            destination = "build";
            return
        end
        if ~modelExists(currentState)
            label = "Build Model";
            action = "build_model";
            destination = "build";
            return
        end
        if isempty(currentState.LastModelCheck)
            label = "Check Model";
            action = "check_model";
            destination = "build";
            return
        end
        if isempty(currentState.TeachingPlan)
            label = "Start Teaching";
            action = "start_teaching";
            destination = "teach";
            return
        end
        if isempty(currentState.LastProbe)
            label = "Probe Model";
            action = "select";
            destination = "probe";
            return
        end
        if isempty(currentState.LastLabDelta)
            label = "Explain Delta";
            action = "select";
            destination = "probe";
            return
        end
        label = "Export Pack";
        action = "export_evidence";
        destination = "evidence";
    end

    function setup = setupState(report)
        if isempty(report)
            setup = struct("gemini", "not checked", "satk", "not checked", "mcp", "not checked", ...
                "simscape", "not checked", "agent", "not checked");
            return
        end
        setup = struct();
        setup.gemini = "Parser: " + parserStatusText(report);
        setup.satk = "SATK: " + readyNeeds(report.satk_initialize_available);
        setup.mcp = "MCP: " + readyNeeds(report.matlab_mcp_available);
        setup.simscape = "Simscape: " + readyNeeds(report.simscape_available);
        setup.agent = "Agent: " + setupAgentText(report);
    end

    function steps = buildStepsState(currentState)
        spec = currentSpecStruct(currentState);
        steps = repmat(struct("label", "", "status", "", "tone", "muted"), 1, 5);
        if isempty(spec)
            steps(1) = struct("label", "Circuit Read", "status", "Waiting", "tone", "muted");
        else
            steps(1) = struct("label", "Circuit Read", "status", "Ready", "tone", "good");
        end
        if agentTaskExists(currentState)
            steps(2) = struct("label", "Build Brief", "status", "Ready", "tone", "good");
        else
            steps(2) = struct("label", "Build Brief", "status", "Prepare", "tone", "active");
        end
        if ~isempty(currentState.AgentRun)
            mode = fieldText(currentState.AgentRun, "mode");
            if mode == "external_agent_pending"
                steps(3) = struct("label", "Builder", "status", "Running", "tone", "active");
            elseif isTruthy(fieldText(currentState.AgentRun, "success"))
                steps(3) = struct("label", "Builder", "status", "Complete", "tone", "good");
            elseif mode == "manual_agent"
                steps(3) = struct("label", "Builder", "status", "Manual", "tone", "warn");
            else
                steps(3) = struct("label", "Builder", "status", "Attention", "tone", "bad");
            end
        else
            steps(3) = struct("label", "Builder", "status", "Not started", "tone", "muted");
        end
        if modelExists(currentState)
            steps(4) = struct("label", "Model", "status", "Available", "tone", "good");
        else
            steps(4) = struct("label", "Model", "status", "Waiting", "tone", "muted");
        end
        if ~isempty(currentState.LastModelCheck)
            steps(5) = struct("label", "Check", "status", "Complete", "tone", "good");
        elseif modelExists(currentState)
            steps(5) = struct("label", "Check", "status", "Ready", "tone", "active");
        else
            steps(5) = struct("label", "Check", "status", "Waiting", "tone", "muted");
        end
    end

    function tf = agentTaskExists(currentState)
        tf = strlength(currentState.AgentTaskPath) > 0 && exist(currentState.AgentTaskPath, "file") == 2;
    end

    function tf = modelExists(currentState)
        tf = strlength(currentState.ModelPath) > 0 && isExistingFile(currentState.ModelPath);
    end

    function spec = currentSpecStruct(currentState)
        spec = [];
        if ~isempty(currentState.Spec)
            spec = currentState.Spec;
            return
        end
        if strlength(currentState.SpecPath) > 0 && exist(currentState.SpecPath, "file") == 2
            try
                spec = jsondecode(fileread(currentState.SpecPath));
            catch
                spec = [];
            end
        end
    end

    function text = parseNextStepText(parsed)
        spec = parsed.spec;
        blockingIssues = specBlockingIssues(spec);
        notes = specBuildNotes(spec);
        if strlength(blockingIssues) > 0
            text = strjoin([
                "Circuit read, but it is not build-ready yet."
                "Clarify unclear or unsupported regions before model generation."
                ""
                blockingIssues
                ""
                "Spec saved at: " + parsed.spec_path
            ], newline);
        else
            text = strjoin([
                "Circuit read successfully."
                emptyText(notes, "Symbolic or omitted values will be kept as model parameters.")
                "Next: Prepare Model."
                "Spec saved at: " + parsed.spec_path
            ], newline);
        end
    end

    function text = currentSpecPreview(currentState)
        spec = currentSpecStruct(currentState);
        if ~isempty(spec)
            text = specSummary(spec);
            return
        end
        text = strjoin([
            "No circuit spec yet."
            "Drop or browse for an image, then click Read Circuit."
        ], newline);
    end

    function text = readinessSummaryText(currentState)
        spec = currentSpecStruct(currentState);
        if isempty(spec)
            text = strjoin([
                "Build readiness: not started"
                "Blocking issues: none yet"
                "Modeling assumptions: none yet"
            ], newline);
            return
        end
        readiness = feval('citt.classifyBuildReadiness', spec);
        notes = specBuildNotes(spec);
        if readiness.build_ready && strlength(strtrim(notes)) > 0
            badge = "parameterized";
        elseif readiness.build_ready
            badge = "ready";
        else
            badge = "needs clarification";
        end
        text = strjoin([
            "Build readiness: " + badge
            ""
            "Blocking issues"
            emptyListText(readiness.blocking_text)
            ""
            "Modeling assumptions"
            emptyListText(notes)
        ], newline);
    end

    function text = readAdvancedText(currentState)
        spec = currentSpecStruct(currentState);
        if isempty(spec)
            specDetails = strjoin([
                "Suggested Simscape blocks"
                "- none yet"
                ""
                "Assumptions"
                "- none yet"
            ], newline);
        else
            specDetails = strjoin([
                "Suggested Simscape blocks"
                listValue(getSpecValue(spec, "suggested_simscape_blocks"))
                ""
                "Assumptions"
                listValue(getSpecValue(spec, "assumptions"))
            ], newline);
        end
        text = strjoin([
            "Raw JSON is available through Open Spec."
            "Image: " + emptyText(currentState.ImagePath, "not selected")
            "Spec file: " + currentState.SpecPath
            ""
            specDetails
            ""
            "Prompt"
            emptyText(currentState.PromptText, "none")
        ], newline);
    end

    function text = teachingStepsText(currentState)
        if isempty(currentState.TeachingPlan)
            text = strjoin([
                "1. Identify command input"
                "2. Trace feedback path"
                "3. Explain output measurement"
                "4. Check modeling assumption"
                "5. Interpret simulation result"
            ], newline);
            return
        end
        steps = currentState.TeachingPlan.steps;
        totalSteps = numel(steps);
        lines = strings(numel(steps), 1);
        for i = 1:numel(steps)
            marker = "Step " + string(i) + " / " + string(totalSteps) + ": ";
            if i == currentState.TeachingStepIndex
                marker = "Current " + string(i) + " / " + string(totalSteps) + ": ";
            end
            lines(i) = marker + string(steps(i).title) + newline + "   focus: " + string(steps(i).focus_id);
        end
        text = strjoin(lines, newline);
    end

    function text = currentStepText()
        if isempty(state.TeachingPlan)
            text = "No teaching plan yet.";
            return
        end
        step = state.TeachingPlan.steps(state.TeachingStepIndex);
        totalSteps = numel(state.TeachingPlan.steps);
        text = strjoin([
            "Step " + string(state.TeachingStepIndex) + " / " + string(totalSteps) + ": " + string(step.title)
            ""
            "Question:"
            string(step.student_question)
            ""
            "Focus: " + string(step.focus_id)
            "Concept: " + string(step.concept)
        ], newline);
    end

    function text = currentStepQuestion()
        if isempty(state.TeachingPlan)
            text = "Start Teaching will generate a focus-linked Socratic prompt.";
            return
        end
        step = state.TeachingPlan.steps(state.TeachingStepIndex);
        text = string(step.student_question);
    end

    function values = focusValues()
        values = strings(0, 1);
        if ~isempty(state.TeachingPlan)
            for i = 1:numel(state.TeachingPlan.steps)
                values(end + 1) = string(state.TeachingPlan.steps(i).focus_id); %#ok<AGROW>
            end
        elseif exist(state.FocusMapPath, "file") == 2
            try
                data = jsondecode(fileread(state.FocusMapPath));
                items = data;
                if isfield(data, "focus_map")
                    items = data.focus_map;
                end
                for i = 1:numel(items)
                    if isfield(items(i), "focus_id")
                        values(end + 1) = string(items(i).focus_id); %#ok<AGROW>
                    elseif isfield(items(i), "id")
                        values(end + 1) = string(items(i).id); %#ok<AGROW>
                    end
                end
            catch
            end
        end
        values = unique(values);
    end

    function values = probeValues()
        values = strings(0, 1);
        if exist(state.ProbeMapPath, "file") ~= 2
            return
        end
        try
            data = jsondecode(fileread(state.ProbeMapPath));
            items = data;
            if isfield(data, "probe_map")
                items = data.probe_map;
            elseif isfield(data, "items")
                items = data.items;
            end
            for i = 1:numel(items)
                if isfield(items(i), "probe_id")
                    values(end + 1) = string(items(i).probe_id); %#ok<AGROW>
                elseif isfield(items(i), "id")
                    values(end + 1) = string(items(i).id); %#ok<AGROW>
                elseif isfield(items(i), "focus_id")
                    values(end + 1) = string(items(i).focus_id); %#ok<AGROW>
                end
            end
        catch
        end
        values = unique(values);
    end

    function values = explainabilityValues()
        values = strings(0, 1);
        if ~isempty(state.LastExplainability) && isfield(state.LastExplainability, "actions")
            actions = state.LastExplainability.actions;
        elseif exist(state.Config.ExplainabilityMapPath, "file") == 2
            try
                data = jsondecode(fileread(state.Config.ExplainabilityMapPath));
                actions = data.actions;
            catch
                actions = struct([]);
            end
        else
            actions = struct([]);
        end
        for i = 1:numel(actions)
            if isfield(actions(i), "action_id")
                values(end + 1) = string(actions(i).action_id); %#ok<AGROW>
            end
        end
        values = unique(values);
    end

    function value = firstOrEmpty(values)
        if isempty(values)
            value = "";
        else
            value = string(values(1));
        end
    end

    function validateTeachingImage()
        imagePath = strtrim(string(fieldText(state, "TeachingImagePath")));
        if strlength(imagePath) > 0 && exist(imagePath, "file") ~= 2
            error("CiTT:TeachingImageMissing", "Teaching image not found: %s", imagePath);
        end
    end

    function answer = teachingSubmissionText()
        answer = fieldText(state, "StudentAnswer");
        imagePath = strtrim(string(fieldText(state, "TeachingImagePath")));
        if strlength(imagePath) > 0
            answer = strjoin([
                string(answer)
                ""
                "[Student attached image]"
                imagePath
            ], newline);
        end
    end

    function text = evidenceContentsText(currentState)
        if ~isempty(currentState.LastEvidencePack)
            text = strjoin([
                "Last exported evidence pack"
                "Pack: " + fieldText(currentState.LastEvidencePack, "pack_path")
            ], newline);
            return
        end
        text = strjoin([
            "This pack collects:"
            "- circuit image and parsed spec"
            "- generated Simscape model path"
            "- model check and simulation status"
            "- requirement pass/fail table"
            "- sweep, fault, and explainability reports"
            "- learning assessment"
            "- risk/scope guardrail"
            "- economics plan"
        ], newline);
    end

    function text = inputStatusText(currentState)
        setup = currentState.LastSetupReport;
        text = strjoin([
            "Image: " + emptyText(currentState.ImagePath, "drop or browse for a circuit image")
            "Parser: " + parserStatusText(setup)
            "SATK: " + readyNeeds(setup.satk_initialize_available) + " | MCP: " + readyNeeds(setup.matlab_mcp_available) + " | Simscape: " + readyNeeds(setup.simscape_available)
            "Spec file: " + currentState.SpecPath
        ], newline);
    end

    function text = setupOverviewText(setup)
        if isempty(setup)
            text = "Setup has not been checked.";
            return
        end
        text = strjoin([
            "Ready checks"
            ""
            "Circuit parser: " + parserStatusText(setup)
            "Gemini API: " + readyNeeds(setup.gemini_key_found)
            "Gemini model: " + setup.gemini_model
            "Simulink Agentic Toolkit: " + readyNeeds(setup.satk_initialize_available)
            "MATLAB MCP Server: " + readyNeeds(setup.matlab_mcp_available)
            "Simscape: " + readyNeeds(setup.simscape_available)
            "Agent CLI: " + setupAgentText(setup)
            ""
            "Paths"
            "Work folder: " + setup.work_dir
            "SATK: " + setup.satk_install_path
            "MCP: " + setup.matlab_mcp_server_path
            ""
            "Setup details"
            setup.guidance(:)
        ], newline);
    end

    function text = pathStatusText(currentState)
        text = strjoin([
            "Current model path: " + currentState.ModelPath
            "Last agent task file: " + currentState.AgentTaskPath
            "Last parsed circuit spec: " + currentState.SpecPath
            "Focus map: " + currentState.FocusMapPath
            "Probe map: " + currentState.ProbeMapPath
            "Bode report: " + currentState.Config.BodeMarkdownPath
            "Evidence pack: " + currentState.EvidencePackPath
        ], newline);
    end

    function text = verificationReportText(currentState)
        text = strjoin([
            "Folder: " + currentState.Config.WorkDir
            "Requirements: " + fileNameOnly(currentState.Config.RequirementReportMarkdownPath)
            "Sweep: " + fileNameOnly(currentState.Config.ParameterSweepMarkdownPath)
            "Faults: " + fileNameOnly(currentState.Config.FaultInjectionMarkdownPath)
            "Explainability: " + fileNameOnly(currentState.Config.ExplainabilityMarkdownPath)
        ], newline);
    end

    function text = assessmentReportText(currentState)
        text = strjoin([
            "Folder: " + currentState.Config.WorkDir
            "Assessment: " + fileNameOnly(currentState.Config.AssessmentMarkdownPath)
            "Cost: " + fileNameOnly(currentState.Config.EconomicsMarkdownPath)
            "Scope: " + fileNameOnly(currentState.Config.ScopeGuardrailMarkdownPath)
        ], newline);
    end

    function text = compactStatus(currentState)
        setup = currentState.LastSetupReport;
        if isempty(setup)
            text = "Setup not checked";
            return
        end
        issues = strings(0, 1);
        if ~parserReady(setup)
            issues(end + 1) = "Parser needs setup";
        end
        if ~logical(setup.satk_initialize_available)
            issues(end + 1) = "SATK needs setup";
        end
        if ~logical(setup.simscape_available)
            issues(end + 1) = "Simscape needs setup";
        end
        if startsWith(setupAgentText(setup), "needs")
            issues(end + 1) = "Agent CLI needs setup";
        end
        if isempty(issues)
            text = "Local workspace";
        else
            text = strjoin(issues, " | ");
        end
    end

    function text = setupAgentText(setup)
        if isfield(setup, "configured_agent_command") && strlength(strtrim(setup.configured_agent_command)) > 0
            text = "ready: CITT_AGENT_COMMAND";
            return
        end
        backend = agentBackendText(setup);
        if isfield(setup, "agent_clis")
            for i = 1:numel(setup.agent_clis)
                if setup.agent_clis(i).name == backend && isfield(setup.agent_clis(i), "available") && setup.agent_clis(i).available
                    text = backend + ": ready";
                    return
                end
            end
        end
        text = backend + ": needs CLI";
    end

    function backend = agentBackendText(setup)
        backend = "codex";
        if isfield(setup, "agent_backend") && strlength(strtrim(setup.agent_backend)) > 0
            backend = lower(strtrim(string(setup.agent_backend)));
        end
    end

    function ready = parserReady(setup)
        ready = false;
        if isfield(setup, "parser_available")
            ready = logical(setup.parser_available);
            return
        end
        backend = parserBackendText(setup);
        switch backend
            case "codex"
                ready = isfield(setup, "codex_parser_cli_path") && strlength(strtrim(setup.codex_parser_cli_path)) > 0;
            case "gemini"
                ready = isfield(setup, "gemini_key_found") && logical(setup.gemini_key_found);
            case "local"
                ready = true;
        end
    end

    function text = parserStatusText(setup)
        backend = parserBackendText(setup);
        if parserReady(setup)
            switch backend
                case "codex"
                    text = "codex: ready";
                case "gemini"
                    text = "gemini: ready";
                case "local"
                    text = "local: ready";
                otherwise
                    text = backend + ": ready";
            end
            return
        end
        switch backend
            case "codex"
                text = "codex: needs Codex CLI";
            case "gemini"
                text = "gemini: needs GEMINI_API_KEY";
            case "local"
                text = "local: unavailable";
            otherwise
                text = backend + ": unsupported";
        end
    end

    function backend = parserBackendText(setup)
        backend = "codex";
        if isfield(setup, "parser_backend") && strlength(strtrim(setup.parser_backend)) > 0
            backend = lower(strtrim(string(setup.parser_backend)));
        end
    end

    function text = readyNeeds(value)
        if logical(value)
            text = "ready";
        else
            text = "needs setup";
        end
    end

    function text = specSummary(spec)
        circuitType = getSpecText(spec, "circuit_type", "unknown circuit");
        nodes = getSpecValue(spec, "nodes");
        components = getSpecValue(spec, "components");
        outputs = getSpecValue(spec, "requested_outputs");
        analysis = getSpecText(spec, "likely_analysis", "not specified");
        blockingIssues = specBlockingIssues(spec);
        notes = specBuildNotes(spec);
        if strlength(blockingIssues) > 0
            readiness = "needs clarification";
            nextText = "Clarify prompt";
        elseif strlength(strtrim(notes)) > 0
            readiness = "parameterized";
            nextText = "Prepare Model";
        else
            readiness = "ready";
            nextText = "Prepare Model";
        end
        text = strjoin([
            "Circuit: " + circuitType
            "Readiness: " + readiness
            "Requested output: " + emptyText(joinValue(outputs), "not specified")
            "Likely analysis: " + analysis
            "Components: " + string(countItems(components))
            "Nodes: " + emptyText(joinValue(nodes), "not specified")
            "Next action: " + nextText
        ], newline);
    end

    function issues = specBlockingIssues(spec)
        readiness = feval('citt.classifyBuildReadiness', spec);
        issues = readiness.blocking_text;
    end

    function notes = specBuildNotes(spec)
        parts = strings(0, 1);
        if isstruct(spec) && isfield(spec, "ambiguities")
            text = joinValue(spec.ambiguities);
            if strlength(strtrim(text)) > 0
                parts(end + 1) = "Ambiguity note: " + text;
            end
        end
        readiness = feval('citt.classifyBuildReadiness', spec);
        if strlength(strtrim(readiness.nonblocking_text)) > 0
            parts(end + 1) = readiness.nonblocking_text;
        end
        notes = strjoin(parts, newline);
    end

    function value = getSpecValue(spec, fieldName)
        if isstruct(spec) && isfield(spec, fieldName)
            value = spec.(fieldName);
        else
            value = [];
        end
    end

    function text = getSpecText(spec, fieldName, defaultText)
        value = getSpecValue(spec, fieldName);
        if isempty(value)
            text = string(defaultText);
        else
            text = joinValue(value);
        end
    end

    function count = countItems(value)
        if isempty(value)
            count = 0;
        elseif isstruct(value) || iscell(value) || isstring(value)
            count = numel(value);
        elseif ischar(value)
            count = 1;
        else
            count = numel(value);
        end
    end

    function text = listValue(value)
        joined = joinValue(value);
        if strlength(joined) == 0
            text = "none";
            return
        end
        pieces = split(joined, ", ");
        text = strjoin("- " + pieces(:), newline);
    end

    function text = joinValue(value)
        if isempty(value)
            text = "";
        elseif isstring(value)
            text = strjoin(value(:)', ", ");
        elseif ischar(value)
            text = string(value);
        elseif iscell(value)
            parts = strings(numel(value), 1);
            for i = 1:numel(value)
                parts(i) = joinValue(value{i});
            end
            text = strjoin(parts(:)', ", ");
        elseif isstruct(value)
            parts = strings(numel(value), 1);
            for i = 1:numel(value)
                if isfield(value(i), "label")
                    parts(i) = string(value(i).label);
                elseif isfield(value(i), "id")
                    parts(i) = string(value(i).id);
                elseif isfield(value(i), "type")
                    parts(i) = string(value(i).type);
                else
                    parts(i) = string(feval('citt.util.jsonEncode', value(i)));
                end
            end
            text = strjoin(parts(:)', ", ");
        elseif isnumeric(value) || islogical(value)
            text = string(mat2str(value));
        else
            text = string(value);
        end
    end

    function text = emptyListText(value)
        value = string(value);
        if strlength(strtrim(value)) == 0
            text = "- none";
            return
        end
        lines = splitlines(value);
        lines = lines(strlength(strtrim(lines)) > 0);
        if isempty(lines)
            text = "- none";
        else
            text = strjoin("- " + lines(:), newline);
        end
    end

    function text = emptyText(value, fallback)
        value = scalarText(value);
        if strlength(strtrim(value)) == 0
            text = string(fallback);
        else
            text = value;
        end
    end

    function text = fieldText(data, fieldName)
        text = "";
        if isstruct(data) && isfield(data, fieldName)
            value = data.(fieldName);
            if isstring(value) || ischar(value)
                text = scalarText(value);
            elseif isnumeric(value) || islogical(value)
                text = scalarText(value);
            else
                try
                    text = scalarText(value);
                catch
                    text = "";
                end
            end
        end
    end

    function tf = isTruthy(value)
        text = lower(strtrim(scalarText(value)));
        tf = any(text == ["true", "1", "yes"]);
    end

    function text = scalarText(value)
        try
            values = string(value);
        catch
            text = "";
            return
        end
        values = values(:);
        if isempty(values)
            text = "";
        else
            text = values(1);
        end
    end

    function text = payloadText(payload, fieldName, defaultText)
        text = string(defaultText);
        if isstruct(payload) && isfield(payload, fieldName)
            text = string(payload.(fieldName));
        end
    end

    function value = payloadNumber(payload, fieldName, defaultValue)
        value = defaultValue;
        if isstruct(payload) && isfield(payload, fieldName)
            try
                value = double(payload.(fieldName));
            catch
                value = defaultValue;
            end
        end
    end

    function name = fileNameOnly(pathValue)
        [~, namePart, ext] = fileparts(char(pathValue));
        name = string(namePart) + string(ext);
    end

    function text = focusActionSummary(actionName, result)
        successText = fieldText(result, "success");
        if strlength(successText) == 0
            successText = "done";
        end
        messageText = fieldText(result, "message");
        if strlength(messageText) == 0
            messageText = fieldText(result, "focus_id");
        end
        text = strjoin([
            actionName + " complete."
            "Status: " + successText
            "Message: " + emptyText(messageText, "model focus updated")
            ""
            "Ask the student to explain what changed in the highlighted model region."
        ], newline);
    end

    function text = probePlanSummary(result)
        text = strjoin([
            "Probe placed or highlighted."
            "Probe: " + emptyText(fieldText(result, "target_id"), "selected focus")
            "Model: " + emptyText(fieldText(result, "model_path"), "current model")
            ""
            "What this probe tells us"
            emptyListText(joinValue(result.instructions))
            ""
            "Automated model actions"
            emptyListText(joinValue(result.automated_actions))
            ""
            "Warnings"
            emptyListText(joinValue(result.warnings))
        ], newline);
    end

    function text = agentRunSummary(runResult)
        mode = fieldText(runResult, "mode");
        if mode == "external_agent_pending"
            headline = "External SATK agent is running.";
        elseif mode == "manual_agent"
            headline = "External SATK agent not launched.";
        elseif mode == "local_fallback"
            headline = "Agent build unavailable. Running local Simscape builder.";
        elseif isTruthy(fieldText(runResult, "success"))
            headline = "External SATK agent build complete.";
        else
            headline = "External SATK agent build incomplete.";
        end
        text = strjoin([
            headline
            "Mode: " + emptyText(mode, "unknown")
            "Agent: " + emptyText(fieldText(runResult, "agent_name"), "unknown")
            "Model: " + emptyText(fieldText(runResult, "produced_model_path"), "not found")
            "Focus map: " + emptyText(fieldText(runResult, "produced_focus_map_path"), "not found")
            "Probe map: " + emptyText(fieldText(runResult, "produced_probe_map_path"), "not found")
            "Report: " + emptyText(fieldText(runResult, "agent_report_path"), "not written")
            "Exit status: " + emptyText(fieldText(runResult, "exit_status"), "running")
            ""
            "Command"
            emptyText(fieldText(runResult, "command"), "not recorded")
        ], newline);
        stdoutTail = tailText(fieldText(runResult, "stdout"), 30);
        if strlength(strtrim(stdoutTail)) > 0
            text = text + newline + newline + "Agent output (last 30 lines)" + newline + stdoutTail;
        end
    end

    function text = modelCheckSummary(checked)
        text = strjoin([
            "Model check complete."
            "Model: " + checked.model_path
            "Report: " + checked.report_path
            ""
            "Messages"
            listValue(checked.messages)
        ], newline);
    end

    function text = simulationSummary(simulated)
        text = strjoin([
            "Simulation complete."
            "Model: " + simulated.model_path
            "Summary: " + simulated.summary_path
            ""
            "Messages"
            listValue(simulated.messages)
            ""
            "Output variables"
            listValue(simulated.output_variables)
        ], newline);
    end

    function text = bodeSummary(report)
        text = strjoin([
            "Bode analysis complete."
            "JSON: " + fieldText(report, "report_path")
            "Markdown: " + fieldText(report, "markdown_path")
            "Plot: " + emptyText(fieldText(report, "plot_path"), "not generated")
            ""
            "Curves"
            reportRowsText(report.curves, ["label", "source", "input", "output", "cutoff_frequency_hz"], 10)
            ""
            "Messages"
            listValue(report.messages)
            ""
            "Next action"
            fieldText(report, "next_action")
        ], newline);
    end

    function text = labErrorSummary(report)
        text = strjoin([
            "Lab error analysis complete."
            "CSV: " + fieldText(report, "csv_path")
            "JSON: " + fieldText(report, "report_path")
            "Markdown: " + fieldText(report, "markdown_report_path")
            ""
            "Rows"
            reportRowsText(report.rows, ["quantity", "unit", "measured_value", "simulation_value", "percent_difference", "status", "probe_id"], 12)
            ""
            "Likely causes"
            reportRowsText(report.likely_causes, ["severity", "label", "evidence", "next_action"], 10)
            ""
            "Next actions"
            listValue(report.prioritized_next_actions)
        ], newline);
    end

    function text = requirementRunSummary(report)
        s = report.summary;
        text = strjoin([
            "Requirement check complete."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "PASS " + string(s.pass) + " | WARN " + string(s.warn) + " | FAIL " + string(s.fail)
            ""
            "Rows"
            reportRowsText(report.rows, ["requirement", "result", "status"], 14)
        ], newline);
    end

    function text = sweepSummary(report)
        text = strjoin([
            "Parameter sweep complete."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "Nominal cutoff: " + fieldText(report.summary, "nominal_cutoff_hz") + " Hz"
            "Worst range: " + fieldText(report.summary, "worst_case_cutoff_range_hz") + " Hz"
            "Most sensitive: " + report.summary.most_sensitive_parameter
        ], newline);
    end

    function text = faultSummary(report)
        text = strjoin([
            "Fault injection report ready."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "Fault scenarios: " + string(numel(report.rows))
            ""
            reportRowsText(report.rows, ["fault", "observed_effect", "status"], 10)
        ], newline);
    end

    function text = explainabilitySummary(report)
        text = strjoin([
            "Explainability map ready."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "Actions: " + string(numel(report.actions))
            ""
            reportRowsText(report.actions, ["action_id", "action_type", "label"], 14)
        ], newline);
    end

    function text = assessmentSummary(report)
        text = strjoin([
            "Assessment complete."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "Concept: " + report.concept
            "Before score: " + string(report.before.score)
            "After score: " + string(report.after.score)
            "Learning gain: " + string(report.learning_gain)
            "Final correctness: " + string(report.final_correctness)
            "Misconception: " + report.misconception_detected
        ], newline);
    end

    function text = economicsSummary(report)
        text = strjoin([
            "Economics plan ready."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "Students: " + string(report.deployment.students)
            "Estimated API cost: $" + sprintf("%.2f", report.total_estimated_api_cost_usd)
            "Optional hardware/team: $" + sprintf("%.2f", report.total_optional_hardware_per_team_usd)
        ], newline);
    end

    function text = scopeSummary(report)
        text = strjoin([
            "Scope guardrail ready."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "Category: " + report.potential_regulatory_category
            "Patient-connected trigger: " + string(report.patient_connected_trigger_detected)
            "Risk rows: " + string(numel(report.risks))
        ], newline);
    end

    function text = evidencePackSummary(exported)
        text = strjoin([
            "Evidence pack exported."
            "Pack: " + fieldText(exported, "pack_path")
            "Spec: " + state.SpecPath
            "Model: " + state.ModelPath
        ], newline);
    end

    function text = reportRowsText(rows, fieldNames, maxRows)
        if isempty(rows)
            text = "none";
            return
        end
        limit = min(numel(rows), maxRows);
        lines = strings(limit, 1);
        for i = 1:limit
            parts = strings(1, numel(fieldNames));
            for j = 1:numel(fieldNames)
                parts(j) = fieldText(rows(i), fieldNames(j));
            end
            lines(i) = "- " + strjoin(parts, " | ");
        end
        text = strjoin(lines, newline);
        if numel(rows) > limit
            text = text + newline + "- ... " + string(numel(rows) - limit) + " more";
        end
    end

    function text = tailText(value, maxLines)
        lines = splitlines(string(value));
        lines = lines(strlength(lines) > 0);
        if isempty(lines)
            text = "";
            return
        end
        startIndex = max(1, numel(lines) - maxLines + 1);
        text = strjoin(lines(startIndex:end), newline);
    end

    function savedPath = saveDroppedImage(data)
        name = payloadText(data, "name", "dropped_circuit.png");
        mimeType = payloadText(data, "mimeType", "image/png");
        dataUrl = payloadText(data, "dataUrl", "");
        if strlength(dataUrl) == 0
            error("CiTT:DropDataMissing", "Dropped image did not include data.");
        end
        rawDataUrl = char(dataUrl);
        commaIndex = strfind(rawDataUrl, ",");
        if isempty(commaIndex)
            error("CiTT:DropDataInvalid", "Dropped image data URL is invalid.");
        end
        base64Text = string(rawDataUrl(commaIndex(1) + 1:end));
        bytes = decodeBase64(base64Text);
        extension = imageExtension(name, mimeType);
        savedPath = string(tempname(char(state.Config.WorkDir))) + extension;
        fid = fopen(char(savedPath), "wb");
        if fid < 0
            error("CiTT:DropWriteFailed", "Could not write dropped image: %s", savedPath);
        end
        cleanup = onCleanup(@() fclose(fid));
        fwrite(fid, bytes, "uint8");
    end

    function bytes = decodeBase64(base64Text)
        try
            bytes = matlab.net.base64decode(char(base64Text));
        catch
            decoder = javaMethod('getDecoder', 'java.util.Base64');
            bytes = uint8(decoder.decode(char(base64Text)));
        end
    end

    function extension = imageExtension(name, mimeType)
        [~, ~, ext] = fileparts(char(name));
        extension = string(lower(ext));
        if strlength(extension) > 0
            return
        end
        switch lower(string(mimeType))
            case "image/jpeg"
                extension = ".jpg";
            case "image/png"
                extension = ".png";
            case "image/gif"
                extension = ".gif";
            case "image/webp"
                extension = ".webp";
            otherwise
                extension = ".png";
        end
    end

    function tf = isExistingFile(pathValue)
        code = exist(string(pathValue), "file");
        tf = code == 2 || code == 4;
    end
end
