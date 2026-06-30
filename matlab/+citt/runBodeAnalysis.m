function report = runBodeAnalysis(context, options)
%RUNBODEANALYSIS Generate available Bode/frequency-response evidence.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionText(options, "OutputPath", config.BodeReportPath);
markdownPath = optionText(options, "MarkdownPath", config.BodeMarkdownPath);
plotPath = optionText(options, "PlotPath", config.BodePlotPath);

spec = readSpec(context);
profiles = mergeProfiles( ...
    feval('citt.opAmpNonidealProfile', spec), ...
    feval('citt.opAmpNonidealProfile', contextText(context, "OpAmpPart", "")));
freqHz = optionNumberArray(options, "FrequencyHz", []);

messages = strings(0, 1);
curves = repmat(emptyCurve(), 0, 1);

[filterCurve, filterMessage] = filterChainBodeCurve(spec, freqHz);
if ~isempty(filterCurve)
    curves(end + 1, 1) = filterCurve; %#ok<AGROW>
elseif strlength(filterMessage) > 0
    messages(end + 1) = filterMessage;
end

[rcCurve, rcMessage] = rcBodeCurve(spec, freqHz);
if ~isempty(rcCurve)
    curves(end + 1, 1) = rcCurve; %#ok<AGROW>
else
    messages(end + 1) = rcMessage;
end

for i = 1:numel(profiles)
    profileCurve = opAmpProfileBodeCurve(profiles(i), freqHz);
    if ~isempty(profileCurve)
        curves(end + 1, 1) = profileCurve; %#ok<AGROW>
    end
end

[linCurve, linMessages] = linearizedBodeCurve(context, options, freqHz);
messages = [messages; linMessages(:)];
if ~isempty(linCurve)
    curves(end + 1, 1) = linCurve; %#ok<AGROW>
end

plotWritten = "";
if ~isempty(curves)
    plotWritten = writeBodePlot(plotPath, curves);
end

report = struct();
report.success = ~isempty(curves);
report.created_at = string(datetime("now"));
report.analysis_type = "bode_frequency_response";
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);
report.plot_path = string(plotWritten);
report.spec_path = context.SpecPath;
report.model_path = context.ModelPath;
report.curves = curves;
report.messages = messages;
report.next_action = nextAction(report);

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function context = normalizeContext(context, config)
if ~isfield(context, "Spec")
    context.Spec = [];
end
if ~isfield(context, "SpecPath")
    context.SpecPath = config.LastSpecPath;
end
if ~isfield(context, "ModelPath")
    context.ModelPath = config.GeneratedModelPath;
end
if ~isfield(context, "OpAmpPart")
    context.OpAmpPart = "";
end
end

function spec = readSpec(context)
if isstruct(context.Spec) && ~isempty(context.Spec)
    spec = context.Spec;
    return
end
spec = struct();
path = string(context.SpecPath);
if strlength(path) > 0 && exist(path, "file") == 2
    try
        spec = jsondecode(fileread(path));
    catch
        spec = struct();
    end
end
end

function [curve, message] = rcBodeCurve(spec, requestedFreqHz)
curve = [];
message = "No numeric resistor/capacitor pair was found for an analytic RC Bode plot.";
[rOhm, rId] = firstComponentValue(spec, ["resistor", "resistance", "r"], "ohm");
[cFarad, cId] = firstComponentValue(spec, ["capacitor", "capacitance", "c"], "f");
if isempty(rOhm) || isempty(cFarad)
    return
end

fcHz = 1 / (2 * pi * rOhm * cFarad);
if isempty(requestedFreqHz)
    freqHz = logspace(log10(max(fcHz / 100, 1e-6)), log10(max(fcHz * 100, fcHz + 1e-6)), 240);
else
    freqHz = requestedFreqHz(:)';
end

kind = rcKind(spec);
s = 1i * (freqHz / fcHz);
if kind == "highpass"
    h = s ./ (1 + s);
else
    h = 1 ./ (1 + s);
end

curve = emptyCurve();
curve.curve_id = "analytic_rc_" + kind;
curve.source = "analytic_spec";
curve.label = upper(kind) + " RC estimate from " + rId + " and " + cId;
curve.input = "spec input";
curve.output = "spec output";
curve.frequency_hz = freqHz;
curve.magnitude_db = 20 * log10(abs(h));
curve.phase_deg = unwrap(angle(h)) * 180 / pi;
curve.cutoff_frequency_hz = fcHz;
curve.notes = [
    "Computed from numeric R and C values in the circuit spec."
    "This is an analytic first-order estimate, not a full Simscape linearization."
];
message = "";
end

function [curve, message] = filterChainBodeCurve(spec, requestedFreqHz)
curve = [];
message = "";

[cHp, cHpId] = componentValueById(spec, "C_HP", "f");
[rHp, rHpId] = componentValueById(spec, "R_HP", "ohm");
[rLp, rLpId] = componentValueById(spec, "R_LP", "ohm");
[cLp, cLpId] = componentValueById(spec, "C_LP", "f");
[rNotch, rNotchId] = componentValueById(spec, "Rn1", "ohm");
[cNotch, cNotchId] = componentValueById(spec, "Cn1", "f");
hasFilterChain = ~isempty(cHp) && ~isempty(rHp) && ~isempty(rLp) && ~isempty(cLp);
hasTwinT = ~isempty(rNotch) && ~isempty(cNotch) && contains(lower(valueText(spec)), "twin");
if ~hasFilterChain && ~hasTwinT
    return
end
if ~hasFilterChain
    message = "A Twin-T/notch path was found, but numeric HP/LP values were incomplete for an ECG filter-chain estimate.";
    return
end

fcHp = 1 / (2 * pi * rHp * cHp);
fcLp = 1 / (2 * pi * rLp * cLp);
if hasTwinT
    f0 = 1 / (2 * pi * rNotch * cNotch);
else
    f0 = [];
end

if isempty(requestedFreqHz)
    upperHz = max([fcLp * 100, 1000, f0 * 10]);
    freqHz = logspace(log10(max(fcHp / 100, 1e-3)), log10(upperHz), 360);
else
    freqHz = requestedFreqHz(:)';
end

s = 1i * 2 * pi * freqHz;
h = (s ./ (s + 2 * pi * fcHp)) .* (1 ./ (1 + s ./ (2 * pi * fcLp)));
notes = [
    "Computed from named ECG filter components in the circuit spec."
    "This is an analytic estimate, not a full Simscape linearization."
];
if hasTwinT
    qEstimate = 0.35;
    w0 = 2 * pi * f0;
    hNotch = (s.^2 + w0^2) ./ (s.^2 + (w0 / qEstimate) .* s + w0^2);
    h = h .* hNotch;
    notes(end + 1) = "Twin-T notch is approximated as a second-order notch using " + ...
        rNotchId + " and " + cNotchId + " with Q=" + string(qEstimate) + ".";
end

curve = emptyCurve();
curve.curve_id = "analytic_ecg_filter_chain";
curve.source = "analytic_spec";
if hasTwinT
    curve.label = "ECG HP/LP + Twin-T notch estimate";
else
    curve.label = "ECG HP/LP filter estimate";
end
curve.input = "INA_OUT";
curve.output = "ADC_OUT";
curve.frequency_hz = freqHz;
curve.magnitude_db = 20 * log10(max(abs(h), realmin));
curve.phase_deg = unwrap(angle(h)) * 180 / pi;
curve.cutoff_frequency_hz = [fcHp, fcLp, f0];
curve.notes = notes;
message = "Generated ECG filter-chain analytic Bode from " + ...
    strjoin([rHpId, cHpId, rLpId, cLpId], ", ") + ".";
end

function kind = rcKind(spec)
text = lower(valueText(spec));
if contains(text, "high pass") || contains(text, "high-pass") || contains(text, "hp filter")
    kind = "highpass";
else
    kind = "lowpass";
end
end

function curve = opAmpProfileBodeCurve(profile, requestedFreqHz)
curve = [];
part = string(profile.part_number);
if part == ""
    return
end
a0 = scalarField(profile, "large_signal_gain_typ_V_per_V");
gbw = scalarField(profile, "unity_gain_bandwidth_typ_Hz");
if isempty(a0) || isempty(gbw) || a0 <= 0 || gbw <= 0
    return
end
fpHz = gbw / a0;
if isempty(requestedFreqHz)
    freqHz = logspace(log10(max(fpHz / 100, 1e-3)), log10(gbw * 10), 260);
else
    freqHz = requestedFreqHz(:)';
end
h = a0 ./ (1 + 1i * (freqHz / fpHz));

curve = emptyCurve();
curve.curve_id = lower(part) + "_open_loop_estimate";
curve.source = "op_amp_profile";
curve.label = part + " open-loop estimate";
curve.input = "differential input";
curve.output = "op-amp output";
curve.frequency_hz = freqHz;
curve.magnitude_db = 20 * log10(abs(h));
curve.phase_deg = unwrap(angle(h)) * 180 / pi;
curve.cutoff_frequency_hz = fpHz;
curve.notes = [
    "Single-pole estimate from large-signal gain and unity-gain bandwidth."
    "This is a device-profile Bode curve, not the closed-loop circuit response."
];
end

function [curve, messages] = linearizedBodeCurve(context, options, requestedFreqHz)
curve = [];
messages = strings(0, 1);
if exist("linearize", "file") ~= 2 || exist("linio", "file") ~= 2
    messages(end + 1) = "Simulink linearization tools were not found; analytic/spec Bode only.";
    return
end

inputPath = optionText(options, "InputPath", "");
outputPath = optionText(options, "OutputPathBlock", "");
if strlength(inputPath) == 0 || strlength(outputPath) == 0
    messages(end + 1) = "No linearization I/O paths were provided. Pass InputPath and OutputPathBlock for full Simulink Bode.";
    return
end

modelPath = string(context.ModelPath);
if exist(modelPath, "file") ~= 2
    messages(end + 1) = "Model path missing for Simulink linearization: " + modelPath;
    return
end

try
    [~, modelName, ~] = fileparts(modelPath);
    load_system(char(modelPath));
    io = [
        linio(char(inputPath), 1, "input")
        linio(char(outputPath), 1, "output")
    ];
    if isempty(requestedFreqHz)
        freqHz = logspace(0, 6, 240);
    else
        freqHz = requestedFreqHz(:)';
    end
    sys = linearize(char(modelName), io);
    [mag, phase] = bode(sys, 2 * pi * freqHz);
    mag = squeeze(mag);
    phase = squeeze(phase);

    curve = emptyCurve();
    curve.curve_id = "simulink_linearized";
    curve.source = "simulink_linearize";
    curve.label = "Linearized Simulink response";
    curve.input = string(inputPath);
    curve.output = string(outputPath);
    curve.frequency_hz = freqHz;
    curve.magnitude_db = 20 * log10(abs(mag(:)'));
    curve.phase_deg = phase(:)';
    curve.cutoff_frequency_hz = [];
    curve.notes = "Generated with linearize/linio from the current model.";
catch linearizeError
    messages(end + 1) = "Simulink linearization failed: " + string(linearizeError.message);
end
end

function path = writeBodePlot(plotPath, curves)
path = string(plotPath);
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end

fig = figure("Visible", "off", "Color", "w");
cleanup = onCleanup(@() close(fig));
tiledlayout(fig, 2, 1);

ax1 = nexttile;
hold(ax1, "on");
grid(ax1, "on");
ylabel(ax1, "Magnitude (dB)");
title(ax1, "CiTT Bode Analysis");

ax2 = nexttile;
hold(ax2, "on");
grid(ax2, "on");
xlabel(ax2, "Frequency (Hz)");
ylabel(ax2, "Phase (deg)");

labels = strings(numel(curves), 1);
for i = 1:numel(curves)
    f = double(curves(i).frequency_hz);
    semilogx(ax1, f, double(curves(i).magnitude_db), "LineWidth", 1.4);
    semilogx(ax2, f, double(curves(i).phase_deg), "LineWidth", 1.4);
    labels(i) = curves(i).label;
end
positiveFrequencies = [];
for i = 1:numel(curves)
    f = double(curves(i).frequency_hz);
    positiveFrequencies = [positiveFrequencies, f(f > 0)]; %#ok<AGROW>
end
if ~isempty(positiveFrequencies)
    xLimits = [min(positiveFrequencies), max(positiveFrequencies)];
    set(ax1, "XScale", "log", "XLim", xLimits);
    set(ax2, "XScale", "log", "XLim", xLimits);
end
legend(ax1, labels, "Interpreter", "none", "Location", "best");
legend(ax2, labels, "Interpreter", "none", "Location", "best");
exportgraphics(fig, char(path), "Resolution", 160);
end

function action = nextAction(report)
if isempty(report.curves)
    action = "Add numeric R/C values, an op-amp part profile, or Simulink linearization I/O points.";
elseif any([report.curves.source] == "analytic_spec")
    action = "Use the analytic Bode as a sanity check, then add Simulink linearization I/O points for full model response.";
else
    action = "Compare the Bode plot against lab frequency-sweep data.";
end
end

function curve = emptyCurve()
curve = struct();
curve.curve_id = "";
curve.source = "";
curve.label = "";
curve.input = "";
curve.output = "";
curve.frequency_hz = [];
curve.magnitude_db = [];
curve.phase_deg = [];
curve.cutoff_frequency_hz = [];
curve.notes = strings(0, 1);
end

function [value, id] = firstComponentValue(spec, typeHints, unitFamily)
value = [];
id = "";
components = getField(spec, "components");
if isempty(components)
    return
end
for i = 1:numel(components)
    if iscell(components)
        component = components{i};
    else
        component = components(i);
    end
    if componentMatchesTypeHint(component, typeHints)
        id = fieldText(component, "id");
        if strlength(id) == 0
            id = "component_" + string(i);
        end
        raw = componentValueWithUnit(component);
        value = parseSi(raw, unitFamily);
        if ~isempty(value)
            return
        end
    end
end
end

function matches = componentMatchesTypeHint(component, typeHints)
hints = lower(string(typeHints));
typeText = lower(strjoin([
    fieldText(component, "type")
    fieldText(component, "component_type")
    fieldText(component, "kind")
    fieldText(component, "label")
], " "));
idText = lower(fieldText(component, "id"));

longHints = hints(strlength(hints) > 1);
matches = ~isempty(longHints) && any(contains(typeText, longHints));
if matches
    return
end

singleHints = hints(strlength(hints) == 1);
if any(singleHints == "r")
    matches = startsWith(idText, "r") || any(typeText == ["r", "resistor"]);
elseif any(singleHints == "c")
    matches = startsWith(idText, "c") || any(typeText == ["c", "capacitor"]);
else
    matches = false;
end
end

function [value, id] = componentValueById(spec, targetId, unitFamily)
value = [];
id = "";
components = getField(spec, "components");
if isempty(components)
    return
end
targetId = lower(string(targetId));
for i = 1:numel(components)
    if iscell(components)
        component = components{i};
    else
        component = components(i);
    end
    candidateId = fieldText(component, "id");
    if lower(candidateId) ~= targetId
        continue
    end
    raw = componentValueWithUnit(component);
    value = parseSi(raw, unitFamily);
    if ~isempty(value)
        id = candidateId;
        return
    end
end
end

function value = componentValueWithUnit(component)
value = firstField(component, ["value", "nominal_value", "resistance", "capacitance"]);
unit = firstField(component, ["unit", "units"]);
if ~isempty(value) && ~isempty(unit)
    value = strtrim(valueText(value) + " " + valueText(unit));
end
end

function value = parseSi(raw, unitFamily)
value = [];
rawText = strtrim(valueText(raw));
text = lower(rawText);
if strlength(text) == 0 || text == "null"
    return
end
tokens = regexp(char(rawText), '([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zA-Zµ]*)', 'tokens', 'once');
if isempty(tokens)
    return
end
base = str2double(tokens{1});
suffixRaw = string(tokens{2});
suffix = lower(replace(suffixRaw, "µ", "u"));
factor = 1;
if startsWith(suffix, "meg") || (unitFamily == "ohm" && startsWith(suffixRaw, "M"))
    factor = 1e6;
elseif startsWith(suffix, "k")
    factor = 1e3;
elseif startsWith(suffix, "m") && unitFamily ~= "f"
    factor = 1e-3;
elseif startsWith(suffix, "u")
    factor = 1e-6;
elseif startsWith(suffix, "n")
    factor = 1e-9;
elseif startsWith(suffix, "p")
    factor = 1e-12;
end
if unitFamily == "f" && startsWith(suffix, "m")
    factor = 1e-3;
end
value = base * factor;
end

function value = getField(container, fieldName)
if isstruct(container) && isfield(container, fieldName)
    value = container.(fieldName);
else
    value = [];
end
end

function value = firstField(container, names)
value = [];
if ~isstruct(container)
    return
end
for i = 1:numel(names)
    name = names(i);
    if isfield(container, name)
        value = container.(name);
        return
    end
end
end

function value = fieldText(container, fieldName)
raw = firstField(container, fieldName);
value = valueText(raw);
end

function value = scalarField(container, fieldName)
raw = firstField(container, fieldName);
if isnumeric(raw) && isscalar(raw)
    value = double(raw);
else
    value = [];
end
end

function text = valueText(value)
if isempty(value)
    text = "";
elseif ischar(value)
    text = string(value);
elseif isstring(value)
    text = strjoin(string(value(:))', " ");
elseif isnumeric(value) || islogical(value)
    text = string(mat2str(value));
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueText(value{i});
    end
    text = strjoin(parts(:)', " ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function profiles = mergeProfiles(left, right)
profiles = left;
if isempty(profiles)
    profiles = right;
    return
end
for i = 1:numel(right)
    part = string(right(i).part_number);
    exists = false;
    for j = 1:numel(profiles)
        if string(profiles(j).part_number) == part
            exists = true;
            break
        end
    end
    if ~exists
        profiles(end + 1, 1) = right(i); %#ok<AGROW>
    end
end
end

function value = optionText(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName) && ~isempty(options.(fieldName))
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function value = contextText(context, fieldName, defaultValue)
if isstruct(context) && isfield(context, fieldName) && ~isempty(context.(fieldName))
    value = string(context.(fieldName));
else
    value = string(defaultValue);
end
end

function values = optionNumberArray(options, fieldName, defaultValues)
if isstruct(options) && isfield(options, fieldName) && ~isempty(options.(fieldName))
    values = double(options.(fieldName));
else
    values = defaultValues;
end
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid >= 0
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid >= 0
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s", char(text));
end
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Bode Analysis"
    ""
    "- JSON: " + report.report_path
    "- Plot: " + emptyText(report.plot_path, "not generated")
    "- Model: " + report.model_path
    "- Spec: " + report.spec_path
    ""
    "## Curves"
    ""
];
if isempty(report.curves)
    lines(end + 1) = "No Bode curve was generated.";
else
    lines = [lines; "| Curve | Source | Input | Output | Cutoff / Pole | Notes |"; ...
        "| --- | --- | --- | --- | --- | --- |"];
    for i = 1:numel(report.curves)
        c = report.curves(i);
        lines(end + 1) = "| " + md(c.label) + " | " + md(c.source) + " | " + ...
            md(c.input) + " | " + md(c.output) + " | " + md(numberText(c.cutoff_frequency_hz)) + ...
            " Hz | " + md(strjoin(string(c.notes), " ")) + " |"; %#ok<AGROW>
    end
end
lines = [lines; ""; "## Messages"; ""];
if isempty(report.messages)
    lines(end + 1) = "- none";
else
    for i = 1:numel(report.messages)
        if strlength(report.messages(i)) > 0
            lines(end + 1) = "- " + report.messages(i); %#ok<AGROW>
        end
    end
end
lines = [lines; ""; "## Next Action"; ""; "- " + report.next_action];
text = strjoin(lines, newline);
end

function text = numberText(value)
if isempty(value)
    text = "";
else
    text = string(sprintf("%.6g", value));
end
end

function text = emptyText(value, defaultText)
if strlength(string(value)) == 0
    text = string(defaultText);
else
    text = string(value);
end
end

function text = md(value)
text = replace(string(value), "|", "\|");
text = replace(text, newline, " ");
end
