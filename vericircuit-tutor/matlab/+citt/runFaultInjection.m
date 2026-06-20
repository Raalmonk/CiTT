function report = runFaultInjection(context, options)
%RUNFAULTINJECTION Generate educational fault scenarios and predicted effects.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.FaultInjectionReportPath);
markdownPath = optionString(options, "MarkdownPath", config.FaultInjectionMarkdownPath);
spec = readSpec(context);
[rOhm, ~] = firstComponentValue(spec, ["resistor", "resistance", "r"], "ohm");
[cFarad, ~] = firstComponentValue(spec, ["capacitor", "capacitance", "c"], "f");

nominalCutoff = [];
if ~isempty(rOhm) && ~isempty(cFarad)
    nominalCutoff = 1 / (2 * pi * rOhm * cFarad);
end

rows = struct("fault", {}, "injected_change", {}, "observed_effect", {}, ...
    "student_explanation", {}, "risk_mitigation", {}, "status", {});
rows(end + 1) = faultRow("Open lead / disconnected electrode", ...
    "Disconnect the input source or electrode path.", ...
    "Output becomes floating, zero, or dominated by noise depending on bias path.", ...
    "The measured signal path is broken before the modeled filter can act.", ...
    "Add connectivity checks and teach students to verify reference nodes first.", "READY");
rows(end + 1) = faultRow("Shorted capacitor", ...
    "Force the filter capacitor impedance toward zero.", ...
    shortedCapEffect(nominalCutoff), ...
    "A shorted shunt capacitor can clamp the output node or destroy the intended pole.", ...
    "Probe both sides of the capacitor and flag near-zero impedance faults.", "READY");
rows(end + 1) = faultRow("Wrong capacitor unit: nF vs uF", ...
    "Scale capacitance by 1/1000 or 1000.", ...
    unitFaultEffect(nominalCutoff), ...
    "Unit-prefix mistakes move the cutoff by orders of magnitude.", ...
    "Run a parameter sanity check before simulation and display SI prefixes in reports.", statusFromNumeric(nominalCutoff));
rows(end + 1) = faultRow("Op-amp output saturation", ...
    "Limit output to assumed supply rails.", ...
    "Waveform clips; small-signal frequency response no longer predicts output amplitude.", ...
    "Active stages can leave their linear operating region.", ...
    "Add output range requirements and inspect saturation source highlights.", "PLAN");
rows(end + 1) = faultRow("ADC undersampling", ...
    "Lower sampling frequency below Nyquist margin.", ...
    "High-frequency content aliases into the measurement band.", ...
    "Sampling is part of the measurement system, not a cosmetic detail.", ...
    "Add an fs >= 2*fmax requirement and sweep sampling frequency.", "PLAN");
rows(end + 1) = faultRow("60 Hz interference too large", ...
    "Increase mains interference amplitude.", ...
    "Output shows residual line-frequency content if filtering or shielding is insufficient.", ...
    "Biomedical front-ends are sensitive to common-mode and environmental pickup.", ...
    "Measure 60 Hz attenuation and include grounding/shielding assumptions.", "PLAN");
rows(end + 1) = faultRow("Sensor noise increased", ...
    "Increase source or measurement noise.", ...
    "Signal-to-noise ratio drops; small feature detection becomes unreliable.", ...
    "Noise can hide physiological or low-amplitude circuit behavior.", ...
    "Log SNR and compare expected versus measured noise floor.", "PLAN");
rows(end + 1) = faultRow("Load impedance too low", ...
    "Decrease load resistance at the output node.", ...
    "The output node is pulled away from the ideal unloaded response.", ...
    "Measurement equipment and downstream stages can alter the circuit under test.", ...
    "Add input/load impedance requirements and teach loading as a failure mode.", "PLAN");

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.nominal_cutoff_hz = numericOrEmpty(nominalCutoff);
report.rows = rows;
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);

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
end

function spec = readSpec(context)
if isstruct(context.Spec) && ~isempty(context.Spec)
    spec = context.Spec;
    return
end
spec = [];
path = string(context.SpecPath);
if strlength(path) > 0 && exist(path, "file") == 2
    try
        spec = jsondecode(fileread(path));
    catch
        spec = [];
    end
end
end

function row = faultRow(fault, injectedChange, observedEffect, explanation, mitigation, status)
row = struct();
row.fault = string(fault);
row.injected_change = string(injectedChange);
row.observed_effect = string(observedEffect);
row.student_explanation = string(explanation);
row.risk_mitigation = string(mitigation);
row.status = string(status);
end

function text = shortedCapEffect(nominalCutoff)
if isempty(nominalCutoff)
    text = "Expected severe output attenuation or node clamp; numeric cutoff shift not evaluated.";
else
    text = sprintf("Nominal cutoff %.4g Hz is no longer meaningful because the output node is effectively shorted.", nominalCutoff);
end
end

function text = unitFaultEffect(nominalCutoff)
if isempty(nominalCutoff)
    text = "Numeric cutoff shift not evaluated because nominal R/C values are missing.";
else
    text = sprintf("If C is 1000x too small, cutoff shifts from %.4g Hz to %.4g Hz; if 1000x too large, it shifts to %.4g Hz.", ...
        nominalCutoff, nominalCutoff * 1000, nominalCutoff / 1000);
end
end

function status = statusFromNumeric(value)
if isempty(value)
    status = "NEEDS_NUMERIC_VALUES";
else
    status = "READY";
end
end

function [value, id] = firstComponentValue(spec, typeHints, unitFamily)
value = [];
id = "";
if ~isstruct(spec) || ~isfield(spec, "components")
    return
end
components = spec.components;
for i = 1:numel(components)
    component = components(i);
    text = lower(valueText(component));
    if any(contains(text, lower(string(typeHints))))
        id = fieldText(component, "id");
        raw = firstField(component, ["value", "nominal_value", "resistance", "capacitance"]);
        value = parseSi(raw, unitFamily);
        if ~isempty(value)
            return
        end
    end
end
end

function value = parseSi(raw, unitFamily)
value = [];
text = lower(strtrim(valueText(raw)));
tokens = regexp(char(text), '([-+]?\d*\.?\d+(e[-+]?\d+)?)\s*([a-zµ]*)', 'tokens', 'once');
if isempty(tokens)
    return
end
base = str2double(tokens{1});
suffix = replace(string(tokens{3}), "µ", "u");
factor = 1;
if startsWith(suffix, "meg")
    factor = 1e6;
elseif startsWith(suffix, "k")
    factor = 1e3;
elseif startsWith(suffix, "m")
    factor = 1e-3;
elseif startsWith(suffix, "u")
    factor = 1e-6;
elseif startsWith(suffix, "n")
    factor = 1e-9;
elseif startsWith(suffix, "p")
    factor = 1e-12;
end
if unitFamily ~= "f" && startsWith(suffix, "m")
    factor = 1e-3;
end
value = base * factor;
end

function value = firstField(container, names)
value = [];
for i = 1:numel(names)
    name = char(names(i));
    if isstruct(container) && isfield(container, name)
        value = container.(name);
        return
    end
end
end

function text = fieldText(container, name)
if isstruct(container) && isfield(container, name)
    text = valueText(container.(name));
else
    text = "";
end
end

function text = valueText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', " ");
elseif ischar(value)
    text = string(value);
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueText(value{i});
    end
    text = strjoin(parts, " ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
elseif isnumeric(value) || islogical(value)
    text = string(mat2str(value));
else
    text = string(value);
end
end

function value = numericOrEmpty(value)
if isempty(value)
    value = [];
end
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Risk / Fault Injection"
    ""
    "Created: " + report.created_at
    ""
    "| Fault | Injected Change | Observed Effect | Explanation | Mitigation | Status |"
    "| --- | --- | --- | --- | --- | --- |"
];
for i = 1:numel(report.rows)
    r = report.rows(i);
    lines(end + 1) = "| " + md(r.fault) + " | " + md(r.injected_change) + " | " + ...
        md(r.observed_effect) + " | " + md(r.student_explanation) + " | " + ...
        md(r.risk_mitigation) + " | " + md(r.status) + " |"; %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function text = md(value)
text = replace(string(value), "|", "\|");
text = replace(text, newline, "<br>");
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end
