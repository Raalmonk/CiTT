function varargout = citt(labId)
%CITT Launch the CiTT MATLAB popup tutor from a local offline bundle.
%   One-time MATLAB setup:
%       addpath('/Users/Raalm/Documents/GitHub/CiTT/vericircuit-tutor')
%       savepath
%
%   Then run:
%       citt

if nargin < 1 || isempty(labId)
    labId = "rc_antialias_adc";
end

repoRoot = fileparts(mfilename("fullpath"));
bundleRoot = fullfile(repoRoot, "backend", "matlab_plugin_exports", char(labId));
loaderPath = fullfile(bundleRoot, "+citt", "loadOfflineBundle.m");

if ~exist(loaderPath, "file")
    error( ...
        "CiTT:MissingOfflineBundle", ...
        "CiTT offline bundle is missing. Expected loader at: %s", ...
        loaderPath ...
    );
end

addpath(bundleRoot, "-end");
bundle = citt.loadOfflineBundle(labId);
fig = openCittPopup(bundle);

if nargout > 0
    bundle.popup_figure = fig;
    varargout{1} = bundle;
end
end

function fig = openCittPopup(bundle)
lab = bundle.lab_plan.lab;
titleText = "CiTT - " + oneLine(readField(lab, "title"));

fig = uifigure( ...
    "Name", titleText, ...
    "Position", [120 120 920 680] ...
);
main = uigridlayout(fig, [2 1]);
main.RowHeight = {54, "1x"};
main.Padding = [16 14 16 16];
main.RowSpacing = 10;

header = uilabel(main);
header.Text = "CiTT Popup Tutor: " + oneLine(readField(lab, "title"));
header.FontSize = 18;
header.FontWeight = "bold";

tabs = uitabgroup(main);
tabs.Layout.Row = 2;
tabs.Layout.Column = 1;

createTextTab(tabs, "Overview", overviewLines(bundle));
createTextTab(tabs, "Teach", teachLines(bundle));
createTextTab(tabs, "Probe", probeLines(bundle));
createTextTab(tabs, "Lab Delta", labDeltaLines(bundle));
end

function createTextTab(tabGroup, titleText, lines)
tab = uitab(tabGroup, "Title", titleText);
layout = uigridlayout(tab, [1 1]);
layout.Padding = [12 12 12 12];

textArea = uitextarea(layout);
textArea.Editable = "off";
textArea.FontName = "Menlo";
textArea.FontSize = 13;
textArea.Value = cellstr(lines(:));
end

function lines = overviewLines(bundle)
lab = bundle.lab_plan.lab;
overview = bundle.lab_plan.overview;

lines = strings(0, 1);
lines = addLine(lines, "Overview");
lines = addLine(lines, "");
lines = addLine(lines, "Lab title: " + oneLine(readField(lab, "title")));
lines = addLine(lines, "Objective: " + oneLine(readField(lab, "objective")));
lines = addLine(lines, "");
lines = addLine(lines, "Inputs");
lines = addBlock(lines, listLines(readField(lab, "inputs")));
lines = addLine(lines, "");
lines = addLine(lines, "Outputs");
lines = addBlock(lines, listLines(readField(lab, "outputs")));
lines = addLine(lines, "");
lines = addLine(lines, "Key parameters");
lines = addBlock(lines, mapLines(readField(lab, "key_parameters")));
lines = addLine(lines, "");
lines = addLine(lines, "Assumptions");
lines = addBlock(lines, listLines(readField(lab, "assumptions")));
lines = addLine(lines, "");
lines = addLine(lines, "Idealizations");
lines = addBlock(lines, listLines(readField(lab, "idealizations")));
lines = addLine(lines, "");
lines = addLine(lines, "BME safety boundary");
lines = addLine(lines, oneLine(readField(lab, "bme_safety_boundary")));
lines = addLine(lines, "");
lines = addLine(lines, "Artifact");
lines = addLine(lines, oneLine(readField(overview, "generated_artifact")));
lines = addLine(lines, "");
lines = addLine(lines, "Evidence to collect");
lines = addBlock(lines, listLines(readField(lab, "evidence_to_collect")));
lines = addLine(lines, "");
lines = addLine(lines, "Local server required: false");
end

function lines = teachLines(bundle)
steps = readField(bundle.lab_plan, "teach_steps");
focusMap = readField(bundle.lab_plan, "focus_map");

lines = strings(0, 1);
lines = addLine(lines, "Teach");
lines = addLine(lines, "");
for i = 1:numel(steps)
    step = steps(i);
    lines = addLine(lines, "Step " + string(i) + ": " + oneLine(readField(step, "title")));
    lines = addLine(lines, "Prompt: " + oneLine(readField(step, "prompt_before_reveal")));
    lines = addLine(lines, "Explanation: " + oneLine(readField(step, "explanation")));
    mistakes = listLines(readField(step, "common_mistakes"));
    if ~isempty(mistakes)
        lines = addLine(lines, "Common mistakes");
        lines = addBlock(lines, mistakes);
    end
    lines = addLine(lines, "");
end

lines = addLine(lines, "Focus map preview");
for i = 1:min(numel(focusMap), 8)
    entry = focusMap(i);
    target = readField(entry, "target");
    lines = addLine(lines, "- " + oneLine(readField(entry, "id")) + ": " + oneLine(readField(target, "label")));
end
end

function lines = probeLines(bundle)
probes = readField(bundle.lab_plan, "probe_plan");

lines = strings(0, 1);
lines = addLine(lines, "Probe");
lines = addLine(lines, "");
for i = 1:numel(probes)
    probe = probes(i);
    target = readField(probe, "target");
    lines = addLine(lines, oneLine(readField(probe, "title")));
    lines = addLine(lines, "Goal: " + oneLine(readField(probe, "student_goal")));
    lines = addLine(lines, "Target: " + oneLine(readField(target, "label")));
    lines = addLine(lines, "Quantity: " + oneLine(readField(probe, "quantity")) + " (" + oneLine(readField(probe, "unit")) + ")");
    lines = addLine(lines, "Question: " + oneLine(readField(probe, "student_question")));
    lines = addLine(lines, "Measurement: " + oneLine(readField(probe, "measurement_explanation")));
    logging = listLines(readField(probe, "suggested_logging"));
    if ~isempty(logging)
        lines = addLine(lines, "Suggested logging");
        lines = addBlock(lines, logging);
    end
    lines = addLine(lines, "");
end
end

function lines = labDeltaLines(bundle)
delta = bundle.lab_delta_example;
rows = readField(delta, "comparison_rows");
causes = readField(delta, "likely_causes");

lines = strings(0, 1);
lines = addLine(lines, "Lab Delta");
lines = addLine(lines, "");
lines = addLine(lines, "Comparison rows");
for i = 1:numel(rows)
    row = rows(i);
    lines = addLine(lines, "- " + oneLine(readField(row, "label")));
    lines = addLine(lines, "  hand: " + oneLine(readField(row, "hand_value")) + ...
        ", simulation: " + oneLine(readField(row, "simulation_value")) + ...
        ", measured: " + oneLine(readField(row, "measured_value")) + ...
        ", percent diff: " + oneLine(readField(row, "percent_difference")));
end
lines = addLine(lines, "");
lines = addLine(lines, "Likely causes");
for i = 1:numel(causes)
    cause = causes(i);
    lines = addLine(lines, "- " + oneLine(readField(cause, "title")) + ": " + oneLine(readField(cause, "explanation")));
    lines = addLine(lines, "  Next check: " + oneLine(readField(cause, "next_check")));
end
lines = addLine(lines, "");
lines = addLine(lines, "Next probe: " + oneLine(readField(delta, "next_probe_suggestion")));
lines = addLine(lines, "Reflection: " + oneLine(readField(delta, "reflection_question")));
end

function value = readField(container, fieldName)
if isstruct(container) && isfield(container, fieldName)
    value = container.(fieldName);
else
    value = [];
end
end

function text = oneLine(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif isnumeric(value) || islogical(value)
    if isscalar(value)
        text = string(num2str(value, 6));
    else
        text = string(mat2str(value));
    end
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = oneLine(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isstruct(value)
    try
        text = string(jsonencode(value));
    catch
        text = "<struct>";
    end
else
    text = string(value);
end
end

function lines = listLines(value)
items = toStringArray(value);
if isempty(items)
    lines = strings(0, 1);
else
    lines = "- " + items(:);
end
end

function lines = mapLines(value)
if isstruct(value)
    names = fieldnames(value);
    lines = strings(numel(names), 1);
    for i = 1:numel(names)
        name = string(names{i});
        lines(i) = "- " + name + ": " + oneLine(value.(names{i}));
    end
else
    lines = listLines(value);
end
end

function items = toStringArray(value)
if isempty(value)
    items = strings(0, 1);
elseif isstring(value)
    items = value(:);
elseif ischar(value)
    items = string(value);
elseif iscell(value)
    items = strings(numel(value), 1);
    for i = 1:numel(value)
        items(i) = oneLine(value{i});
    end
elseif isnumeric(value) || islogical(value)
    items = string(value(:));
else
    items = string(value);
end
end

function lines = addLine(lines, line)
lines(end + 1, 1) = string(line);
end

function lines = addBlock(lines, block)
if ~isempty(block)
    lines = [lines; string(block(:))];
end
end
