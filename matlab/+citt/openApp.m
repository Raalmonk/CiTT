function app = openApp()
%OPENAPP Build the MATLAB-native CiTT plugin UI.

state = feval('citt.appState');
state.LastSetupReport = feval('citt.checkSetup');

app = struct();
app.Figure = uifigure( ...
    "Name", "CiTT Circuit Tutor", ...
    "Position", [70 60 1240 800]);
app.Figure.Color = [0.965 0.976 0.969];
app.Figure.CloseRequestFcn = @(src, ~) onCloseApp(src);

main = uigridlayout(app.Figure, [2 1]);
main.RowHeight = {108, "1x"};
main.Padding = [18 14 18 16];
main.RowSpacing = 12;

handles = struct();
agentPollTimer = [];
activeWorkflowPage = "read";
palette = struct();
palette.primary = [0.145 0.486 0.353];
palette.primaryDark = [0.07 0.18 0.14];
palette.surface = [0.986 0.992 0.987];
palette.soft = [0.92 0.949 0.933];
palette.text = [0.08 0.16 0.13];

header = uigridlayout(main, [3 4]);
header.ColumnWidth = {"1x", 220, 220, 220};
header.RowHeight = {30, 26, 32};
header.Padding = [0 0 0 0];
header.RowSpacing = 5;
header.ColumnSpacing = 12;
header.Layout.Row = 1;

titleLabel = uilabel(header);
titleLabel.Text = "CiTT Circuit Tutor";
titleLabel.FontSize = 23;
titleLabel.FontWeight = "bold";
titleLabel.Tooltip = "Circuit insight, teaching, and Simscape model building inside MATLAB.";
titleLabel.Layout.Row = [1 2];
titleLabel.Layout.Column = 1;

stageGrid = uigridlayout(header, [1 5]);
stageGrid.ColumnWidth = {"1x", "1x", "1x", "1.25x", "1.2x"};
stageGrid.Padding = [0 0 0 0];
stageGrid.ColumnSpacing = 5;
stageGrid.Layout.Row = 3;
stageGrid.Layout.Column = 1;
handles.stageRead = makeStageChip(stageGrid, "Read", "read");
handles.stageRead.Layout.Row = 1;
handles.stageRead.Layout.Column = 1;
handles.stageBuild = makeStageChip(stageGrid, "Build", "build");
handles.stageBuild.Layout.Row = 1;
handles.stageBuild.Layout.Column = 2;
handles.stageTeach = makeStageChip(stageGrid, "Teach", "teach");
handles.stageTeach.Layout.Row = 1;
handles.stageTeach.Layout.Column = 3;
handles.stageProbe = makeStageChip(stageGrid, "Probe", "probe");
handles.stageProbe.Layout.Row = 1;
handles.stageProbe.Layout.Column = 4;
handles.stageEvidence = makeStageChip(stageGrid, "Evidence", "evidence");
handles.stageEvidence.Layout.Row = 1;
handles.stageEvidence.Layout.Column = 5;

statusLabel = uilabel(header);
statusLabel.HorizontalAlignment = "right";
statusLabel.FontSize = 13;
statusLabel.FontWeight = "bold";
statusLabel.Text = compactStatus(state);
statusLabel.Layout.Row = 1;
statusLabel.Layout.Column = [2 4];

pipelineLabel = uilabel(header);
pipelineLabel.HorizontalAlignment = "right";
pipelineLabel.FontSize = 12;
pipelineLabel.Text = "Ready for circuit input";
pipelineLabel.Layout.Row = 2;
pipelineLabel.Layout.Column = [2 4];

handles.pipelineProgress = uilabel(header, "Text", "Progress 0%");
handles.pipelineProgress.HorizontalAlignment = "center";
handles.pipelineProgress.FontWeight = "bold";
handles.pipelineProgress.FontSize = 11;
handles.pipelineProgress.Layout.Row = 3;
handles.pipelineProgress.Layout.Column = [2 3];
setTone(handles.pipelineProgress, "gray");

handles.nextActionButton = uibutton(header, "Text", "Next: Read Circuit", ...
    "ButtonPushedFcn", @(~, ~) onNextAction());
handles.nextActionButton.FontWeight = "bold";
handles.nextActionButton.BackgroundColor = [0.145 0.486 0.353];
handles.nextActionButton.FontColor = [1 1 1];
handles.nextActionButton.Layout.Row = 3;
handles.nextActionButton.Layout.Column = 4;

contentHost = uigridlayout(main, [1 1]);
contentHost.Layout.Row = 2;
contentHost.Padding = [0 0 0 0];
contentHost.RowSpacing = 0;
contentHost.ColumnSpacing = 0;

buildInputTab(contentHost);
buildBuildAndModelTab(contentHost);
buildTeachTab(contentHost);
buildProbeTab(contentHost);
buildEvidenceTab(contentHost);
selectWorkflowTab("read");

app.Handles = handles;
app.State = state;
refreshAll();

    function buildInputTab(parent)
        tab = makeWorkflowPage(parent);
        handles.readTab = tab;
        grid = uigridlayout(tab, [2 3]);
        grid.RowHeight = {"1x", 150};
        grid.ColumnWidth = {"1.15x", "1x", "1x"};
        grid.Padding = [18 16 18 16];
        grid.RowSpacing = 12;
        grid.ColumnSpacing = 12;
        enableScroll(grid);

        inputCard = makeCard(grid, "Circuit Input");
        inputCard.Layout.Row = 1;
        inputCard.Layout.Column = 1;
        inputGrid = uigridlayout(inputCard, [7 3]);
        inputGrid.RowHeight = {24, "1x", 30, 72, 34, 56, 44};
        inputGrid.ColumnWidth = {58, "1x", 108};
        inputGrid.Padding = [12 10 12 12];
        inputGrid.RowSpacing = 8;
        inputGrid.ColumnSpacing = 8;
        enableScroll(inputGrid);

        heading = uilabel(inputGrid, "Text", "Start with a circuit image or prompt");
        heading.FontSize = 15;
        heading.FontWeight = "bold";
        heading.Layout.Row = 1;
        heading.Layout.Column = [1 3];

        dropHtml = fullfile(state.Config.MatlabRoot, "resources", "ui", "image_dropzone.html");
        handles.dropZone = uihtml(inputGrid, ...
            "HTMLSource", dropHtml, ...
            "DataChangedFcn", @(src, ~) onImageDropped(src));
        handles.dropZone.Layout.Row = 2;
        handles.dropZone.Layout.Column = [1 3];

        uilabel(inputGrid, "Text", "Image");
        handles.imageField = uieditfield(inputGrid, "text");
        handles.imageField.Layout.Row = 3;
        handles.imageField.Layout.Column = 2;
        handles.selectImageButton = uibutton(inputGrid, "Text", "Browse", ...
            "ButtonPushedFcn", @(~, ~) onSelectImage());
        handles.selectImageButton.Layout.Row = 3;
        handles.selectImageButton.Layout.Column = 3;
        styleSecondary(handles.selectImageButton);

        uilabel(inputGrid, "Text", "Prompt");
        handles.promptText = uitextarea(inputGrid);
        handles.promptText.Value = {""};
        handles.promptText.ValueChangedFcn = @(~, ~) updateLatexPreviews();
        handles.promptText.Layout.Row = 4;
        handles.promptText.Layout.Column = [2 3];

        handles.parseButton = uibutton(inputGrid, "Text", "Read Circuit", ...
            "ButtonPushedFcn", @(~, ~) onParseWithGemini());
        stylePrimary(handles.parseButton);
        handles.parseButton.Layout.Row = 5;
        handles.parseButton.Layout.Column = [1 2];
        handles.openSpecButton = uibutton(inputGrid, "Text", "Open Spec", ...
            "ButtonPushedFcn", @(~, ~) onOpenSpec());
        handles.openSpecButton.Layout.Row = 5;
        handles.openSpecButton.Layout.Column = 3;
        styleSecondary(handles.openSpecButton);

        handles.promptLatexPreview = makeLatexPreview(inputGrid, "LaTeX preview");
        handles.promptLatexPreview.Layout.Row = 6;
        handles.promptLatexPreview.Layout.Column = [1 3];

        handles.inputStatus = makeSoftArea(inputGrid, "Helvetica");
        handles.inputStatus.Layout.Row = 7;
        handles.inputStatus.Layout.Column = [1 3];

        summaryCard = makeCard(grid, "Circuit Summary");
        summaryCard.Layout.Row = 1;
        summaryCard.Layout.Column = 2;
        summaryGrid = uigridlayout(summaryCard, [1 1]);
        summaryGrid.Padding = [12 10 12 12];
        handles.specDisplay = makeSoftArea(summaryGrid, "Helvetica");
        handles.specDisplay.Layout.Row = 1;
        handles.specDisplay.Layout.Column = 1;

        readinessCard = makeCard(grid, "Assumptions and Clarifications");
        readinessCard.Layout.Row = 1;
        readinessCard.Layout.Column = 3;
        readinessGrid = uigridlayout(readinessCard, [1 1]);
        readinessGrid.Padding = [12 10 12 12];
        handles.readinessDisplay = makeSoftArea(readinessGrid, "Helvetica");
        handles.readinessDisplay.Layout.Row = 1;
        handles.readinessDisplay.Layout.Column = 1;

        advancedCard = makeCard(grid, "Trace Notes");
        advancedCard.Layout.Row = 2;
        advancedCard.Layout.Column = [1 3];
        advancedGrid = uigridlayout(advancedCard, [1 1]);
        advancedGrid.Padding = [12 10 12 12];
        handles.readAdvancedDisplay = makeOutputArea(advancedGrid);
        handles.readAdvancedDisplay.Layout.Row = 1;
        handles.readAdvancedDisplay.Layout.Column = 1;
    end

    function buildBuildAndModelTab(parent)
        tab = makeWorkflowPage(parent);
        handles.buildTab = tab;
        grid = uigridlayout(tab, [4 5]);
        grid.RowHeight = {58, 82, "1x", 116};
        grid.ColumnWidth = {"1x", "1x", "1x", "1x", 238};
        grid.Padding = [18 16 18 16];
        grid.RowSpacing = 12;
        grid.ColumnSpacing = 12;
        enableScroll(grid);

        setupCard = makeCard(grid, "Ready Checks");
        setupCard.Layout.Row = 1;
        setupCard.Layout.Column = [1 5];
        setupGrid = uigridlayout(setupCard, [1 5]);
        setupGrid.ColumnWidth = {"1x", "1x", "1x", "1x", "1.2x"};
        setupGrid.Padding = [12 8 12 10];
        setupGrid.ColumnSpacing = 8;
        handles.geminiChip = makeStatusChip(setupGrid, "Gemini");
        handles.geminiChip.Layout.Row = 1;
        handles.geminiChip.Layout.Column = 1;
        handles.satkChip = makeStatusChip(setupGrid, "SATK");
        handles.satkChip.Layout.Row = 1;
        handles.satkChip.Layout.Column = 2;
        handles.mcpChip = makeStatusChip(setupGrid, "MCP");
        handles.mcpChip.Layout.Row = 1;
        handles.mcpChip.Layout.Column = 3;
        handles.simscapeChip = makeStatusChip(setupGrid, "Simscape");
        handles.simscapeChip.Layout.Row = 1;
        handles.simscapeChip.Layout.Column = 4;
        handles.agentChip = makeStatusChip(setupGrid, "Agent");
        handles.agentChip.Layout.Row = 1;
        handles.agentChip.Layout.Column = 5;

        handles.buildStepSpec = makeStepCard(grid, "Circuit Read", 2, 1);
        handles.buildStepTask = makeStepCard(grid, "Build Brief", 2, 2);
        handles.buildStepAgent = makeStepCard(grid, "Builder", 2, 3);
        handles.buildStepModel = makeStepCard(grid, "Model", 2, 4);
        handles.buildStepCheck = makeStepCard(grid, "Check", 2, 5);

        detailTabs = uitabgroup(grid);
        detailTabs.Layout.Row = [3 4];
        detailTabs.Layout.Column = [1 4];

        agentTab = uitab(detailTabs, "Title", "Build Log");
        agentGrid = uigridlayout(agentTab, [2 1]);
        agentGrid.RowHeight = {26, "1x"};
        agentGrid.Padding = [10 10 10 10];
        handles.agentStatus = uilabel(agentGrid);
        handles.agentStatus.FontName = "Helvetica";
        handles.agentStatus.FontWeight = "bold";
        handles.agentStatus.Layout.Row = 1;
        handles.agentStatus.Layout.Column = 1;
        handles.agentOutput = makeOutputArea(agentGrid);
        handles.agentOutput.Layout.Row = 2;
        handles.agentOutput.Layout.Column = 1;

        modelTab = uitab(detailTabs, "Title", "Model Lab");
        modelGrid = uigridlayout(modelTab, [2 1]);
        modelGrid.RowHeight = {26, "1x"};
        modelGrid.Padding = [10 10 10 10];
        handles.modelStatus = uilabel(modelGrid);
        handles.modelStatus.FontName = "Helvetica";
        handles.modelStatus.FontWeight = "bold";
        handles.modelStatus.Layout.Row = 1;
        handles.modelStatus.Layout.Column = 1;
        handles.modelOutput = makeOutputArea(modelGrid);
        handles.modelOutput.Layout.Row = 2;
        handles.modelOutput.Layout.Column = 1;

        detailsTab = uitab(detailTabs, "Title", "Setup");
        detailsGrid = uigridlayout(detailsTab, [2 1]);
        detailsGrid.RowHeight = {"1x", 104};
        detailsGrid.Padding = [10 10 10 10];
        detailsGrid.RowSpacing = 8;
        handles.setupReport = makeSoftArea(detailsGrid, "Helvetica");
        handles.setupReport.Layout.Row = 1;
        handles.setupReport.Layout.Column = 1;
        handles.modelPathsDisplay = makeOutputArea(detailsGrid);
        handles.modelPathsDisplay.Layout.Row = 2;
        handles.modelPathsDisplay.Layout.Column = 1;

        actionCard = makeCard(grid, "Build Controls");
        actionCard.Layout.Row = [3 4];
        actionCard.Layout.Column = 5;
        actionGrid = uigridlayout(actionCard, [10 2]);
        actionGrid.RowHeight = {22, 34, 30, 22, 30, 34, 34, 22, 30, 34};
        actionGrid.ColumnWidth = {"1x", "1x"};
        actionGrid.Padding = [12 10 12 12];
        actionGrid.RowSpacing = 6;
        actionGrid.ColumnSpacing = 8;

        agentLabel = uilabel(actionGrid, "Text", "Build model");
        agentLabel.FontWeight = "bold";
        agentLabel.Layout.Row = 1;
        agentLabel.Layout.Column = [1 2];
        handles.generateTaskButton = uibutton(actionGrid, "Text", "Prepare Model", ...
            "ButtonPushedFcn", @(~, ~) onGenerateAgentTask());
        handles.generateTaskButton.Layout.Row = 2;
        handles.generateTaskButton.Layout.Column = 1;
        styleSecondary(handles.generateTaskButton);
        handles.runAgentButton = uibutton(actionGrid, "Text", "Build Model", ...
            "ButtonPushedFcn", @(~, ~) onRunAgent());
        handles.runAgentButton.Layout.Row = 2;
        handles.runAgentButton.Layout.Column = 2;
        stylePrimary(handles.runAgentButton);
        handles.openTaskButton = uibutton(actionGrid, "Text", "Open Task", ...
            "ButtonPushedFcn", @(~, ~) onOpenTask());
        handles.openTaskButton.Layout.Row = 3;
        handles.openTaskButton.Layout.Column = [1 2];
        styleSecondary(handles.openTaskButton);

        modelLabel = uilabel(actionGrid, "Text", "Model");
        modelLabel.FontWeight = "bold";
        modelLabel.Layout.Row = 4;
        modelLabel.Layout.Column = [1 2];
        handles.modelPathField = uieditfield(actionGrid, "text");
        handles.modelPathField.Layout.Row = 5;
        handles.modelPathField.Layout.Column = [1 2];
        handles.openModelButton = uibutton(actionGrid, "Text", "Open Model", ...
            "ButtonPushedFcn", @(~, ~) onOpenModel());
        handles.openModelButton.Layout.Row = 6;
        handles.openModelButton.Layout.Column = 1;
        styleSecondary(handles.openModelButton);
        handles.selectModelButton = uibutton(actionGrid, "Text", "Choose .slx", ...
            "ButtonPushedFcn", @(~, ~) onSelectModel());
        handles.selectModelButton.Layout.Row = 6;
        handles.selectModelButton.Layout.Column = 2;
        styleSecondary(handles.selectModelButton);
        handles.checkModelButton = uibutton(actionGrid, "Text", "Check Model", ...
            "ButtonPushedFcn", @(~, ~) onCheckModel());
        handles.checkModelButton.Layout.Row = 7;
        handles.checkModelButton.Layout.Column = 1;
        styleSecondary(handles.checkModelButton);

        labLabel = uilabel(actionGrid, "Text", "Lab command");
        labLabel.FontWeight = "bold";
        labLabel.Layout.Row = 8;
        labLabel.Layout.Column = 1;
        handles.bodeButton = uibutton(actionGrid, "Text", "Bode Plot", ...
            "ButtonPushedFcn", @(~, ~) onRunBodeAnalysis());
        handles.bodeButton.Tooltip = "Generate available Bode/frequency-response evidence from spec, op-amp profile, or Simulink linearization I/O.";
        handles.bodeButton.Layout.Row = 8;
        handles.bodeButton.Layout.Column = 2;
        styleSecondary(handles.bodeButton);
        handles.runSimulationButton = uibutton(actionGrid, "Text", "Run Simulation", ...
            "ButtonPushedFcn", @(~, ~) onRunSimulation());
        handles.runSimulationButton.Layout.Row = 7;
        handles.runSimulationButton.Layout.Column = 2;
        styleSecondary(handles.runSimulationButton);
        handles.commandField = uieditfield(actionGrid, "text");
        handles.commandField.Tooltip = "Examples: open Data Inspector, bode plot, clear highlights, highlight feedback loop, probe clamp current.";
        handles.commandField.Layout.Row = 9;
        handles.commandField.Layout.Column = [1 2];
        handles.runCommandButton = uibutton(actionGrid, "Text", "Run Command", ...
            "ButtonPushedFcn", @(~, ~) onRunCommand());
        handles.runCommandButton.Layout.Row = 10;
        handles.runCommandButton.Layout.Column = 1;
        styleSecondary(handles.runCommandButton);

        handles.refreshSetupButton = uibutton(actionGrid, "Text", "Refresh Setup", ...
            "ButtonPushedFcn", @(~, ~) onRefreshSetup());
        handles.refreshSetupButton.Layout.Row = 10;
        handles.refreshSetupButton.Layout.Column = 2;
        styleSecondary(handles.refreshSetupButton);
    end

    function buildTeachTab(parent)
        tab = makeWorkflowPage(parent);
        handles.teachTab = tab;
        grid = uigridlayout(tab, [1 3]);
        grid.RowHeight = {"1x"};
        grid.ColumnWidth = {240, "1x", 240};
        grid.Padding = [18 16 18 16];
        grid.RowSpacing = 12;
        grid.ColumnSpacing = 12;
        enableScroll(grid);

        stepsCard = makeCard(grid, "Lesson Steps");
        stepsCard.Layout.Row = 1;
        stepsCard.Layout.Column = 1;
        stepsGrid = uigridlayout(stepsCard, [3 1]);
        stepsGrid.RowHeight = {36, "1x", 42};
        stepsGrid.Padding = [12 10 12 12];
        stepsGrid.RowSpacing = 8;
        handles.startTeachingButton = uibutton(stepsGrid, "Text", "Start Teaching", ...
            "ButtonPushedFcn", @(~, ~) onStartTeaching());
        stylePrimary(handles.startTeachingButton);
        handles.startTeachingButton.Layout.Row = 1;
        handles.startTeachingButton.Layout.Column = 1;
        handles.lessonStepsDisplay = makeSoftArea(stepsGrid, "Helvetica");
        handles.lessonStepsDisplay.Layout.Row = 2;
        handles.lessonStepsDisplay.Layout.Column = 1;
        stepsNote = uilabel(stepsGrid, "Text", "Answer, hint, focus, reveal");
        stepsNote.FontSize = 11;
        stepsNote.FontColor = [0.31 0.36 0.33];
        try
            stepsNote.WordWrap = "on";
        catch
        end
        stepsNote.Layout.Row = 3;
        stepsNote.Layout.Column = 1;

        questionCard = makeCard(grid, "Socratic Question");
        questionCard.Layout.Row = 1;
        questionCard.Layout.Column = 2;
        questionGrid = uigridlayout(questionCard, [8 3]);
        questionGrid.RowHeight = {34, "1x", 22, 78, 30, 58, 34, 92};
        questionGrid.ColumnWidth = {86, "1x", 128};
        questionGrid.Padding = [12 10 12 12];
        questionGrid.RowSpacing = 8;
        questionGrid.ColumnSpacing = 8;
        enableScroll(questionGrid);
        handles.currentStepDisplay = makeSoftArea(questionGrid, "Helvetica");
        handles.currentStepDisplay.Layout.Row = [1 2];
        handles.currentStepDisplay.Layout.Column = [1 3];

        answerLabel = uilabel(questionGrid, "Text", "Student answer");
        answerLabel.FontWeight = "bold";
        answerLabel.Layout.Row = 3;
        answerLabel.Layout.Column = [1 3];
        handles.studentAnswer = uitextarea(questionGrid);
        handles.studentAnswer.ValueChangedFcn = @(~, ~) updateLatexPreviews();
        handles.studentAnswer.Layout.Row = 4;
        handles.studentAnswer.Layout.Column = [1 3];

        uilabel(questionGrid, "Text", "Image");
        handles.studentImageField = uieditfield(questionGrid, "text");
        handles.studentImageField.Layout.Row = 5;
        handles.studentImageField.Layout.Column = 2;
        handles.selectStudentImageButton = uibutton(questionGrid, "Text", "Browse", ...
            "ButtonPushedFcn", @(~, ~) onSelectTeachingImage());
        handles.selectStudentImageButton.Layout.Row = 5;
        handles.selectStudentImageButton.Layout.Column = 3;
        styleSecondary(handles.selectStudentImageButton);

        handles.studentLatexPreview = makeLatexPreview(questionGrid, "LaTeX preview");
        handles.studentLatexPreview.Layout.Row = 6;
        handles.studentLatexPreview.Layout.Column = [1 3];

        handles.nextHintButton = uibutton(questionGrid, "Text", "Next Hint", ...
            "ButtonPushedFcn", @(~, ~) onNextHint());
        handles.nextHintButton.Layout.Row = 7;
        handles.nextHintButton.Layout.Column = [1 2];
        styleSecondary(handles.nextHintButton);
        handles.revealButton = uibutton(questionGrid, "Text", "Reveal", ...
            "ButtonPushedFcn", @(~, ~) onReveal());
        handles.revealButton.Layout.Row = 7;
        handles.revealButton.Layout.Column = 3;
        styleSecondary(handles.revealButton);

        handles.teachOutput = makeSoftArea(questionGrid, "Helvetica");
        handles.teachOutput.Layout.Row = 8;
        handles.teachOutput.Layout.Column = [1 3];

        focusCard = makeCard(grid, "Model Focus Actions");
        focusCard.Layout.Row = 1;
        focusCard.Layout.Column = 3;
        focusGrid = uigridlayout(focusCard, [8 1]);
        focusGrid.RowHeight = {24, 32, 38, 38, 24, 26, "1x", 34};
        focusGrid.Padding = [12 10 12 12];
        focusGrid.RowSpacing = 8;
        focusLabel = uilabel(focusGrid, "Text", "Focus");
        focusLabel.FontWeight = "bold";
        focusLabel.Layout.Row = 1;
        focusLabel.Layout.Column = 1;
        handles.focusSelector = uidropdown(focusGrid, "Items", "");
        handles.focusSelector.Layout.Row = 2;
        handles.focusSelector.Layout.Column = 1;
        handles.highlightButton = uibutton(focusGrid, "Text", "Highlight in Model", ...
            "ButtonPushedFcn", @(~, ~) onHighlightCurrent());
        handles.highlightButton.Layout.Row = 3;
        handles.highlightButton.Layout.Column = 1;
        stylePrimary(handles.highlightButton);
        handles.zoomButton = uibutton(focusGrid, "Text", "Zoom to Focus", ...
            "ButtonPushedFcn", @(~, ~) onZoomCurrent());
        handles.zoomButton.Layout.Row = 4;
        handles.zoomButton.Layout.Column = 1;
        styleSecondary(handles.zoomButton);
        statusLabelTeach = uilabel(focusGrid, "Text", "Tutor status");
        statusLabelTeach.FontWeight = "bold";
        statusLabelTeach.Layout.Row = 5;
        statusLabelTeach.Layout.Column = 1;
        handles.teachStatus = uilabel(focusGrid);
        handles.teachStatus.Text = "Waiting for teaching plan";
        handles.teachStatus.FontName = "Helvetica";
        handles.teachStatus.Layout.Row = 6;
        handles.teachStatus.Layout.Column = 1;
        focusHelp = uitextarea(focusGrid);
        focusHelp.Editable = "off";
        focusHelp.FontName = "Helvetica";
        focusHelp.Value = [
            "Use Highlight and Zoom after the student commits an answer."
            "This links the lesson step to the generated model."
            ];
        focusHelp.Layout.Row = 7;
        focusHelp.Layout.Column = 1;
        handles.clearTeachingButton = uibutton(focusGrid, "Text", "Clear Highlights", ...
            "ButtonPushedFcn", @(~, ~) onRunNaturalClearHighlights());
        handles.clearTeachingButton.Layout.Row = 8;
        handles.clearTeachingButton.Layout.Column = 1;
        styleSecondary(handles.clearTeachingButton);
    end

    function buildProbeTab(parent)
        tab = makeWorkflowPage(parent);
        handles.probeTab = tab;
        grid = uigridlayout(tab, [2 2]);
        grid.RowHeight = {205, "1x"};
        grid.ColumnWidth = {"1x", "1x"};
        grid.Padding = [18 16 18 16];
        grid.RowSpacing = 12;
        grid.ColumnSpacing = 12;
        enableScroll(grid);

        probeCard = makeCard(grid, "Probe the Model");
        probeCard.Layout.Row = 1;
        probeCard.Layout.Column = 1;
        probeGrid = uigridlayout(probeCard, [4 4]);
        probeGrid.RowHeight = {28, 34, 34, "1x"};
        probeGrid.ColumnWidth = {96, "1x", 124, 124};
        probeGrid.Padding = [12 10 12 12];
        probeGrid.RowSpacing = 8;
        probeGrid.ColumnSpacing = 8;
        uilabel(probeGrid, "Text", "Focus / probe");
        handles.probeSelector = uidropdown(probeGrid, "Items", "");
        handles.probeSelector.Layout.Row = 1;
        handles.probeSelector.Layout.Column = [2 4];
        handles.addProbeButton = uibutton(probeGrid, "Text", "Place Probe", ...
            "ButtonPushedFcn", @(~, ~) onAddProbe());
        handles.addProbeButton.Layout.Row = 2;
        handles.addProbeButton.Layout.Column = [2 3];
        stylePrimary(handles.addProbeButton);
        handles.probeStatus = uilabel(probeGrid);
        handles.probeStatus.FontName = "Helvetica";
        handles.probeStatus.FontWeight = "bold";
        handles.probeStatus.Layout.Row = 3;
        handles.probeStatus.Layout.Column = [1 4];
        probeHelp = uitextarea(probeGrid);
        probeHelp.Editable = "off";
        probeHelp.FontName = "Helvetica";
        probeHelp.Value = [
            "Probe the controlled output, feedback path, or measured node before changing parameters."
            "CiTT will use the generated probe map, then highlight or add logging in Simulink."
            ];
        probeHelp.Layout.Row = 4;
        probeHelp.Layout.Column = [1 4];

        deltaCard = makeCard(grid, "Explain Lab Delta");
        deltaCard.Layout.Row = 1;
        deltaCard.Layout.Column = 2;
        deltaGrid = uigridlayout(deltaCard, [5 4]);
        deltaGrid.RowHeight = {28, 28, 34, 28, "1x"};
        deltaGrid.ColumnWidth = {76, "1x", 124, 124};
        deltaGrid.Padding = [12 10 12 12];
        deltaGrid.RowSpacing = 8;
        deltaGrid.ColumnSpacing = 8;
        uilabel(deltaGrid, "Text", "Lab CSV");
        handles.labCsvField = uieditfield(deltaGrid, "text");
        handles.labCsvField.Layout.Row = 1;
        handles.labCsvField.Layout.Column = 2;
        handles.selectCsvButton = uibutton(deltaGrid, "Text", "Select CSV", ...
            "ButtonPushedFcn", @(~, ~) onSelectCsv());
        handles.selectCsvButton.Layout.Row = 1;
        handles.selectCsvButton.Layout.Column = 3;
        styleSecondary(handles.selectCsvButton);
        handles.compareDeltaButton = uibutton(deltaGrid, "Text", "Compare", ...
            "ButtonPushedFcn", @(~, ~) onCompareLabDelta());
        handles.compareDeltaButton.Layout.Row = 1;
        handles.compareDeltaButton.Layout.Column = 4;
        styleSecondary(handles.compareDeltaButton);
        uilabel(deltaGrid, "Text", "Op-amp");
        handles.opAmpPartField = uieditfield(deltaGrid, "text", ...
            "Value", char(fieldText(state, "OpAmpPart")));
        handles.opAmpPartField.Tooltip = "Optional op-amp part number for nonideal lab-error diagnosis, for example LM741.";
        handles.opAmpPartField.Layout.Row = 2;
        handles.opAmpPartField.Layout.Column = [2 4];
        handles.analyzeLabErrorButton = uibutton(deltaGrid, "Text", "Analyze Error", ...
            "ButtonPushedFcn", @(~, ~) onAnalyzeLabError());
        handles.analyzeLabErrorButton.Tooltip = "Diagnose lab-vs-simulation error using the CSV, probe map, spec assumptions, model check, and simulation status.";
        handles.analyzeLabErrorButton.Layout.Row = 3;
        handles.analyzeLabErrorButton.Layout.Column = [3 4];
        stylePrimary(handles.analyzeLabErrorButton);
        handles.deltaStatus = uilabel(deltaGrid);
        handles.deltaStatus.FontName = "Helvetica";
        handles.deltaStatus.FontWeight = "bold";
        handles.deltaStatus.Layout.Row = 4;
        handles.deltaStatus.Layout.Column = [1 4];
        deltaHelp = uitextarea(deltaGrid);
        deltaHelp.Editable = "off";
        deltaHelp.FontName = "Helvetica";
        deltaHelp.Value = [
            "Compare lab data against simulation, then identify likely causes and the next experiment."
            "Use this after the first probe so the delta is tied to model evidence."
            ];
        deltaHelp.Layout.Row = 5;
        deltaHelp.Layout.Column = [1 4];

        resultTabs = uitabgroup(grid);
        resultTabs.Layout.Row = 2;
        resultTabs.Layout.Column = [1 2];
        probeResultTab = uitab(resultTabs, "Title", "Probe Result");
        probeResultGrid = uigridlayout(probeResultTab, [1 1]);
        probeResultGrid.Padding = [10 10 10 10];
        handles.probeOutput = makeSoftArea(probeResultGrid, "Helvetica");
        handles.probeOutput.Layout.Row = 1;
        handles.probeOutput.Layout.Column = 1;
        deltaResultTab = uitab(resultTabs, "Title", "Lab Delta");
        deltaResultGrid = uigridlayout(deltaResultTab, [1 1]);
        deltaResultGrid.Padding = [10 10 10 10];
        handles.deltaOutput = makeSoftArea(deltaResultGrid, "Helvetica");
        handles.deltaOutput.Layout.Row = 1;
        handles.deltaOutput.Layout.Column = 1;
    end

    function buildEvidenceTab(parent)
        tab = makeWorkflowPage(parent);
        handles.evidenceTab = tab;
        grid = uigridlayout(tab, [4 4]);
        grid.RowHeight = {76, 154, 192, "1x"};
        grid.ColumnWidth = {"1x", "1x", "1x", "1x"};
        grid.Padding = [18 16 18 16];
        grid.RowSpacing = 12;
        grid.ColumnSpacing = 12;
        enableScroll(grid);

        packCard = makeCard(grid, "Competition Package");
        packCard.Layout.Row = 1;
        packCard.Layout.Column = [1 4];
        packGrid = uigridlayout(packCard, [2 6]);
        packGrid.RowHeight = {28, 34};
        packGrid.ColumnWidth = {90, "1x", 150, 150, 150, 130};
        packGrid.Padding = [12 8 12 10];
        packGrid.RowSpacing = 6;
        packGrid.ColumnSpacing = 8;
        uilabel(packGrid, "Text", "Pack path");
        handles.evidencePathField = uieditfield(packGrid, "text");
        handles.evidencePathField.Layout.Row = 1;
        handles.evidencePathField.Layout.Column = [2 6];
        handles.evidenceStatus = uilabel(packGrid);
        handles.evidenceStatus.FontName = "Helvetica";
        handles.evidenceStatus.FontWeight = "bold";
        handles.evidenceStatus.Layout.Row = 2;
        handles.evidenceStatus.Layout.Column = [1 3];
        handles.exportEvidenceButton = uibutton(packGrid, "Text", "Export BMES Evidence Pack", ...
            "ButtonPushedFcn", @(~, ~) onExportEvidencePack());
        handles.exportEvidenceButton.Layout.Row = 2;
        handles.exportEvidenceButton.Layout.Column = [4 5];
        stylePrimary(handles.exportEvidenceButton);
        handles.openEvidenceButton = uibutton(packGrid, "Text", "Open Pack", ...
            "ButtonPushedFcn", @(~, ~) onOpenEvidencePack());
        handles.openEvidenceButton.Tooltip = "Open the generated evidence pack.";
        handles.openEvidenceButton.Layout.Row = 2;
        handles.openEvidenceButton.Layout.Column = 6;
        styleSecondary(handles.openEvidenceButton);

        proofCard = makeCard(grid, "Functional Proof");
        proofCard.Layout.Row = 2;
        proofCard.Layout.Column = 1;
        proofGrid = uigridlayout(proofCard, [5 1]);
        proofGrid.RowHeight = {34, 34, 26, "1x", 28};
        proofGrid.Padding = [12 10 12 12];
        proofGrid.RowSpacing = 8;
        handles.requirementsButton = uibutton(proofGrid, "Text", "Requirements", ...
            "ButtonPushedFcn", @(~, ~) onRunRequirements());
        handles.requirementsButton.Tooltip = "Export the requirement-to-simulation pass/fail table.";
        handles.requirementsButton.Layout.Row = 1;
        handles.requirementsButton.Layout.Column = 1;
        stylePrimary(handles.requirementsButton);
        handles.openVerificationReportButton = uibutton(proofGrid, "Text", "Open Report", ...
            "ButtonPushedFcn", @(~, ~) onOpenLastVerificationReport());
        handles.openVerificationReportButton.Tooltip = "Open the latest generated verification report.";
        handles.openVerificationReportButton.Layout.Row = 2;
        handles.openVerificationReportButton.Layout.Column = 1;
        styleSecondary(handles.openVerificationReportButton);
        handles.verificationStatus = uilabel(proofGrid);
        handles.verificationStatus.FontName = "Helvetica";
        handles.verificationStatus.FontWeight = "bold";
        handles.verificationStatus.Layout.Row = 3;
        handles.verificationStatus.Layout.Column = 1;
        proofText = uitextarea(proofGrid);
        proofText.Editable = "off";
        proofText.FontName = "Helvetica";
        proofText.Value = [
            "Shows prototype proof with requirement pass/fail evidence."
            "Use after model check and simulation."
            ];
        proofText.Layout.Row = 4;
        proofText.Layout.Column = 1;

        perfCard = makeCard(grid, "Performance and Limitations");
        perfCard.Layout.Row = 2;
        perfCard.Layout.Column = [2 3];
        perfGrid = uigridlayout(perfCard, [4 4]);
        perfGrid.RowHeight = {34, 34, 34, "1x"};
        perfGrid.ColumnWidth = {"1x", 112, 112, 112};
        perfGrid.Padding = [12 10 12 12];
        perfGrid.RowSpacing = 8;
        perfGrid.ColumnSpacing = 8;
        handles.sweepButton = uibutton(perfGrid, "Text", "Sweep", ...
            "ButtonPushedFcn", @(~, ~) onRunSweep());
        handles.sweepButton.Tooltip = "Run the RC tolerance sweep report.";
        handles.sweepButton.Layout.Row = 1;
        handles.sweepButton.Layout.Column = 1;
        styleSecondary(handles.sweepButton);
        handles.faultButton = uibutton(perfGrid, "Text", "Faults", ...
            "ButtonPushedFcn", @(~, ~) onRunFaults());
        handles.faultButton.Tooltip = "Export educational fault-injection scenarios.";
        handles.faultButton.Layout.Row = 1;
        handles.faultButton.Layout.Column = 2;
        styleSecondary(handles.faultButton);
        handles.buildExplainabilityButton = uibutton(perfGrid, "Text", "Map", ...
            "ButtonPushedFcn", @(~, ~) onBuildExplainability());
        handles.buildExplainabilityButton.Tooltip = "Build the explainability action map from focus and probe artifacts.";
        handles.buildExplainabilityButton.Layout.Row = 1;
        handles.buildExplainabilityButton.Layout.Column = 3;
        styleSecondary(handles.buildExplainabilityButton);
        handles.highlightExplainabilityButton = uibutton(perfGrid, "Text", "Highlight", ...
            "ButtonPushedFcn", @(~, ~) onHighlightExplainability());
        handles.highlightExplainabilityButton.Tooltip = "Highlight the selected explainability action in Simulink.";
        handles.highlightExplainabilityButton.Layout.Row = 1;
        handles.highlightExplainabilityButton.Layout.Column = 4;
        styleSecondary(handles.highlightExplainabilityButton);
        uilabel(perfGrid, "Text", "Explain action");
        handles.explainSelector = uidropdown(perfGrid, "Items", "");
        handles.explainSelector.Layout.Row = 2;
        handles.explainSelector.Layout.Column = [2 4];
        perfText = uitextarea(perfGrid);
        perfText.Editable = "off";
        perfText.FontName = "Helvetica";
        perfText.Value = [
            "Collect sweep, fault, and explainability evidence."
            "These reports show actual performance, limitations, and traceability."
            ];
        perfText.Layout.Row = [3 4];
        perfText.Layout.Column = [1 4];

        econCard = makeCard(grid, "Economic and Scope");
        econCard.Layout.Row = 2;
        econCard.Layout.Column = 4;
        econGrid = uigridlayout(econCard, [5 2]);
        econGrid.RowHeight = {28, 34, 34, 34, "1x"};
        econGrid.ColumnWidth = {76, "1x"};
        econGrid.Padding = [12 10 12 12];
        econGrid.RowSpacing = 8;
        uilabel(econGrid, "Text", "Students");
        handles.studentsField = uieditfield(econGrid, "numeric", "Value", 30, "Limits", [1 10000]);
        handles.studentsField.Layout.Row = 1;
        handles.studentsField.Layout.Column = 2;
        handles.economicsButton = uibutton(econGrid, "Text", "Cost Plan", ...
            "ButtonPushedFcn", @(~, ~) onBuildEconomics());
        handles.economicsButton.Tooltip = "Export the deployment cost and licensing plan.";
        handles.economicsButton.Layout.Row = 2;
        handles.economicsButton.Layout.Column = [1 2];
        styleSecondary(handles.economicsButton);
        handles.scopeButton = uibutton(econGrid, "Text", "Scope Guardrail", ...
            "ButtonPushedFcn", @(~, ~) onBuildScopeGuardrail());
        handles.scopeButton.Tooltip = "Export educational/regulatory scope guardrails.";
        handles.scopeButton.Layout.Row = 3;
        handles.scopeButton.Layout.Column = [1 2];
        styleSecondary(handles.scopeButton);
        econText = uitextarea(econGrid);
        econText.Editable = "off";
        econText.FontName = "Helvetica";
        econText.Value = [
            "Budget, market fit, educational scope, and regulatory guardrails."
            ];
        econText.Layout.Row = [4 5];
        econText.Layout.Column = [1 2];

        learningCard = makeCard(grid, "Learning Evidence");
        learningCard.Layout.Row = 3;
        learningCard.Layout.Column = [1 2];
        learningGrid = uigridlayout(learningCard, [5 4]);
        learningGrid.RowHeight = {30, 56, 56, 26, 34};
        learningGrid.ColumnWidth = {72, "1x", 96, 112};
        learningGrid.Padding = [12 10 12 12];
        learningGrid.RowSpacing = 8;
        learningGrid.ColumnSpacing = 8;
        uilabel(learningGrid, "Text", "Concept");
        handles.assessmentConceptField = uieditfield(learningGrid, "text", ...
            "Value", "cutoff frequency output node");
        handles.assessmentConceptField.Layout.Row = 1;
        handles.assessmentConceptField.Layout.Column = 2;
        handles.hintLevelsField = uieditfield(learningGrid, "numeric", "Value", 0, "Limits", [0 10]);
        handles.hintLevelsField.Layout.Row = 1;
        handles.hintLevelsField.Layout.Column = 3;
        handles.assessmentButton = uibutton(learningGrid, "Text", "Assess", ...
            "ButtonPushedFcn", @(~, ~) onRunAssessment());
        handles.assessmentButton.Tooltip = "Export learning-gain evidence from before/after answers.";
        handles.assessmentButton.Layout.Row = 1;
        handles.assessmentButton.Layout.Column = 4;
        stylePrimary(handles.assessmentButton);
        uilabel(learningGrid, "Text", "Before");
        handles.beforeAnswerText = uitextarea(learningGrid);
        handles.beforeAnswerText.Layout.Row = 2;
        handles.beforeAnswerText.Layout.Column = [2 4];
        uilabel(learningGrid, "Text", "After");
        handles.afterAnswerText = uitextarea(learningGrid);
        handles.afterAnswerText.Layout.Row = 3;
        handles.afterAnswerText.Layout.Column = [2 4];
        handles.assessmentStatus = uilabel(learningGrid);
        handles.assessmentStatus.FontName = "Helvetica";
        handles.assessmentStatus.FontWeight = "bold";
        handles.assessmentStatus.Layout.Row = 4;
        handles.assessmentStatus.Layout.Column = [1 4];
        learningNote = uilabel(learningGrid, "Text", "Summarizes before/after reasoning and hint use for learning-gain evidence.");
        learningNote.FontSize = 11;
        learningNote.FontColor = [0.31 0.36 0.33];
        learningNote.Layout.Row = 5;
        learningNote.Layout.Column = [1 4];

        finalCard = makeCard(grid, "Final Package Contents");
        finalCard.Layout.Row = 3;
        finalCard.Layout.Column = [3 4];
        finalGrid = uigridlayout(finalCard, [1 1]);
        finalGrid.Padding = [12 10 12 12];
        handles.evidenceNotes = makeSoftArea(finalGrid, "Helvetica");
        handles.evidenceNotes.Layout.Row = 1;
        handles.evidenceNotes.Layout.Column = 1;

        detailTabs = uitabgroup(grid);
        detailTabs.Layout.Row = 4;
        detailTabs.Layout.Column = [1 4];

        verificationTab = uitab(detailTabs, "Title", "Proof Reports");
        verificationGrid = uigridlayout(verificationTab, [1 1]);
        verificationGrid.Padding = [10 10 10 10];
        handles.verificationOutput = makeOutputArea(verificationGrid);
        handles.verificationOutput.Layout.Row = 1;
        handles.verificationOutput.Layout.Column = 1;

        assessmentTab = uitab(detailTabs, "Title", "Plan Reports");
        assessmentGrid = uigridlayout(assessmentTab, [1 1]);
        assessmentGrid.Padding = [10 10 10 10];
        handles.assessmentOutput = makeOutputArea(assessmentGrid);
        handles.assessmentOutput.Layout.Row = 1;
        handles.assessmentOutput.Layout.Column = 1;

        packTab = uitab(detailTabs, "Title", "Evidence Pack");
        evidenceGrid = uigridlayout(packTab, [1 1]);
        evidenceGrid.Padding = [10 10 10 10];
        handles.evidenceOutput = makeOutputArea(evidenceGrid);
        handles.evidenceOutput.Layout.Row = 1;
        handles.evidenceOutput.Layout.Column = 1;

        reportsTab = uitab(detailTabs, "Title", "Artifact Index");
        reportsGrid = uigridlayout(reportsTab, [1 2]);
        reportsGrid.ColumnWidth = {"1x", "1x"};
        reportsGrid.Padding = [10 10 10 10];
        reportsGrid.ColumnSpacing = 10;
        handles.verificationReports = makeOutputArea(reportsGrid);
        handles.verificationReports.Layout.Row = 1;
        handles.verificationReports.Layout.Column = 1;
        handles.assessmentReports = makeOutputArea(reportsGrid);
        handles.assessmentReports.Layout.Row = 1;
        handles.assessmentReports.Layout.Column = 2;
    end

    function page = makeWorkflowPage(parent)
        page = uipanel(parent, "BorderType", "none");
        page.Layout.Row = 1;
        page.Layout.Column = 1;
        page.Visible = "off";
        try
            page.BackgroundColor = app.Figure.Color;
        catch
        end
    end

    function enableScroll(container)
        try
            container.Scrollable = "on";
        catch
        end
    end

    function panel = makeCard(parent, titleText)
        panel = uipanel(parent, "Title", char(titleText));
        try
            panel.BackgroundColor = palette.surface;
            panel.BorderType = "line";
            panel.FontWeight = "bold";
            panel.ForegroundColor = palette.text;
        catch
        end
    end

    function area = makeSoftArea(parent, fontName)
        area = uitextarea(parent);
        area.Editable = "off";
        area.FontName = fontName;
        area.Value = {""};
        try
            area.BackgroundColor = [1 1 1];
            area.FontSize = 12;
        catch
        end
    end

    function area = makeOutputArea(parent)
        area = makeSoftArea(parent, "Menlo");
    end

    function preview = makeLatexPreview(parent, fallbackText)
        htmlPath = fullfile(state.Config.MatlabRoot, "resources", "ui", "latex_preview.html");
        preview = uihtml(parent, "HTMLSource", htmlPath);
        try
            preview.Data = struct("latex", "", "placeholder", char(fallbackText));
        catch
        end
    end

    function label = makeStepCard(parent, titleText, row, column)
        panel = makeCard(parent, titleText);
        panel.Layout.Row = row;
        panel.Layout.Column = column;
        stepGrid = uigridlayout(panel, [2 1]);
        stepGrid.RowHeight = {22, "1x"};
        stepGrid.Padding = [10 8 10 10];
        stepGrid.RowSpacing = 4;
        titleLabelLocal = uilabel(stepGrid, "Text", titleText);
        titleLabelLocal.FontSize = 11;
        titleLabelLocal.FontWeight = "bold";
        titleLabelLocal.FontColor = [0.145 0.286 0.235];
        titleLabelLocal.Layout.Row = 1;
        titleLabelLocal.Layout.Column = 1;
        label = uilabel(stepGrid, "Text", "Not started");
        label.FontSize = 12;
        label.FontWeight = "bold";
        label.HorizontalAlignment = "center";
        label.Layout.Row = 2;
        label.Layout.Column = 1;
        try
            label.WordWrap = "on";
            setTone(label, "gray");
        catch
        end
    end

    function label = makeStatusChip(parent, initialText)
        label = uilabel(parent, "Text", char(initialText));
        label.HorizontalAlignment = "center";
        label.FontWeight = "bold";
        label.FontSize = 11;
        try
            label.WordWrap = "on";
        catch
        end
        setTone(label, "gray");
    end

    function label = makeStageChip(parent, initialText, destination)
        label = uibutton(parent, "Text", char(initialText), ...
            "ButtonPushedFcn", @(~, ~) selectWorkflowTab(destination));
        label.FontWeight = "bold";
        label.FontSize = 11;
        try
            label.HorizontalAlignment = "center";
        catch
        end
        setTone(label, "gray");
    end

    function stylePrimary(button)
        button.FontWeight = "bold";
        button.BackgroundColor = palette.primary;
        button.FontColor = [1 1 1];
    end

    function styleSecondary(button)
        try
            button.BackgroundColor = palette.soft;
            button.FontColor = palette.primaryDark;
        catch
        end
    end

    function setTone(component, tone)
        [bg, fg] = toneColors(tone);
        try
            component.BackgroundColor = bg;
            component.FontColor = fg;
        catch
        end
    end

    function [bg, fg] = toneColors(tone)
        switch string(tone)
            case "green"
                bg = [0.82 0.93 0.86];
                fg = [0.04 0.24 0.13];
            case "yellow"
                bg = [0.99 0.91 0.68];
                fg = [0.32 0.22 0.04];
            case "red"
                bg = [0.96 0.82 0.82];
                fg = [0.38 0.07 0.07];
            case "blue"
                bg = [0.83 0.90 0.98];
                fg = [0.05 0.18 0.36];
            otherwise
                bg = [0.91 0.93 0.92];
                fg = [0.22 0.27 0.24];
        end
    end

    function onSelectImage()
        [file, folder] = uigetfile({"*.png;*.jpg;*.jpeg;*.gif;*.webp", "Circuit images"; "*.*", "All files"});
        if isequal(file, 0)
            return
        end
        state.ImagePath = string(fullfile(folder, file));
        refreshAll();
    end

    function onSelectTeachingImage()
        [file, folder] = uigetfile({"*.png;*.jpg;*.jpeg;*.gif;*.webp", "Student images"; "*.*", "All files"});
        if isequal(file, 0)
            return
        end
        state.TeachingImagePath = string(fullfile(folder, file));
        handles.studentImageField.Value = char(state.TeachingImagePath);
        setArea(handles.teachOutput, "Student image attached for the next hint or reveal." + newline + state.TeachingImagePath);
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
            setPipeline("Image ready. Next: Read Circuit.", 12);
            setArea(handles.inputStatus, "Image ready. Click Read Circuit when you are ready." + newline + savedPath);
        catch dropError
            setArea(handles.inputStatus, "Could not save dropped image: " + string(dropError.message));
            setPipeline("Image drop failed. Try another file.", 0);
        end
    end

    function onParseWithGemini()
        state.ImagePath = string(handles.imageField.Value);
        state.PromptText = textAreaText(handles.promptText);
        try
            setBusy("Reading circuit...", 25);
            progress = startProgress("Reading Circuit", "CiTT is parsing the image and prompt into a model spec.");
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
                setArea(handles.inputStatus, "No spec JSON exists yet. Read a circuit first.");
                return
            end
            edit(char(state.SpecPath));
        catch openError
            setArea(handles.inputStatus, "Could not open spec JSON: " + string(openError.message));
        end
    end

    function onNextAction()
        syncInputsFromUi();
        [~, action, destination] = nextActionForState(state);
        selectWorkflowTab(destination);
        switch action
            case "read"
                onParseWithGemini();
            case "prepare"
                onGenerateAgentTask();
            case "build"
                onRunAgent();
            case "check"
                onCheckModel();
            case "teach"
                onStartTeaching();
            case "export"
                onExportEvidencePack();
            otherwise
                refreshAll();
        end
    end

    function syncInputsFromUi()
        try
            state.ImagePath = string(handles.imageField.Value);
            state.PromptText = textAreaText(handles.promptText);
            state.ModelPath = string(handles.modelPathField.Value);
            state.LabCsvPath = string(handles.labCsvField.Value);
            state.EvidencePackPath = string(handles.evidencePathField.Value);
            if isfield(handles, "studentImageField")
                state.TeachingImagePath = string(handles.studentImageField.Value);
            end
        catch
        end
    end

    function selectWorkflowTab(destination)
        destination = string(destination);
        activeWorkflowPage = destination;
        pageNames = ["read", "build", "teach", "probe", "evidence"];
        pageHandles = {
            handles.readTab
            handles.buildTab
            handles.teachTab
            handles.probeTab
            handles.evidenceTab
        };
        for pageIndex = 1:numel(pageHandles)
            try
                if pageNames(pageIndex) == destination
                    pageHandles{pageIndex}.Visible = "on";
                else
                    pageHandles{pageIndex}.Visible = "off";
                end
            catch
            end
        end
        updateStageRail(state);
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
                "Next: edit the prompt with the missing/clarified values, then click Read Circuit again."
                "Spec saved at: " + parsed.spec_path
            ], newline);
        else
            text = strjoin([
                "Circuit read successfully."
                emptyText(notes, "Symbolic or omitted values will be kept as model parameters.")
                "Next: open Build, then click Prepare Build."
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
            setArea(handles.agentOutput, "Build brief ready. Build Model will hand this task to the configured SATK agent." + newline + generated.task_path);
            setPipeline("Build task ready. Next: Build Model.", 55);
        catch taskError
            setArea(handles.agentOutput, "Build preparation failed: " + string(taskError.message));
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

            setBusy("Starting SATK agent...", 68);
            progress = startProgress("Starting Agent", "CiTT is launching an SATK-enabled external agent, then freeing MATLAB for MCP tool calls.");
            cleanup = onCleanup(@() finishProgress(progress));
            runResult = feval('citt.runAgentTask', state.AgentTaskPath, struct("SpecPath", state.SpecPath, "Async", true));
            state.AgentRun = runResult;
            applyAgentRunState(runResult);
            if fieldText(runResult, "mode") == "external_agent_pending"
                startAgentPollTimer();
            else
                stopAgentPollTimer();
            end
        catch runError
            handles.agentStatus.Text = "Build failed";
            setArea(handles.agentOutput, "Model build failed: " + string(runError.message));
            setPipeline("Build failed. See Agent Output.", 55);
        end
        setIdle();
    end

    function startAgentPollTimer()
        stopAgentPollTimer();
        agentPollTimer = timer( ...
            "ExecutionMode", "fixedSpacing", ...
            "Period", 5, ...
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
                setIdle();
            end
        catch pollError
            stopAgentPollTimer();
            handles.agentStatus.Text = "Agent status failed";
            setArea(handles.agentOutput, "Could not poll external agent: " + string(pollError.message));
            setPipeline("Agent status failed. See Agent Output.", 58);
            setIdle();
        end
    end

    function applyAgentRunState(runResult)
        runResult = reconcileAgentRunArtifacts(runResult);
        state.AgentRun = runResult;
        if strlength(fieldText(runResult, "produced_model_path")) > 0 && isTruthy(fieldText(runResult, "success"))
            state.ModelPath = runResult.produced_model_path;
        end
        refreshAll();
        setArea(handles.agentOutput, agentRunSummary(runResult));

        mode = fieldText(runResult, "mode");
        if mode == "external_agent_pending"
            handles.agentStatus.Text = "Agent running";
            setPipeline("Agent running. MATLAB is free for MCP/SATK tool calls.", 68);
        elseif isTruthy(fieldText(runResult, "success"))
            if mode == "local_fallback"
                handles.agentStatus.Text = "Local Simscape model built";
                setPipeline("Local Simscape model built. Next: Check or Simulate.", 78);
            else
                handles.agentStatus.Text = "Model built by SATK agent";
                setPipeline("Model built by agent. Next: Check or Simulate.", 78);
            end
        elseif mode == "manual_agent"
            handles.agentStatus.Text = "Manual agent required";
            setPipeline("Manual agent task opened. Run it in an SATK-configured agent.", 58);
        else
            handles.agentStatus.Text = "Build incomplete";
            setPipeline("Build incomplete. See Agent Output.", 58);
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

    function onRunBodeAnalysis()
        state.ModelPath = string(handles.modelPathField.Value);
        try
            setBusy("Building Bode analysis...", 92);
            bode = feval('citt.runBodeAnalysis', state);
            state.LastBode = bode;
            handles.modelStatus.Text = "Bode analysis complete";
            setArea(handles.modelOutput, bodeSummary(bode));
            setPipeline("Bode analysis ready.", 94);
        catch bodeError
            handles.modelStatus.Text = "Bode analysis failed";
            setArea(handles.modelOutput, "Bode analysis failed: " + string(bodeError.message));
            setPipeline("Bode analysis failed. Check spec values or I/O points.", 84);
        end
        setIdle();
    end

    function onRunCommand()
        state.ModelPath = string(handles.modelPathField.Value);
        commandText = string(handles.commandField.Value);
        try
            setBusy("Running command...", 86);
            commandResult = feval('citt.runNaturalCommand', commandText, state);
            handles.modelStatus.Text = commandResult.message;
            setArea(handles.modelOutput, feval('citt.util.jsonEncode', commandResult));
            setPipeline("Command complete: " + commandResult.action, 90);
        catch commandError
            handles.modelStatus.Text = "Command failed";
            setArea(handles.modelOutput, "Command failed: " + string(commandError.message));
            setPipeline("Command failed. Try a more direct phrase.", 78);
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
            syncInputsFromUi();
            validateTeachingImage();
            setBusy("Reading student answer...", 92);
            progress = startProgress("Socratic Hint", "Gemini is classifying the answer and preparing one local hint.");
            cleanup = onCleanup(@() finishProgress(progress));
            answer = teachingSubmissionText();
            turn = feval('citt.runSocraticTurn', state.TeachingPlan, state.TeachingStepIndex, answer, ...
                struct("Action", "hint", "HintLevel", state.HintLevel, "AnswerImagePath", state.TeachingImagePath));
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
        try
            syncInputsFromUi();
            validateTeachingImage();
            turn = feval('citt.runSocraticTurn', state.TeachingPlan, state.TeachingStepIndex, teachingSubmissionText(), ...
                struct("Action", "reveal", "AnswerImagePath", state.TeachingImagePath));
            handles.teachStatus.Text = "Reveal shown for " + turn.step_id;
            setArea(handles.teachOutput, turn.message);
        catch revealError
            setArea(handles.teachOutput, "Reveal failed: " + string(revealError.message));
        end
    end

    function onHighlightCurrent()
        focusId = string(handles.focusSelector.Value);
        highlighted = feval('citt.highlightFocus', state.ModelPath, state.FocusMapPath, focusId);
        handles.teachStatus.Text = "Highlighted: " + string(highlighted.success);
        setArea(handles.teachOutput, focusActionSummary("Highlight", highlighted));
    end

    function onZoomCurrent()
        focusId = string(handles.focusSelector.Value);
        zoomed = feval('citt.zoomToFocus', state.ModelPath, state.FocusMapPath, focusId);
        handles.teachStatus.Text = zoomed.message;
        setArea(handles.teachOutput, focusActionSummary("Zoom", zoomed));
    end

    function onRunNaturalClearHighlights()
        try
            cleared = feval('citt.clearHighlights', state.ModelPath);
            handles.teachStatus.Text = "Highlights cleared";
            setArea(handles.teachOutput, "Model focus cleared." + newline + "Model: " + fieldText(cleared, "model_name"));
        catch clearError
            handles.teachStatus.Text = "Clear failed";
            setArea(handles.teachOutput, "Could not clear highlights: " + string(clearError.message));
        end
    end

    function onAddProbe()
        targetId = string(handles.probeSelector.Value);
        probed = feval('citt.addProbe', state.ModelPath, targetId, state.ProbeMapPath, state.SpecPath);
        state.LastProbe = probed;
        refreshAll();
        handles.probeStatus.Text = "Probe plan success: " + string(probed.success);
        setArea(handles.probeOutput, probePlanSummary(probed));
        setPipeline("Probe ready. Next: compare lab delta or export evidence.", 100);
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
        state.OpAmpPart = string(handles.opAmpPartField.Value);
        try
            delta = feval('citt.compareLabDelta', struct(), struct(), state.LabCsvPath, struct("Context", state));
            state.LastLabDelta = delta;
            handles.deltaStatus.Text = "Lab error rows: " + string(numel(delta.rows)) + ...
                " | causes: " + string(numel(delta.likely_causes));
            setArea(handles.deltaOutput, labErrorSummary(delta));
            setPipeline("Lab delta comparison ready.", 100);
        catch deltaError
            setArea(handles.deltaOutput, "Lab Delta failed: " + string(deltaError.message));
        end
    end

    function onAnalyzeLabError()
        state.LabCsvPath = string(handles.labCsvField.Value);
        state.OpAmpPart = string(handles.opAmpPartField.Value);
        try
            setBusy("Analyzing lab error...", 94);
            analyzed = feval('citt.analyzeLabError', state.LabCsvPath, state);
            state.LastLabDelta = analyzed;
            handles.deltaStatus.Text = "Lab error causes: " + string(numel(analyzed.likely_causes));
            setArea(handles.deltaOutput, labErrorSummary(analyzed));
            setPipeline("Lab error analysis ready.", 100);
        catch labError
            handles.deltaStatus.Text = "Lab error analysis failed";
            setArea(handles.deltaOutput, "Lab error analysis failed: " + string(labError.message));
            setPipeline("Lab error analysis failed. Check CSV format.", 90);
        end
        setIdle();
    end

    function onRunRequirements()
        try
            setBusy("Checking requirements...", 96);
            checked = feval('citt.runRequirementChecks', state);
            state.LastRequirements = checked;
            handles.verificationStatus.Text = "Requirement check complete";
            setArea(handles.verificationOutput, requirementRunSummary(checked));
            refreshAll();
            setPipeline("Requirement table ready.", 100);
        catch requirementError
            handles.verificationStatus.Text = "Requirement check failed";
            setArea(handles.verificationOutput, "Requirement check failed: " + string(requirementError.message));
        end
        setIdle();
    end

    function onRunSweep()
        try
            setBusy("Running tolerance sweep...", 96);
            swept = feval('citt.runParameterSweep', state);
            state.LastSweep = swept;
            handles.verificationStatus.Text = "Sweep complete";
            setArea(handles.verificationOutput, sweepSummary(swept));
            refreshAll();
            setPipeline("Tolerance sweep ready.", 100);
        catch sweepError
            handles.verificationStatus.Text = "Sweep failed";
            setArea(handles.verificationOutput, "Sweep failed: " + string(sweepError.message));
        end
        setIdle();
    end

    function onRunFaults()
        try
            setBusy("Building fault scenarios...", 96);
            faults = feval('citt.runFaultInjection', state);
            state.LastFaults = faults;
            handles.verificationStatus.Text = "Fault scenarios ready";
            setArea(handles.verificationOutput, faultSummary(faults));
            refreshAll();
            setPipeline("Fault injection report ready.", 100);
        catch faultError
            handles.verificationStatus.Text = "Fault generation failed";
            setArea(handles.verificationOutput, "Fault generation failed: " + string(faultError.message));
        end
        setIdle();
    end

    function onBuildExplainability()
        try
            setBusy("Building explainability map...", 96);
            explained = feval('citt.buildExplainabilityMap', state);
            state.LastExplainability = explained;
            handles.verificationStatus.Text = "Explainability map ready";
            setArea(handles.verificationOutput, explainabilitySummary(explained));
            updateExplainabilitySelector();
            refreshAll();
            setPipeline("Explainability map ready.", 100);
        catch explainError
            handles.verificationStatus.Text = "Explainability map failed";
            setArea(handles.verificationOutput, "Explainability map failed: " + string(explainError.message));
        end
        setIdle();
    end

    function onHighlightExplainability()
        actionId = string(handles.explainSelector.Value);
        try
            highlighted = feval('citt.highlightExplainabilityAction', ...
                state.ModelPath, state.Config.ExplainabilityMapPath, actionId, state.FocusMapPath);
            handles.verificationStatus.Text = highlighted.message;
            setArea(handles.verificationOutput, feval('citt.util.jsonEncode', highlighted));
        catch highlightError
            handles.verificationStatus.Text = "Explainability highlight failed";
            setArea(handles.verificationOutput, "Explainability highlight failed: " + string(highlightError.message));
        end
    end

    function onOpenLastVerificationReport()
        path = lastVerificationMarkdownPath();
        if strlength(path) == 0 || exist(path, "file") ~= 2
            setArea(handles.verificationOutput, "No verification report exists yet.");
            return
        end
        edit(char(path));
    end

    function onRunAssessment()
        request = struct();
        request.concept = string(handles.assessmentConceptField.Value);
        request.before_answer = textAreaText(handles.beforeAnswerText);
        request.after_answer = textAreaText(handles.afterAnswerText);
        request.hint_levels_used = handles.hintLevelsField.Value;
        try
            setBusy("Scoring learning gain...", 96);
            assessed = feval('citt.runLearningAssessment', request);
            state.LastAssessment = assessed;
            handles.assessmentStatus.Text = "Assessment complete";
            setArea(handles.assessmentOutput, assessmentSummary(assessed));
            refreshAll();
            setPipeline("Assessment evidence ready.", 100);
        catch assessmentError
            handles.assessmentStatus.Text = "Assessment failed";
            setArea(handles.assessmentOutput, "Assessment failed: " + string(assessmentError.message));
        end
        setIdle();
    end

    function onBuildEconomics()
        try
            setBusy("Building cost plan...", 96);
            plan = feval('citt.buildEconomicsPlan', struct("Students", handles.studentsField.Value));
            state.LastEconomics = plan;
            handles.assessmentStatus.Text = "Cost plan ready";
            setArea(handles.assessmentOutput, economicsSummary(plan));
            refreshAll();
            setPipeline("Economics plan ready.", 100);
        catch economicsError
            handles.assessmentStatus.Text = "Cost plan failed";
            setArea(handles.assessmentOutput, "Cost plan failed: " + string(economicsError.message));
        end
        setIdle();
    end

    function onBuildScopeGuardrail()
        try
            setBusy("Building scope guardrail...", 96);
            guardrail = feval('citt.buildScopeGuardrail', state);
            state.LastScopeGuardrail = guardrail;
            handles.assessmentStatus.Text = "Scope guardrail ready";
            setArea(handles.assessmentOutput, scopeSummary(guardrail));
            refreshAll();
            setPipeline("Scope guardrail ready.", 100);
        catch scopeError
            handles.assessmentStatus.Text = "Scope guardrail failed";
            setArea(handles.assessmentOutput, "Scope guardrail failed: " + string(scopeError.message));
        end
        setIdle();
    end

    function onExportEvidencePack()
        state.EvidencePackPath = string(handles.evidencePathField.Value);
        try
            setBusy("Exporting evidence pack...", 100);
            progress = startProgress("Evidence Pack", "CiTT is collecting the current spec, model, checks, maps, probe data, and Lab Delta evidence.");
            cleanup = onCleanup(@() finishProgress(progress));
            exported = feval('citt.exportEvidencePack', state, struct("OutputPath", state.EvidencePackPath));
            state.LastEvidencePack = exported;
            refreshAll();
            handles.evidenceStatus.Text = "Evidence pack exported";
            setArea(handles.evidenceOutput, evidencePackSummary(exported));
            setArea(handles.evidenceNotes, exported.functional_proof_draft);
            setPipeline("Evidence pack exported.", 100);
        catch evidenceError
            handles.evidenceStatus.Text = "Evidence pack export failed";
            setArea(handles.evidenceOutput, "Evidence Pack failed: " + string(evidenceError.message));
            setPipeline("Evidence pack failed. See output.", 92);
        end
        setIdle();
    end

    function onOpenEvidencePack()
        state.EvidencePackPath = string(handles.evidencePathField.Value);
        try
            if exist(state.EvidencePackPath, "file") ~= 2
                setArea(handles.evidenceOutput, "No evidence pack exists yet. Click Export Evidence Pack first.");
                return
            end
            edit(char(state.EvidencePackPath));
        catch openError
            setArea(handles.evidenceOutput, "Could not open evidence pack: " + string(openError.message));
        end
    end

    function showCurrentStep()
        if isempty(state.TeachingPlan)
            setArea(handles.currentStepDisplay, "No teaching plan yet.");
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
        setArea(handles.currentStepDisplay, text);
        setArea(handles.teachOutput, string(step.student_question));
        setArea(handles.lessonStepsDisplay, teachingStepsText(state));
    end

    function updateFocusSelectors()
        focusItems = focusValues();
        if isempty(focusItems)
            focusItems = "";
        end
        focusItems = focusItems(:)';
        handles.focusSelector.Items = focusItems;
        handles.focusSelector.Value = focusItems(1);

        probeItems = probeValues();
        if isempty(probeItems)
            probeItems = "";
        end
        probeItems = probeItems(:)';
        handles.probeSelector.Items = probeItems;
        handles.probeSelector.Value = probeItems(1);
    end

    function updateExplainabilitySelector()
        values = explainabilityValues();
        if isempty(values)
            values = "";
        end
        values = values(:)';
        handles.explainSelector.Items = values;
        handles.explainSelector.Value = values(1);
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

    function refreshAll()
        reconcileStateArtifacts();

        statusLabel.Text = compactStatus(state);
        [nextLabel, ~, ~] = nextActionForState(state);
        handles.nextActionButton.Text = nextLabel;
        handles.imageField.Value = char(state.ImagePath);
        handles.modelPathField.Value = char(state.ModelPath);
        handles.labCsvField.Value = char(state.LabCsvPath);
        if isfield(handles, "studentImageField")
            handles.studentImageField.Value = char(fieldText(state, "TeachingImagePath"));
        end
        if isfield(handles, "opAmpPartField")
            handles.opAmpPartField.Value = char(fieldText(state, "OpAmpPart"));
        end
        handles.evidencePathField.Value = char(state.EvidencePackPath);
        updateSetupChips(state.LastSetupReport);
        setArea(handles.setupReport, setupOverviewText(state.LastSetupReport));
        handles.agentStatus.Text = "Task file: " + state.AgentTaskPath;
        handles.modelStatus.Text = "Model: " + state.ModelPath;
        setArea(handles.modelPathsDisplay, pathStatusText(state));
        setArea(handles.inputStatus, inputStatusText(state));
        setArea(handles.specDisplay, currentSpecPreview(state));
        setArea(handles.readinessDisplay, readinessSummaryText(state));
        setArea(handles.readAdvancedDisplay, readAdvancedText(state));
        updateBuildStepCards(state);
        setArea(handles.lessonStepsDisplay, teachingStepsText(state));
        setArea(handles.evidenceNotes, evidenceContentsText(state));
        setArea(handles.verificationReports, verificationReportText(state));
        setArea(handles.assessmentReports, assessmentReportText(state));
        updateStageRail(state);
        updatePipelineFromState(state);
        updateFocusSelectors();
        updateExplainabilitySelector();
        updateLatexPreviews();
    end

    function [label, action, destination] = nextActionForState(currentState)
        spec = currentSpecStruct(currentState);
        hasInput = strlength(strtrim(currentState.ImagePath)) > 0 || ...
            strlength(strtrim(currentState.PromptText)) > 0;
        if isempty(spec) && ~hasInput && exist(currentState.SpecPath, "file") ~= 2
            label = "Next: Add Input";
            action = "select";
            destination = "read";
            return
        end
        if isempty(spec) && exist(currentState.SpecPath, "file") ~= 2
            label = "Next: Read Circuit";
            action = "read";
            destination = "read";
            return
        end
        if ~isempty(spec)
            readiness = feval('citt.classifyBuildReadiness', spec);
            if ~readiness.build_ready
                label = "Next: Clarify Read";
                action = "select";
                destination = "read";
                return
            end
        end
        if ~agentTaskExists(currentState)
            label = "Next: Prepare Build";
            action = "prepare";
            destination = "build";
            return
        end
        if ~modelExists(currentState)
            label = "Next: Build Model";
            action = "build";
            destination = "build";
            return
        end
        if isempty(currentState.LastModelCheck)
            label = "Next: Check Model";
            action = "check";
            destination = "build";
            return
        end
        if isempty(currentState.TeachingPlan)
            label = "Next: Start Teaching";
            action = "teach";
            destination = "teach";
            return
        end
        if isempty(currentState.LastProbe)
            label = "Next: Probe Model";
            action = "select";
            destination = "probe";
            return
        end
        if isempty(currentState.LastLabDelta)
            label = "Next: Explain Delta";
            action = "select";
            destination = "probe";
            return
        end
        label = "Next: Export BMES Pack";
        action = "export";
        destination = "evidence";
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

    function updateSetupChips(setup)
        if isempty(setup)
            setStatusChip(handles.geminiChip, "Gemini", false, "not checked");
            setStatusChip(handles.satkChip, "SATK", false, "not checked");
            setStatusChip(handles.mcpChip, "MCP", false, "not checked");
            setStatusChip(handles.simscapeChip, "Simscape", false, "not checked");
            setStatusChip(handles.agentChip, "Agent", false, "not checked");
            return
        end
        setStatusChip(handles.geminiChip, "Parser", parserReady(setup), parserStatusText(setup));
        setStatusChip(handles.satkChip, "SATK", setup.satk_initialize_available, readyNeeds(setup.satk_initialize_available));
        setStatusChip(handles.mcpChip, "MCP", setup.matlab_mcp_available, readyNeeds(setup.matlab_mcp_available));
        setStatusChip(handles.simscapeChip, "Simscape", setup.simscape_available, readyNeeds(setup.simscape_available));
        setStatusChip(handles.agentChip, "Agent", setupAgentReady(setup), setupAgentText(setup));
    end

    function setStatusChip(label, name, ready, detail)
        if ready
            statusText = "ready";
            tone = "green";
        else
            statusText = "needs setup";
            tone = "yellow";
        end
        detail = string(detail);
        if strlength(strtrim(detail)) == 0
            detail = statusText;
        end
        label.Text = string(name) + ": " + detail;
        setTone(label, tone);
    end

    function ready = setupAgentReady(setup)
        ready = false;
        if isfield(setup, "configured_agent_command") && strlength(strtrim(setup.configured_agent_command)) > 0
            ready = true;
            return
        end
        if isfield(setup, "agent_clis")
            for i = 1:numel(setup.agent_clis)
                if isfield(setup.agent_clis(i), "available") && setup.agent_clis(i).available
                    ready = true;
                    return
                end
            end
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

    function text = readinessSummaryText(currentState)
        spec = currentSpecStruct(currentState);
        if isempty(spec)
            text = strjoin([
                "Build readiness: NOT STARTED"
                ""
                "Blocking issues"
                "- none yet"
                ""
                "Modeling assumptions"
                "- none yet"
                ""
                "Next action: Read Circuit"
            ], newline);
            return
        end

        readiness = feval('citt.classifyBuildReadiness', spec);
        notes = specBuildNotes(spec);
        if readiness.build_ready && strlength(strtrim(notes)) > 0
            badge = "PARAMETERIZED";
        elseif readiness.build_ready
            badge = "READY";
        else
            badge = "NEEDS CLARIFICATION";
        end

        if readiness.build_ready
            nextText = "Prepare Build";
        else
            nextText = "Clarify prompt, then read again";
        end

        text = strjoin([
            "Build readiness: " + badge
            ""
            "Blocking issues"
            emptyListText(readiness.blocking_text)
            ""
            "Modeling assumptions"
            emptyListText(notes)
            ""
            "Next action: " + nextText
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

    function updateBuildStepCards(currentState)
        spec = currentSpecStruct(currentState);
        if isempty(spec)
            setStepStatus(handles.buildStepSpec, "Waiting for Read", "gray");
        else
            setStepStatus(handles.buildStepSpec, "Ready" + newline + fileNameOnly(currentState.SpecPath), "green");
        end

        if agentTaskExists(currentState)
            setStepStatus(handles.buildStepTask, "Ready" + newline + fileNameOnly(currentState.AgentTaskPath), "green");
        else
            setStepStatus(handles.buildStepTask, "Prepare Model", "blue");
        end

        if ~isempty(currentState.AgentRun)
            mode = fieldText(currentState.AgentRun, "mode");
            if mode == "external_agent_pending"
                setStepStatus(handles.buildStepAgent, "Running", "blue");
            elseif isTruthy(fieldText(currentState.AgentRun, "success"))
                setStepStatus(handles.buildStepAgent, "Complete", "green");
            elseif mode == "manual_agent"
                setStepStatus(handles.buildStepAgent, "Manual agent needed", "yellow");
            else
                setStepStatus(handles.buildStepAgent, "Needs attention", "red");
            end
        else
            setStepStatus(handles.buildStepAgent, "Not started", "gray");
        end

        if modelExists(currentState)
            setStepStatus(handles.buildStepModel, "Available" + newline + fileNameOnly(currentState.ModelPath), "green");
        else
            setStepStatus(handles.buildStepModel, "Waiting for model", "gray");
        end

        if ~isempty(currentState.LastModelCheck)
            setStepStatus(handles.buildStepCheck, "Complete", "green");
        elseif modelExists(currentState)
            setStepStatus(handles.buildStepCheck, "Ready to check", "blue");
        else
            setStepStatus(handles.buildStepCheck, "Waiting for model", "gray");
        end
    end

    function setStepStatus(label, text, tone)
        label.Text = string(text);
        setTone(label, tone);
    end

    function updateStageRail(currentState)
        selected = pageIndexForName(activeWorkflowPage);
        completed = workflowStageIndex(currentState);
        stageLabels = {
            handles.stageRead
            handles.stageBuild
            handles.stageTeach
            handles.stageProbe
            handles.stageEvidence
        };
        names = ["Read", "Build", "Teach", "Probe", "Evidence"];
        for i = 1:numel(stageLabels)
            stageLabels{i}.Text = names(i);
            if i == selected
                setTone(stageLabels{i}, "blue");
            elseif i < completed
                setTone(stageLabels{i}, "green");
            else
                setTone(stageLabels{i}, "gray");
            end
        end
    end

    function index = pageIndexForName(pageName)
        names = ["read", "build", "teach", "probe", "evidence"];
        match = find(names == string(pageName), 1);
        if isempty(match)
            index = 1;
        else
            index = match;
        end
    end

    function index = workflowStageIndex(currentState)
        if ~isempty(currentState.LastEvidencePack)
            index = 5;
        elseif ~isempty(currentState.LastProbe) || ~isempty(currentState.LastLabDelta)
            index = 4;
        elseif ~isempty(currentState.TeachingPlan)
            index = 3;
        elseif ~isempty(currentState.AgentRun) || agentTaskExists(currentState) || modelExists(currentState) || ~isempty(currentState.LastModelCheck)
            index = 2;
        else
            index = 1;
        end
    end

    function text = teachingStepsText(currentState)
        if isempty(currentState.TeachingPlan)
            text = strjoin([
                "1. Identify command input"
                "2. Trace feedback path"
                "3. Explain output measurement"
                "4. Check modeling assumption"
                "5. Interpret simulation result"
                ""
                "Start Teaching will replace this with the generated lesson plan."
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

    function text = evidenceContentsText(currentState)
        if ~isempty(currentState.LastEvidencePack)
            text = strjoin([
                "Last exported evidence pack"
                "Pack: " + fieldText(currentState.LastEvidencePack, "pack_path")
                ""
                "Functional proof draft appears in the Markdown pack."
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
            ""
            "Next question: if this value differs from expectation, which part of the feedback path explains the error?"
        ], newline);
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

    function text = compactStatus(currentState)
        setup = currentState.LastSetupReport;
        text = "Parser " + readyNeeds(parserReady(setup)) + ...
            " | SATK " + readyNeeds(setup.satk_initialize_available) + ...
            " | Simscape " + readyNeeds(setup.simscape_available);
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
        agentText = "needs CLI";
        if strlength(strtrim(setup.configured_agent_command)) > 0
            agentText = "ready: CITT_AGENT_COMMAND";
        end
        for i = 1:numel(setup.agent_clis)
            if agentText == "needs CLI" && setup.agent_clis(i).available
                agentText = "ready: " + setup.agent_clis(i).name;
                break
            end
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

    function name = fileNameOnly(pathValue)
        [~, namePart, ext] = fileparts(char(pathValue));
        name = string(namePart) + string(ext);
    end

    function text = textAreaText(area)
        value = string(area.Value);
        text = strjoin(value(:), newline);
    end

    function setArea(area, text)
        area.Value = cellstr(splitlines(string(text)));
    end

    function updateLatexPreviews()
        try
            if isfield(handles, "promptLatexPreview")
                rawPrompt = textAreaText(handles.promptText);
                handles.promptLatexPreview.Data = struct( ...
                    "latex", char(latexPreviewText(rawPrompt)), ...
                    "html", char(htmlPreviewText(rawPrompt)));
            end
            if isfield(handles, "studentLatexPreview")
                rawAnswer = textAreaText(handles.studentAnswer);
                handles.studentLatexPreview.Data = struct( ...
                    "latex", char(latexPreviewText(rawAnswer)), ...
                    "html", char(htmlPreviewText(rawAnswer)));
            end
        catch
        end
    end

    function preview = latexPreviewText(rawText)
        rawText = string(rawText);
        formula = extractLatexFormula(rawText);
        if strlength(strtrim(formula)) == 0
            preview = "";
        else
            preview = formula;
        end
    end

    function html = htmlPreviewText(rawText)
        text = strtrim(string(rawText));
        html = "";
        if strlength(text) == 0
            return
        end

        fenced = regexp(char(text), '```html\s*([\s\S]*?)\s*```', 'tokens', 'once');
        if ~isempty(fenced)
            html = string(fenced{1});
            return
        end

        if startsWith(text, "<") && contains(text, ">")
            html = text;
        end
    end

    function formula = extractLatexFormula(rawText)
        text = char(string(rawText));
        token = regexp(text, '\$\$(.*?)\$\$', 'tokens', 'once');
        if isempty(token)
            token = regexp(text, '\$(.*?)\$', 'tokens', 'once');
        end
        if isempty(token)
            token = regexp(text, '\\\[(.*?)\\\]', 'tokens', 'once');
        end
        if ~isempty(token)
            formula = string(strtrim(token{1}));
            return
        end

        lines = splitlines(string(rawText));
        formula = "";
        for i = 1:numel(lines)
            candidate = strtrim(lines(i));
            if contains(candidate, "=") || contains(candidate, char(92)) || contains(candidate, "^") || contains(candidate, "_")
                formula = stripFormulaDelimiters(candidate);
                return
            end
        end
    end

    function formula = stripFormulaDelimiters(candidate)
        formula = string(candidate);
        formula = regexprep(formula, '^\s*\$\$?', '');
        formula = regexprep(formula, '\$\$?\s*$', '');
        formula = regexprep(formula, '^\s*\\\[', '');
        formula = regexprep(formula, '\\\]\s*$', '');
        formula = strtrim(formula);
    end

    function validateTeachingImage()
        imagePath = strtrim(string(fieldText(state, "TeachingImagePath")));
        if strlength(imagePath) > 0 && exist(imagePath, "file") ~= 2
            error("CiTT:TeachingImageMissing", "Teaching image not found: %s", imagePath);
        end
    end

    function answer = teachingSubmissionText()
        answer = textAreaText(handles.studentAnswer);
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
            "Drop or browse for an image, then click Read Circuit."
        ], newline);
    end

    function updatePipelineFromState(currentState)
        if ~isempty(currentState.LastSimulation)
            setPipeline("Simulation complete.", 100);
        elseif ~isempty(currentState.TeachingPlan)
            setPipeline("Teaching plan ready.", 92);
        elseif ~isempty(currentState.LastModelCheck)
            setPipeline("Model check complete.", 90);
        elseif modelExists(currentState)
            setPipeline("Model available. Next: Check.", 78);
        elseif ~isempty(currentState.AgentRun)
            setPipeline("Agent run complete. Check generated artifacts.", 70);
        elseif strlength(currentState.AgentTaskPath) > 0 && exist(currentState.AgentTaskPath, "file") == 2
            setPipeline("Build task ready. Next: Build Model.", 55);
        elseif ~isempty(currentState.Spec) || (strlength(currentState.SpecPath) > 0 && exist(currentState.SpecPath, "file") == 2)
            setPipeline("Circuit spec available. Next: Prepare Build.", 35);
        elseif strlength(currentState.ImagePath) > 0 || strlength(strtrim(currentState.PromptText)) > 0
            setPipeline("Input ready. Next: Read Circuit.", 12);
        else
            setPipeline("Ready for circuit input.", 0);
        end
    end

    function setPipeline(message, value)
        try
            pipelineLabel.Text = string(message);
            if nargin >= 2 && ~isempty(value)
                progressValue = max(0, min(100, round(double(value))));
                handles.pipelineProgress.Text = "Progress " + string(progressValue) + "%";
                if progressValue >= 90
                    setTone(handles.pipelineProgress, "green");
                elseif progressValue >= 35
                    setTone(handles.pipelineProgress, "blue");
                else
                    setTone(handles.pipelineProgress, "gray");
                end
            end
            [nextLabel, ~, ~] = nextActionForState(state);
            handles.nextActionButton.Text = nextLabel;
            updateStageRail(state);
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

    function onCloseApp(fig)
        stopAgentPollTimer();
        try
            delete(fig);
        catch
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
            readiness = "NEEDS CLARIFICATION";
            nextText = "Clarify prompt";
        elseif strlength(strtrim(notes)) > 0
            readiness = "PARAMETERIZED";
            nextText = "Prepare Build";
        else
            readiness = "READY";
            nextText = "Prepare Build";
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
                parts(end + 1) = "Ambiguity note: " + text; %#ok<AGROW>
            end
        end
        readiness = feval('citt.classifyBuildReadiness', spec);
        if strlength(strtrim(readiness.nonblocking_text)) > 0
            parts(end + 1) = readiness.nonblocking_text; %#ok<AGROW>
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
            "Local build code: " + emptyText(fieldText(runResult, "generated_code_path"), "not written")
            "Model: " + emptyText(fieldText(runResult, "produced_model_path"), "not found")
            "Focus map: " + emptyText(fieldText(runResult, "produced_focus_map_path"), "not found")
            "Probe map: " + emptyText(fieldText(runResult, "produced_probe_map_path"), "not found")
            "Report: " + emptyText(fieldText(runResult, "agent_report_path"), "not written")
            "Attempts: " + emptyText(fieldText(runResult, "agent_attempts"), "0")
            "PID: " + emptyText(fieldText(runResult, "agent_pid"), "not tracked")
            "Stdout log: " + emptyText(fieldText(runResult, "agent_stdout_path"), "not written")
            "Stderr log: " + emptyText(fieldText(runResult, "agent_stderr_path"), "not written")
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
            "Nonideal profiles"
            nonidealProfilesText(report)
            ""
            "Next actions"
            listValue(report.prioritized_next_actions)
            ""
            "Probe suggestion"
            fieldText(report, "next_probe_suggestion")
        ], newline);
    end

    function text = requirementRunSummary(report)
        s = report.summary;
        text = strjoin([
            "Requirement check complete."
            "JSON: " + report.report_path
            "Markdown: " + report.markdown_path
            "PASS " + string(s.pass) + ...
                " | WARN " + string(s.warn) + ...
                " | FAIL " + string(s.fail) + ...
                " | NOT_RUN " + string(s.not_run) + ...
                " | NOT_EVALUATED " + string(s.not_evaluated)
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
            "Suggestion: " + report.summary.suggested_design_change
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
        if numel(rows) > limit
            lines(end + 1) = "- ... " + string(numel(rows) - limit) + " more";
        end
        text = strjoin(lines, newline);
    end

    function text = nonidealProfilesText(report)
        if ~isstruct(report) || ~isfield(report, "nonideal_profiles")
            text = "none";
            return
        end
        text = reportRowsText(report.nonideal_profiles, ...
            ["part_number", "input_bias_current_typ_A", "input_offset_voltage_typ_V", "input_resistance_typ_ohm"], 6);
    end

    function path = lastVerificationMarkdownPath()
        candidates = [
            state.Config.ExplainabilityMarkdownPath
            state.Config.FaultInjectionMarkdownPath
            state.Config.ParameterSweepMarkdownPath
            state.Config.RequirementReportMarkdownPath
        ];
        path = "";
        for i = 1:numel(candidates)
            if exist(candidates(i), "file") == 2
                path = candidates(i);
                return
            end
        end
    end

    function text = evidencePackSummary(exported)
        summary = exported.status_summary;
        text = strjoin([
            "Evidence pack exported."
            "Pack: " + exported.pack_path
            "Requirements: PASS " + string(summary.pass) + ...
                " | WARN " + string(summary.warn) + ...
                " | FAIL " + string(summary.fail) + ...
                " | NOT_RUN " + string(summary.not_run)
            "Risk rows: " + string(numel(exported.risks))
            "Limitations: " + string(numel(exported.limitations))
            ""
            "Functional proof draft is shown below and included in the Markdown pack."
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
        if isempty(value) || strlength(strtrim(string(value))) == 0
            text = string(defaultText);
        else
            text = string(value);
        end
    end

    function text = fieldText(data, fieldName)
        if isstruct(data) && isfield(data, fieldName)
            text = joinValue(data.(fieldName));
        else
            text = "";
        end
    end

    function tf = isTruthy(value)
        text = lower(strtrim(string(value)));
        tf = any(text == ["true", "1", "yes"]);
    end

    function tf = isExistingFile(pathValue)
        code = exist(string(pathValue), "file");
        tf = code == 2 || code == 4;
    end
end
