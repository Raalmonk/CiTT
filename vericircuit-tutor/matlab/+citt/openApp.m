function app = openApp()
%OPENAPP Build the MATLAB-native CiTT plugin UI.

state = feval('citt.appState');
state.LastSetupReport = feval('citt.checkSetup');

app = struct();
app.Figure = uifigure( ...
    "Name", "CiTT Circuit Tutor", ...
    "Position", [80 80 1180 760]);
app.Figure.Color = [0.965 0.976 0.969];

main = uigridlayout(app.Figure, [2 1]);
main.RowHeight = {82, "1x"};
main.Padding = [18 14 18 16];
main.RowSpacing = 12;

handles = struct();

header = uigridlayout(main, [2 3]);
header.ColumnWidth = {"1x", 180, 250};
header.RowHeight = {36, 24};
header.Padding = [0 0 0 0];
header.RowSpacing = 6;
header.ColumnSpacing = 12;
header.Layout.Row = 1;

titleLabel = uilabel(header);
titleLabel.Text = "CiTT";
titleLabel.FontSize = 24;
titleLabel.FontWeight = "bold";
titleLabel.Tooltip = "Circuit insight, teaching, and Simscape model building inside MATLAB.";
titleLabel.Layout.Row = [1 2];
titleLabel.Layout.Column = 1;

statusLabel = uilabel(header);
statusLabel.HorizontalAlignment = "right";
statusLabel.FontSize = 13;
statusLabel.FontWeight = "bold";
statusLabel.Text = compactStatus(state);
statusLabel.Layout.Row = 1;
statusLabel.Layout.Column = [2 3];

pipelineLabel = uilabel(header);
pipelineLabel.HorizontalAlignment = "right";
pipelineLabel.FontSize = 12;
pipelineLabel.Text = "Ready for circuit input";
pipelineLabel.Layout.Row = 2;
pipelineLabel.Layout.Column = 2;

pipelineGauge = uigauge(header, "linear");
pipelineGauge.Limits = [0 100];
pipelineGauge.Value = 0;
pipelineGauge.Layout.Row = 2;
pipelineGauge.Layout.Column = 3;

tabs = uitabgroup(main);
tabs.Layout.Row = 2;

buildInputTab(tabs);
buildAgentTab(tabs);
buildModelTab(tabs);
buildTeachTab(tabs);
buildProbeTab(tabs);

app.Handles = handles;
app.State = state;
refreshAll();

    function buildInputTab(parent)
        tab = uitab(parent, "Title", "Read Circuit");
        grid = uigridlayout(tab, [8 4]);
        grid.RowHeight = {32, 170, 34, 92, 38, 70, 28, "1x"};
        grid.ColumnWidth = {110, "1x", 170, 170};
        grid.Padding = [18 16 18 16];
        grid.RowSpacing = 10;
        grid.ColumnSpacing = 10;

        heading = uilabel(grid, "Text", "Start with a circuit image or a short prompt");
        heading.FontSize = 17;
        heading.FontWeight = "bold";
        heading.Layout.Row = 1;
        heading.Layout.Column = [1 4];

        dropHtml = fullfile(state.Config.MatlabRoot, "resources", "ui", "image_dropzone.html");
        handles.dropZone = uihtml(grid, ...
            "HTMLSource", dropHtml, ...
            "DataChangedFcn", @(src, ~) onImageDropped(src));
        handles.dropZone.Layout.Row = 2;
        handles.dropZone.Layout.Column = [1 4];

        uilabel(grid, "Text", "Image");
        handles.imageField = uieditfield(grid, "text");
        handles.imageField.Layout.Row = 3;
        handles.imageField.Layout.Column = [2 3];
        handles.selectImageButton = uibutton(grid, "Text", "Browse", ...
            "ButtonPushedFcn", @(~, ~) onSelectImage());
        handles.selectImageButton.Layout.Row = 3;
        handles.selectImageButton.Layout.Column = 4;

        uilabel(grid, "Text", "Prompt");
        handles.promptText = uitextarea(grid);
        handles.promptText.Value = {""};
        handles.promptText.Layout.Row = 4;
        handles.promptText.Layout.Column = [2 4];

        handles.parseButton = uibutton(grid, "Text", "Read with Gemini", ...
            "ButtonPushedFcn", @(~, ~) onParseWithGemini());
        handles.parseButton.FontWeight = "bold";
        handles.parseButton.BackgroundColor = [0.145 0.486 0.353];
        handles.parseButton.FontColor = [1 1 1];
        handles.parseButton.Layout.Row = 5;
        handles.parseButton.Layout.Column = [2 3];
        handles.openSpecButton = uibutton(grid, "Text", "Open JSON", ...
            "ButtonPushedFcn", @(~, ~) onOpenSpec());
        handles.openSpecButton.Layout.Row = 5;
        handles.openSpecButton.Layout.Column = 4;

        handles.inputStatus = uitextarea(grid);
        handles.inputStatus.Editable = "off";
        handles.inputStatus.FontName = "Helvetica";
        handles.inputStatus.Layout.Row = 6;
        handles.inputStatus.Layout.Column = [1 4];

        uilabel(grid, "Text", "Spec preview");
        handles.specDisplay = uitextarea(grid);
        handles.specDisplay.Editable = "off";
        handles.specDisplay.FontName = "Menlo";
        handles.specDisplay.Layout.Row = 8;
        handles.specDisplay.Layout.Column = [1 4];
    end

    function buildAgentTab(parent)
        tab = uitab(parent, "Title", "Build Model");
        grid = uigridlayout(tab, [5 3]);
        grid.RowHeight = {180, 34, 34, "1x", 34};
        grid.ColumnWidth = {"1x", 170, 170};
        grid.Padding = [12 12 12 12];
        grid.RowSpacing = 8;
        grid.ColumnSpacing = 8;

        handles.setupReport = uitextarea(grid);
        handles.setupReport.Editable = "off";
        handles.setupReport.FontName = "Helvetica";
        handles.setupReport.Layout.Row = 1;
        handles.setupReport.Layout.Column = [1 3];

        handles.generateTaskButton = uibutton(grid, "Text", "Prepare Build", ...
            "ButtonPushedFcn", @(~, ~) onGenerateAgentTask());
        handles.generateTaskButton.Layout.Row = 2;
        handles.generateTaskButton.Layout.Column = 1;
        handles.runAgentButton = uibutton(grid, "Text", "Build Model", ...
            "ButtonPushedFcn", @(~, ~) onRunAgent());
        handles.runAgentButton.FontWeight = "bold";
        handles.runAgentButton.BackgroundColor = [0.145 0.486 0.353];
        handles.runAgentButton.FontColor = [1 1 1];
        handles.runAgentButton.Layout.Row = 2;
        handles.runAgentButton.Layout.Column = 2;
        handles.openTaskButton = uibutton(grid, "Text", "View Task", ...
            "ButtonPushedFcn", @(~, ~) onOpenTask());
        handles.openTaskButton.Layout.Row = 2;
        handles.openTaskButton.Layout.Column = 3;

        handles.agentStatus = uilabel(grid);
        handles.agentStatus.FontName = "Helvetica";
        handles.agentStatus.Layout.Row = 3;
        handles.agentStatus.Layout.Column = [1 3];

        handles.agentOutput = uitextarea(grid);
        handles.agentOutput.Editable = "off";
        handles.agentOutput.FontName = "Menlo";
        handles.agentOutput.Layout.Row = 4;
        handles.agentOutput.Layout.Column = [1 3];

        handles.refreshSetupButton = uibutton(grid, "Text", "Refresh Setup", ...
            "ButtonPushedFcn", @(~, ~) onRefreshSetup());
        handles.refreshSetupButton.Layout.Row = 5;
        handles.refreshSetupButton.Layout.Column = 3;
    end

    function buildModelTab(parent)
        tab = uitab(parent, "Title", "Model Lab");
        grid = uigridlayout(tab, [5 4]);
        grid.RowHeight = {34, 34, 34, "1x", 160};
        grid.ColumnWidth = {90, "1x", 150, 150};
        grid.Padding = [12 12 12 12];
        grid.RowSpacing = 8;
        grid.ColumnSpacing = 8;

        uilabel(grid, "Text", "Model path");
        handles.modelPathField = uieditfield(grid, "text");
        handles.modelPathField.Layout.Row = 1;
        handles.modelPathField.Layout.Column = 2;
        handles.openModelButton = uibutton(grid, "Text", "Open", ...
            "ButtonPushedFcn", @(~, ~) onOpenModel());
        handles.openModelButton.Layout.Row = 1;
        handles.openModelButton.Layout.Column = 3;
        handles.selectModelButton = uibutton(grid, "Text", "Choose .slx", ...
            "ButtonPushedFcn", @(~, ~) onSelectModel());
        handles.selectModelButton.Layout.Row = 1;
        handles.selectModelButton.Layout.Column = 4;

        handles.checkModelButton = uibutton(grid, "Text", "Check", ...
            "ButtonPushedFcn", @(~, ~) onCheckModel());
        handles.checkModelButton.Layout.Row = 2;
        handles.checkModelButton.Layout.Column = 3;
        handles.runSimulationButton = uibutton(grid, "Text", "Simulate", ...
            "ButtonPushedFcn", @(~, ~) onRunSimulation());
        handles.runSimulationButton.Layout.Row = 2;
        handles.runSimulationButton.Layout.Column = 4;

        handles.modelStatus = uilabel(grid);
        handles.modelStatus.FontName = "Helvetica";
        handles.modelStatus.Layout.Row = 3;
        handles.modelStatus.Layout.Column = [1 4];

        handles.modelOutput = uitextarea(grid);
        handles.modelOutput.Editable = "off";
        handles.modelOutput.FontName = "Menlo";
        handles.modelOutput.Layout.Row = 4;
        handles.modelOutput.Layout.Column = [1 4];

        handles.modelPathsDisplay = uitextarea(grid);
        handles.modelPathsDisplay.Editable = "off";
        handles.modelPathsDisplay.FontName = "Menlo";
        handles.modelPathsDisplay.Layout.Row = 5;
        handles.modelPathsDisplay.Layout.Column = [1 4];
    end

    function buildTeachTab(parent)
        tab = uitab(parent, "Title", "Teach");
        grid = uigridlayout(tab, [7 4]);
        grid.RowHeight = {34, "1x", 82, 34, 34, 34, 100};
        grid.ColumnWidth = {160, "1x", 150, 150};
        grid.Padding = [12 12 12 12];
        grid.RowSpacing = 8;
        grid.ColumnSpacing = 8;

        handles.startTeachingButton = uibutton(grid, "Text", "Start Teaching", ...
            "ButtonPushedFcn", @(~, ~) onStartTeaching());
        handles.startTeachingButton.FontWeight = "bold";
        handles.startTeachingButton.Layout.Row = 1;
        handles.startTeachingButton.Layout.Column = 1;
        handles.focusSelector = uidropdown(grid, "Items", "");
        handles.focusSelector.Layout.Row = 1;
        handles.focusSelector.Layout.Column = 2;
        handles.highlightButton = uibutton(grid, "Text", "Highlight", ...
            "ButtonPushedFcn", @(~, ~) onHighlightCurrent());
        handles.highlightButton.Layout.Row = 1;
        handles.highlightButton.Layout.Column = 3;
        handles.zoomButton = uibutton(grid, "Text", "Zoom", ...
            "ButtonPushedFcn", @(~, ~) onZoomCurrent());
        handles.zoomButton.Layout.Row = 1;
        handles.zoomButton.Layout.Column = 4;

        handles.currentStepDisplay = uitextarea(grid);
        handles.currentStepDisplay.Editable = "off";
        handles.currentStepDisplay.FontName = "Menlo";
        handles.currentStepDisplay.Layout.Row = 2;
        handles.currentStepDisplay.Layout.Column = [1 4];

        handles.studentAnswer = uitextarea(grid);
        handles.studentAnswer.Layout.Row = 3;
        handles.studentAnswer.Layout.Column = [1 4];

        handles.nextHintButton = uibutton(grid, "Text", "Next Hint", ...
            "ButtonPushedFcn", @(~, ~) onNextHint());
        handles.nextHintButton.Layout.Row = 4;
        handles.nextHintButton.Layout.Column = 3;
        handles.revealButton = uibutton(grid, "Text", "Reveal", ...
            "ButtonPushedFcn", @(~, ~) onReveal());
        handles.revealButton.Layout.Row = 4;
        handles.revealButton.Layout.Column = 4;

        handles.teachStatus = uilabel(grid);
        handles.teachStatus.FontName = "Helvetica";
        handles.teachStatus.Layout.Row = 5;
        handles.teachStatus.Layout.Column = [1 4];

        handles.teachOutput = uitextarea(grid);
        handles.teachOutput.Editable = "off";
        handles.teachOutput.FontName = "Menlo";
        handles.teachOutput.Layout.Row = [6 7];
        handles.teachOutput.Layout.Column = [1 4];
    end

    function buildProbeTab(parent)
        tab = uitab(parent, "Title", "Probe & Compare");
        grid = uigridlayout(tab, [7 4]);
        grid.RowHeight = {34, 34, 34, "1x", 34, 34, 150};
        grid.ColumnWidth = {150, "1x", 160, 160};
        grid.Padding = [12 12 12 12];
        grid.RowSpacing = 8;
        grid.ColumnSpacing = 8;

        uilabel(grid, "Text", "Focus / probe");
        handles.probeSelector = uidropdown(grid, "Items", "");
        handles.probeSelector.Layout.Row = 1;
        handles.probeSelector.Layout.Column = 2;
        handles.addProbeButton = uibutton(grid, "Text", "Place Probe", ...
            "ButtonPushedFcn", @(~, ~) onAddProbe());
        handles.addProbeButton.Layout.Row = 1;
        handles.addProbeButton.Layout.Column = 3;

        uilabel(grid, "Text", "Lab CSV");
        handles.labCsvField = uieditfield(grid, "text");
        handles.labCsvField.Layout.Row = 2;
        handles.labCsvField.Layout.Column = 2;
        handles.selectCsvButton = uibutton(grid, "Text", "Select CSV", ...
            "ButtonPushedFcn", @(~, ~) onSelectCsv());
        handles.selectCsvButton.Layout.Row = 2;
        handles.selectCsvButton.Layout.Column = 3;
        handles.compareDeltaButton = uibutton(grid, "Text", "Compare", ...
            "ButtonPushedFcn", @(~, ~) onCompareLabDelta());
        handles.compareDeltaButton.Layout.Row = 2;
        handles.compareDeltaButton.Layout.Column = 4;

        handles.probeStatus = uilabel(grid);
        handles.probeStatus.FontName = "Helvetica";
        handles.probeStatus.Layout.Row = 3;
        handles.probeStatus.Layout.Column = [1 4];

        handles.probeOutput = uitextarea(grid);
        handles.probeOutput.Editable = "off";
        handles.probeOutput.FontName = "Menlo";
        handles.probeOutput.Layout.Row = 4;
        handles.probeOutput.Layout.Column = [1 4];

        handles.deltaStatus = uilabel(grid);
        handles.deltaStatus.FontName = "Helvetica";
        handles.deltaStatus.Layout.Row = 5;
        handles.deltaStatus.Layout.Column = [1 4];

        handles.deltaOutput = uitextarea(grid);
        handles.deltaOutput.Editable = "off";
        handles.deltaOutput.FontName = "Menlo";
        handles.deltaOutput.Layout.Row = [6 7];
        handles.deltaOutput.Layout.Column = [1 4];
    end

    function onSelectImage()
        [file, folder] = uigetfile({"*.png;*.jpg;*.jpeg;*.gif;*.webp", "Circuit images"; "*.*", "All files"});
        if isequal(file, 0)
            return
        end
        state.ImagePath = string(fullfile(folder, file));
        refreshAll();
    end

    function onImageDropped(src)
        data = src.Data;
        if isempty(data) || ~isstruct(data) || ~isfield(data, "kind")
            return
        end

        kind = string(data.kind);
        if kind == "drop-error"
            message = "Could not use dropped file.";
            if isfield(data, "message")
                message = string(data.message);
            end
            setArea(handles.inputStatus, message);
            return
        end
        if kind ~= "image-drop"
            return
        end

        try
            savedPath = saveDroppedImage(data);
            state.ImagePath = savedPath;
            handles.imageField.Value = char(savedPath);
            setPipeline("Image ready. Next: Read with Gemini.", 12);
            setArea(handles.inputStatus, "Image ready. Click Read with Gemini when you are ready." + newline + savedPath);
        catch dropError
            setArea(handles.inputStatus, "Could not save dropped image: " + string(dropError.message));
            setPipeline("Image drop failed. Try another file.", 0);
        end
    end

    function onParseWithGemini()
        state.ImagePath = string(handles.imageField.Value);
        state.PromptText = textAreaText(handles.promptText);
        try
            setBusy("Reading circuit with Gemini...", 25);
            progress = startProgress("Reading Circuit", "Gemini is parsing the image and prompt into a model spec.");
            cleanup = onCleanup(@() finishProgress(progress));
            parsed = feval('citt.parseCircuitWithGemini', state.ImagePath, state.PromptText);
            state.Spec = parsed.spec;
            state.SpecPath = parsed.spec_path;
            refreshAll();
            setArea(handles.specDisplay, specSummary(parsed.spec));
            setArea(handles.inputStatus, parseNextStepText(parsed));
            if strlength(specBlockingIssues(parsed.spec)) > 0
                setPipeline("Clarification needed before Build Model.", 35);
            else
                setPipeline("Circuit spec ready. Next: Prepare Build.", 35);
            end
        catch parseError
            setArea(handles.inputStatus, "Parse failed: " + string(parseError.message));
            setPipeline("Read failed. Check input or setup.", 10);
        end
        setIdle();
    end

    function onOpenSpec()
        try
            if exist(state.SpecPath, "file") ~= 2
                setArea(handles.inputStatus, "No spec JSON exists yet. Read a circuit with Gemini first.");
                return
            end
            edit(char(state.SpecPath));
        catch openError
            setArea(handles.inputStatus, "Could not open spec JSON: " + string(openError.message));
        end
    end

    function text = parseNextStepText(parsed)
        spec = parsed.spec;
        blockingIssues = specBlockingIssues(spec);
        notes = specBuildNotes(spec);
        if strlength(blockingIssues) > 0
            text = strjoin([
                "Circuit read, but it is not build-ready yet."
                "CiTT found unclear or unsupported regions that must be clarified before model generation."
                ""
                blockingIssues
                ""
                "Next: edit the prompt with the missing/clarified values, then click Read with Gemini again."
                "Spec saved at: " + parsed.spec_path
            ], newline);
        else
            text = strjoin([
                "Circuit read successfully."
                emptyText(notes, "Symbolic or omitted values will be kept as model parameters.")
                "Next: open Build Model, then click Prepare Build."
                "Spec saved at: " + parsed.spec_path
            ], newline);
        end
    end

    function onGenerateAgentTask()
        try
            setBusy("Preparing SATK build task...", 45);
            progress = startProgress("Preparing Build", "CiTT is converting the circuit spec into a Simscape-first agent task.");
            cleanup = onCleanup(@() finishProgress(progress));
            generated = feval('citt.buildAgentTask', state.SpecPath);
            state.AgentTaskPath = generated.task_path;
            refreshAll();
            handles.agentStatus.Text = "Build task ready";
            setArea(handles.agentOutput, "Build task ready. Build Model will generate and run MATLAB Simscape code." + newline + generated.task_path);
            setPipeline("Build task ready. Next: Build Model.", 55);
        catch taskError
            setArea(handles.agentOutput, "Build preparation failed: " + string(taskError.message));
            setPipeline("Prepare Build failed. Resolve the listed issue.", 35);
        end
        setIdle();
    end

    function onRunAgent()
        try
            setBusy("Building Simscape model...", 68);
            progress = startProgress("Building Model", "Gemini CLI and SATK are building the Simscape model. This can take a while.");
            cleanup = onCleanup(@() finishProgress(progress));
            runResult = feval('citt.runAgentTask', state.AgentTaskPath, struct("SpecPath", state.SpecPath));
            state.AgentRun = runResult;
            if strlength(runResult.produced_model_path) > 0
                state.ModelPath = runResult.produced_model_path;
            end
            refreshAll();
            setArea(handles.agentOutput, agentRunSummary(runResult));
            handles.agentStatus.Text = "Model built";
            setPipeline("Model built. Next: Check or Simulate.", 78);
        catch runError
            handles.agentStatus.Text = "Build failed";
            setArea(handles.agentOutput, "Model build failed: " + string(runError.message));
            setPipeline("Build failed. See Build Model output.", 55);
        end
        setIdle();
    end

    function onOpenTask()
        try
            edit(char(state.AgentTaskPath));
        catch openError
            setArea(handles.agentOutput, "Could not open task: " + string(openError.message));
        end
    end

    function onRefreshSetup()
        state.LastSetupReport = feval('citt.checkSetup');
        refreshAll();
    end

    function onSelectModel()
        [file, folder] = uigetfile({"*.slx;*.mdl", "Simulink models"; "*.*", "All files"});
        if isequal(file, 0)
            return
        end
        state.ModelPath = string(fullfile(folder, file));
        refreshAll();
    end

    function onOpenModel()
        state.ModelPath = string(handles.modelPathField.Value);
        refreshAll();
        try
            opened = feval('citt.openOrCreateModel', state.ModelPath);
            handles.modelStatus.Text = opened.message;
            setArea(handles.modelOutput, "Model opened." + newline + opened.model_path);
            setPipeline("Model open in Simulink. Next: Check.", 78);
        catch openError
            setArea(handles.modelOutput, "Open model failed: " + string(openError.message));
        end
    end

    function onCheckModel()
        state.ModelPath = string(handles.modelPathField.Value);
        try
            setBusy("Checking model...", 86);
            progress = startProgress("Checking Model", "Simulink is updating and checking the generated model.");
            cleanup = onCleanup(@() finishProgress(progress));
            checked = feval('citt.runModelCheck', state.ModelPath);
            state.LastModelCheck = checked;
            handles.modelStatus.Text = "Model check complete";
            setArea(handles.modelOutput, modelCheckSummary(checked));
            setPipeline("Model check complete. Next: Simulate or Teach.", 90);
        catch checkError
            handles.modelStatus.Text = "Model check failed";
            setArea(handles.modelOutput, string(checkError.message));
            setPipeline("Model check failed. See Model Lab output.", 78);
        end
        setIdle();
    end

    function onRunSimulation()
        state.ModelPath = string(handles.modelPathField.Value);
        try
            setBusy("Running simulation...", 94);
            progress = startProgress("Running Simulation", "Simulink is simulating the generated model.");
            cleanup = onCleanup(@() finishProgress(progress));
            simulated = feval('citt.runSimulation', state.ModelPath);
            state.LastSimulation = simulated;
            handles.modelStatus.Text = "Simulation complete";
            setArea(handles.modelOutput, simulationSummary(simulated));
            setPipeline("Simulation complete. Teach and compare are available.", 100);
        catch simError
            handles.modelStatus.Text = "Simulation failed";
            setArea(handles.modelOutput, string(simError.message));
            setPipeline("Simulation failed. See Model Lab output.", 90);
        end
        setIdle();
    end

    function onStartTeaching()
        try
            setBusy("Building teaching plan...", 92);
            progress = startProgress("Teaching Plan", "CiTT is reading the focus map and preparing the first Socratic step.");
            cleanup = onCleanup(@() finishProgress(progress));
            built = feval('citt.buildTeachingPlan', state.SpecPath, state.FocusMapPath, state.LastModelCheck, state.LastSimulation);
            state.TeachingPlan = built.plan;
            state.TeachingStepIndex = 1;
            state.HintLevel = 0;
            showCurrentStep();
            updateFocusSelectors();
            setPipeline("Teaching plan ready. Work through the focus step.", 92);
        catch teachError
            setArea(handles.teachOutput, "Teaching plan failed: " + string(teachError.message));
            setPipeline("Teaching plan failed. Check focus map output.", 78);
        end
        setIdle();
    end

    function onNextHint()
        if isempty(state.TeachingPlan)
            onStartTeaching();
        end
        try
            setBusy("Reading student answer...", 92);
            progress = startProgress("Socratic Hint", "Gemini is classifying the answer and preparing one local hint.");
            cleanup = onCleanup(@() finishProgress(progress));
            answer = textAreaText(handles.studentAnswer);
            turn = feval('citt.runSocraticTurn', state.TeachingPlan, state.TeachingStepIndex, answer, ...
                struct("Action", "hint", "HintLevel", state.HintLevel));
            state.HintLevel = turn.next_hint_level;
            handles.teachStatus.Text = "Classification: " + turn.classification;
            setArea(handles.teachOutput, turn.message);
        catch hintError
            setArea(handles.teachOutput, "Hint failed: " + string(hintError.message));
        end
        setIdle();
    end

    function onReveal()
        if isempty(state.TeachingPlan)
            onStartTeaching();
        end
        turn = feval('citt.runSocraticTurn', state.TeachingPlan, state.TeachingStepIndex, textAreaText(handles.studentAnswer), ...
            struct("Action", "reveal"));
        handles.teachStatus.Text = "Reveal shown for " + turn.step_id;
        setArea(handles.teachOutput, turn.message);
    end

    function onHighlightCurrent()
        focusId = string(handles.focusSelector.Value);
        highlighted = feval('citt.highlightFocus', state.ModelPath, state.FocusMapPath, focusId);
        handles.teachStatus.Text = "Highlighted: " + string(highlighted.success);
        setArea(handles.teachOutput, feval('citt.util.jsonEncode', highlighted));
    end

    function onZoomCurrent()
        focusId = string(handles.focusSelector.Value);
        zoomed = feval('citt.zoomToFocus', state.ModelPath, state.FocusMapPath, focusId);
        handles.teachStatus.Text = zoomed.message;
        setArea(handles.teachOutput, feval('citt.util.jsonEncode', zoomed));
    end

    function onAddProbe()
        targetId = string(handles.probeSelector.Value);
        probed = feval('citt.addProbe', state.ModelPath, targetId, state.ProbeMapPath, state.SpecPath);
        state.LastProbe = probed;
        handles.probeStatus.Text = "Probe plan success: " + string(probed.success);
        setArea(handles.probeOutput, feval('citt.util.jsonEncode', probed));
    end

    function onSelectCsv()
        [file, folder] = uigetfile({"*.csv", "CSV files"; "*.*", "All files"});
        if isequal(file, 0)
            return
        end
        state.LabCsvPath = string(fullfile(folder, file));
        refreshAll();
    end

    function onCompareLabDelta()
        state.LabCsvPath = string(handles.labCsvField.Value);
        try
            delta = feval('citt.compareLabDelta', struct(), struct(), state.LabCsvPath);
            state.LastLabDelta = delta;
            handles.deltaStatus.Text = "Lab Delta rows: " + string(numel(delta.rows));
            setArea(handles.deltaOutput, feval('citt.util.jsonEncode', delta));
        catch deltaError
            setArea(handles.deltaOutput, "Lab Delta failed: " + string(deltaError.message));
        end
    end

    function showCurrentStep()
        if isempty(state.TeachingPlan)
            setArea(handles.currentStepDisplay, "No teaching plan yet.");
            return
        end
        step = state.TeachingPlan.steps(state.TeachingStepIndex);
        text = strjoin([
            "Step: " + string(step.id)
            "Title: " + string(step.title)
            "Focus: " + string(step.focus_id)
            "Concept: " + string(step.concept)
            "Question: " + string(step.student_question)
        ], newline);
        setArea(handles.currentStepDisplay, text);
        setArea(handles.teachOutput, string(step.student_question));
    end

    function updateFocusSelectors()
        values = focusValues();
        if isempty(values)
            values = "";
        end
        values = values(:)';
        handles.focusSelector.Items = values;
        handles.probeSelector.Items = values;
        handles.focusSelector.Value = values(1);
        handles.probeSelector.Value = values(1);
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

    function refreshAll()
        statusLabel.Text = compactStatus(state);
        handles.imageField.Value = char(state.ImagePath);
        handles.modelPathField.Value = char(state.ModelPath);
        handles.labCsvField.Value = char(state.LabCsvPath);
        setArea(handles.setupReport, setupOverviewText(state.LastSetupReport));
        handles.agentStatus.Text = "Task file: " + state.AgentTaskPath;
        handles.modelStatus.Text = "Model: " + state.ModelPath;
        setArea(handles.modelPathsDisplay, pathStatusText(state));
        setArea(handles.inputStatus, inputStatusText(state));
        setArea(handles.specDisplay, currentSpecPreview(state));
        updatePipelineFromState(state);
        updateFocusSelectors();
    end

    function text = compactStatus(currentState)
        setup = currentState.LastSetupReport;
        text = "Gemini " + readyNeeds(setup.gemini_key_found) + ...
            " | SATK " + readyNeeds(setup.satk_initialize_available) + ...
            " | Simscape " + readyNeeds(setup.simscape_available);
    end

    function text = inputStatusText(currentState)
        setup = currentState.LastSetupReport;
        text = strjoin([
            "Image: " + emptyText(currentState.ImagePath, "drop or browse for a circuit image")
            "Gemini: " + readyNeeds(setup.gemini_key_found) + " using " + setup.gemini_model
            "SATK: " + readyNeeds(setup.satk_initialize_available) + " | MCP: " + readyNeeds(setup.matlab_mcp_available) + " | Simscape: " + readyNeeds(setup.simscape_available)
            "Spec file: " + currentState.SpecPath
        ], newline);
    end

    function text = setupOverviewText(setup)
        agentText = "needs CLI";
        for i = 1:numel(setup.agent_clis)
            if setup.agent_clis(i).available
                agentText = "ready: " + setup.agent_clis(i).name;
                break
            end
        end

        text = strjoin([
            "Ready checks"
            ""
            "Gemini API: " + readyNeeds(setup.gemini_key_found)
            "Model: " + setup.gemini_model
            "Simulink Agentic Toolkit: " + readyNeeds(setup.satk_initialize_available)
            "MATLAB MCP Server: " + readyNeeds(setup.matlab_mcp_available)
            "Simscape: " + readyNeeds(setup.simscape_available)
            "Agent CLI: " + agentText
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
        ], newline);
    end

    function text = textAreaText(area)
        value = string(area.Value);
        text = strjoin(value(:), newline);
    end

    function setArea(area, text)
        area.Value = cellstr(splitlines(string(text)));
    end

    function savedPath = saveDroppedImage(data)
        name = structString(data, "name", "dropped_circuit.png");
        mimeType = structString(data, "mimeType", "image/png");
        dataUrl = structString(data, "dataUrl", "");
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

    function value = structString(data, fieldName, defaultValue)
        if isstruct(data) && isfield(data, fieldName)
            value = string(data.(fieldName));
        else
            value = string(defaultValue);
        end
    end

    function text = currentSpecPreview(currentState)
        if ~isempty(currentState.Spec)
            text = specSummary(currentState.Spec);
            return
        end

        if exist(currentState.SpecPath, "file") == 2
            try
                spec = jsondecode(fileread(currentState.SpecPath));
                text = specSummary(spec);
                return
            catch previewError
                text = "Last spec exists but could not be summarized: " + string(previewError.message);
                return
            end
        end

        text = strjoin([
            "No circuit spec yet."
            "Drop or browse for an image, then click Read with Gemini."
        ], newline);
    end

    function updatePipelineFromState(currentState)
        if ~isempty(currentState.LastSimulation)
            setPipeline("Simulation complete.", 100);
        elseif ~isempty(currentState.TeachingPlan)
            setPipeline("Teaching plan ready.", 92);
        elseif ~isempty(currentState.LastModelCheck)
            setPipeline("Model check complete.", 90);
        elseif strlength(currentState.ModelPath) > 0 && exist(currentState.ModelPath, "file") == 2
            setPipeline("Model available. Next: Check.", 78);
        elseif ~isempty(currentState.AgentRun)
            setPipeline("Agent run complete. Check generated artifacts.", 70);
        elseif strlength(currentState.AgentTaskPath) > 0 && exist(currentState.AgentTaskPath, "file") == 2
            setPipeline("Build task ready. Next: Build Model.", 55);
        elseif ~isempty(currentState.Spec) || (strlength(currentState.SpecPath) > 0 && exist(currentState.SpecPath, "file") == 2)
            setPipeline("Circuit spec available. Next: Prepare Build.", 35);
        elseif strlength(currentState.ImagePath) > 0 || strlength(strtrim(currentState.PromptText)) > 0
            setPipeline("Input ready. Next: Read with Gemini.", 12);
        else
            setPipeline("Ready for circuit input.", 0);
        end
    end

    function setPipeline(message, value)
        try
            pipelineLabel.Text = string(message);
            if nargin >= 2 && ~isempty(value)
                pipelineGauge.Value = max(0, min(100, double(value)));
            end
            drawnow limitrate;
        catch
        end
    end

    function setBusy(message, value)
        statusLabel.Text = string(message);
        if nargin >= 2
            setPipeline(message, value);
        else
            setPipeline(message, []);
        end
        try
            app.Figure.Pointer = "watch";
        catch
        end
        drawnow;
    end

    function setIdle()
        statusLabel.Text = compactStatus(state);
        try
            app.Figure.Pointer = "arrow";
        catch
        end
        drawnow;
    end

    function progress = startProgress(titleText, messageText)
        progress = [];
        try
            progress = uiprogressdlg(app.Figure, ...
                "Title", char(titleText), ...
                "Message", char(messageText), ...
                "Indeterminate", "on", ...
                "Cancelable", "off");
            drawnow;
        catch
            progress = [];
        end
    end

    function finishProgress(progress)
        if isempty(progress)
            return
        end
        try
            if isvalid(progress)
                close(progress);
            end
        catch
        end
    end

    function text = specSummary(spec)
        circuitType = getSpecText(spec, "circuit_type", "unknown circuit");
        nodes = getSpecValue(spec, "nodes");
        components = getSpecValue(spec, "components");
        outputs = getSpecValue(spec, "requested_outputs");
        analysis = getSpecText(spec, "likely_analysis", "not specified");
        assumptions = getSpecValue(spec, "assumptions");
        suggestedBlocks = getSpecValue(spec, "suggested_simscape_blocks");
        blockingIssues = specBlockingIssues(spec);
        notes = specBuildNotes(spec);

        if strlength(blockingIssues) > 0
            readiness = "Needs topology/region clarification before model build";
        else
            readiness = "Ready for Build Model > Prepare Build. Missing values become parameters";
        end

        text = strjoin([
            "Circuit: " + circuitType
            "Status: " + readiness
            "Likely analysis: " + analysis
            "Components: " + string(countItems(components))
            "Nodes: " + joinValue(nodes)
            "Requested outputs: " + joinValue(outputs)
            ""
            "Assumptions"
            listValue(assumptions)
            ""
            "Suggested Simscape blocks"
            listValue(suggestedBlocks)
            ""
            "Build notes"
            emptyText(notes, "none")
            ""
            "Blocking issues"
            emptyText(blockingIssues, "none")
        ], newline);
    end

    function issues = specBlockingIssues(spec)
        parts = strings(0, 1);
        if isstruct(spec) && isfield(spec, "unsupported_or_unclear_regions")
            text = joinValue(spec.unsupported_or_unclear_regions);
            if strlength(strtrim(text)) > 0
                parts(end + 1) = "Unclear region: " + text; %#ok<AGROW>
            end
        end
        issues = strjoin(parts, newline);
    end

    function notes = specBuildNotes(spec)
        parts = strings(0, 1);
        if isstruct(spec) && isfield(spec, "ambiguities")
            text = joinValue(spec.ambiguities);
            if strlength(strtrim(text)) > 0
                parts(end + 1) = "Ambiguity note: " + text; %#ok<AGROW>
            end
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

    function text = agentRunSummary(runResult)
        text = strjoin([
            "Simscape build complete."
            "Generated code: " + emptyText(fieldText(runResult, "generated_code_path"), "not written")
            "Model: " + emptyText(runResult.produced_model_path, "not found")
            "Focus map: " + emptyText(runResult.produced_focus_map_path, "not found")
            "Probe map: " + emptyText(runResult.produced_probe_map_path, "not found")
            "Report: " + emptyText(fieldText(runResult, "agent_report_path"), "not written")
            "Exit status: " + string(runResult.exit_status)
            ""
            "Command"
            string(runResult.command)
        ], newline);

        stdoutTail = tailText(runResult.stdout, 30);
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

    function text = tailText(value, maxLines)
        lines = splitlines(string(value));
        if numel(lines) > maxLines
            lines = lines(end - maxLines + 1:end);
        end
        text = strjoin(lines(:), newline);
    end

    function text = readyNeeds(flag)
        if flag
            text = "ready";
        else
            text = "needs setup";
        end
    end

    function text = emptyText(value, defaultText)
        value = string(value);
        if strlength(value) == 0
            text = string(defaultText);
        else
            text = value;
        end
    end

    function text = fieldText(data, fieldName)
        if isstruct(data) && isfield(data, fieldName)
            text = string(data.(fieldName));
        else
            text = "";
        end
    end
end
