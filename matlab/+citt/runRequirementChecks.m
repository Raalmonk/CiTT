function report = runRequirementChecks(context, options)
%RUNREQUIREMENTCHECKS Build a requirement-to-evidence pass/fail table.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.RequirementReportPath);
markdownPath = optionString(options, "MarkdownPath", config.RequirementReportMarkdownPath);

spec = readSpec(context);
modelCheck = firstStruct(context, "LastModelCheck", config.ModelCheckReportPath);
simulation = firstStruct(context, "LastSimulation", config.SimulationSummaryPath);
labDelta = firstStruct(context, "LastLabDelta", config.LabDeltaReportPath);

rows = struct("requirement", {}, "result", {}, "status", {}, "evidence", {});
rows(end + 1) = row("Cutoff frequency near target", cutoffResult(spec, labDelta), cutoffStatus(spec, labDelta), "spec + Lab Delta/simulation metrics");
rows(end + 1) = row("Sampling frequency satisfies Nyquist", nyquistResult(spec, simulation), nyquistStatus(spec, simulation), "spec + simulation metrics");
rows(end + 1) = row("Output saturation / clipping absent", clippingResult(simulation), clippingStatus(simulation), "simulation summary");
rows(end + 1) = row("60 Hz interference attenuation checked", attenuationResult(labDelta, simulation), attenuationStatus(labDelta, simulation), "Lab Delta/simulation metrics");
rows(end + 1) = row("Input impedance above threshold", scalarRequirementResult(spec, simulation, ["input_impedance_ohm", "input_impedance"], "ohm"), scalarRequirementStatus(spec, simulation, ["input_impedance_ohm", "input_impedance"]), "spec + simulation metrics");
rows(end + 1) = row("ADC quantization step below threshold", scalarRequirementResult(spec, simulation, ["adc_quantization_step_v", "quantization_step"], "V"), scalarRequirementStatus(spec, simulation, ["adc_quantization_step_v", "quantization_step"]), "spec + simulation metrics");
rows(end + 1) = row("Model check has no update errors", modelCheckResult(modelCheck), passFailNotRun(modelCheck), "model_check report");
rows(end + 1) = row("Focus map available for teaching highlights", pathResult(context.FocusMapPath), pathStatus(context.FocusMapPath), context.FocusMapPath);
rows(end + 1) = row("Probe map available for guided measurements", pathResult(context.ProbeMapPath), pathStatus(context.ProbeMapPath), context.ProbeMapPath);

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.source_spec = string(context.SpecPath);
report.rows = rows;
report.summary = summarize(rows);
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function context = normalizeContext(context, config)
defaults = struct( ...
    "Spec", [], ...
    "SpecPath", config.LastSpecPath, ...
    "FocusMapPath", config.FocusMapPath, ...
    "ProbeMapPath", config.ProbeMapPath, ...
    "LastModelCheck", [], ...
    "LastSimulation", [], ...
    "LastLabDelta", []);
names = fieldnames(defaults);
for i = 1:numel(names)
    if ~isfield(context, names{i})
        context.(names{i}) = defaults.(names{i});
    end
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

function value = firstStruct(context, stateField, path)
value = [];
if isfield(context, stateField) && isstruct(context.(stateField)) && ~isempty(context.(stateField))
    value = context.(stateField);
    return
end
path = string(path);
if strlength(path) > 0 && exist(path, "file") == 2
    try
        if endsWith(path, ".json")
            value = jsondecode(fileread(path));
        else
            text = string(fileread(path));
            value = struct("success", contains(lower(text), "success: true") || contains(lower(text), "success: 1"), ...
                "messages", splitlines(text), "report_path", path);
        end
    catch
        value = [];
    end
end
end

function r = row(requirement, result, status, evidence)
r = struct("requirement", string(requirement), "result", string(result), ...
    "status", string(status), "evidence", string(evidence));
end

function text = cutoffResult(spec, labDelta)
[value, source] = findMetric(labDelta, ["fc", "cutoff"]);
[target, tolerance] = cutoffTarget(spec);
if isempty(value)
    text = "cutoff frequency not measured/logged";
elseif isempty(target)
    text = sprintf("fc=%.4g Hz from %s; no target found", value, source);
else
    text = sprintf("fc=%.4g Hz, target %.4g Hz +/- %.3g%%", value, target, tolerance * 100);
end
end

function status = cutoffStatus(spec, labDelta)
[value, ~] = findMetric(labDelta, ["fc", "cutoff"]);
[target, tolerance] = cutoffTarget(spec);
if isempty(value) || isempty(target)
    status = "NOT_EVALUATED";
elseif abs(value - target) <= abs(target) * tolerance
    status = "PASS";
elseif abs(value - target) <= abs(target) * tolerance * 1.5
    status = "WARN";
else
    status = "FAIL";
end
end

function [target, tolerance] = cutoffTarget(spec)
target = [];
tolerance = 0.10;
text = lower(valueText(spec));
tokens = regexp(char(text), '(\d+(\.\d+)?)\s*hz', 'tokens');
if ~isempty(tokens)
    target = str2double(tokens{1}{1});
elseif contains(text, "ecg") || contains(text, "anti") || contains(text, "alias")
    target = 40;
end
end

function text = nyquistResult(spec, simulation)
fs = firstNumber(spec, ["sampling_frequency_hz", "sample_rate_hz", "fs_hz", "fs"]);
fmax = firstNumber(spec, ["highest_signal_frequency_hz", "max_signal_frequency_hz", "fmax_hz"]);
if isempty(fs)
    fs = firstNumber(simulation, ["sampling_frequency_hz", "sample_rate_hz", "fs_hz", "fs"]);
end
if isempty(fmax)
    fmax = firstNumber(simulation, ["highest_signal_frequency_hz", "max_signal_frequency_hz", "fmax_hz"]);
end
if isempty(fmax) && contains(lower(valueText(spec)), "ecg")
    fmax = 150;
end
if isempty(fs) || isempty(fmax)
    text = "sampling frequency or highest signal frequency not available";
else
    text = sprintf("fs=%.4g Hz, 2*fmax=%.4g Hz", fs, 2 * fmax);
end
end

function status = nyquistStatus(spec, simulation)
fs = firstNumber(spec, ["sampling_frequency_hz", "sample_rate_hz", "fs_hz", "fs"]);
fmax = firstNumber(spec, ["highest_signal_frequency_hz", "max_signal_frequency_hz", "fmax_hz"]);
if isempty(fs)
    fs = firstNumber(simulation, ["sampling_frequency_hz", "sample_rate_hz", "fs_hz", "fs"]);
end
if isempty(fmax)
    fmax = firstNumber(simulation, ["highest_signal_frequency_hz", "max_signal_frequency_hz", "fmax_hz"]);
end
if isempty(fmax) && contains(lower(valueText(spec)), "ecg")
    fmax = 150;
end
if isempty(fs) || isempty(fmax)
    status = "NOT_EVALUATED";
elseif fs >= 2 * fmax
    status = "PASS";
else
    status = "FAIL";
end
end

function text = clippingResult(simulation)
flag = firstLogical(simulation, ["clipping_detected", "output_clipping", "saturation_detected"]);
if isempty(flag)
    text = "clipping metric not logged";
elseif flag
    text = "clipping detected";
else
    text = "none detected";
end
end

function status = clippingStatus(simulation)
flag = firstLogical(simulation, ["clipping_detected", "output_clipping", "saturation_detected"]);
if isempty(flag)
    status = "NOT_EVALUATED";
elseif flag
    status = "FAIL";
else
    status = "PASS";
end
end

function text = attenuationResult(labDelta, simulation)
[value, source] = findMetric(labDelta, ["60", "attenuation", "mains"]);
if isempty(value)
    value = firstNumber(simulation, ["attenuation_60hz_db", "mains_attenuation_db"]);
    source = "simulation";
end
if isempty(value)
    text = "60 Hz attenuation metric not available";
else
    text = sprintf("%.4g dB from %s", value, source);
end
end

function status = attenuationStatus(labDelta, simulation)
[value, ~] = findMetric(labDelta, ["60", "attenuation", "mains"]);
if isempty(value)
    value = firstNumber(simulation, ["attenuation_60hz_db", "mains_attenuation_db"]);
end
if isempty(value)
    status = "NOT_EVALUATED";
elseif value <= -20
    status = "PASS";
elseif value <= -10
    status = "WARN";
else
    status = "FAIL";
end
end

function text = scalarRequirementResult(spec, simulation, names, unit)
value = firstNumber(spec, names);
source = "spec";
if isempty(value)
    value = firstNumber(simulation, names);
    source = "simulation";
end
if isempty(value)
    text = "metric not available";
else
    text = sprintf("%.4g %s from %s", value, unit, source);
end
end

function status = scalarRequirementStatus(spec, simulation, names)
value = firstNumber(spec, names);
if isempty(value)
    value = firstNumber(simulation, names);
end
if isempty(value)
    status = "NOT_EVALUATED";
else
    status = "RECORDED";
end
end

function text = modelCheckResult(modelCheck)
if ~isstruct(modelCheck) || isempty(modelCheck)
    text = "model_check not run";
elseif logicalField(modelCheck, "success", false)
    text = "model update/check succeeded";
else
    text = "model update/check failed";
end
end

function status = passFailNotRun(value)
if ~isstruct(value) || isempty(value)
    status = "NOT_RUN";
elseif logicalField(value, "success", false)
    status = "PASS";
else
    status = "FAIL";
end
end

function text = pathResult(path)
if exist(string(path), "file") == 2
    text = "artifact exists";
else
    text = "artifact missing";
end
end

function status = pathStatus(path)
if exist(string(path), "file") == 2
    status = "PASS";
else
    status = "NOT_RUN";
end
end

function [value, source] = findMetric(report, patterns)
value = [];
source = "";
if ~isstruct(report) || isempty(report) || ~isfield(report, "rows")
    return
end
patterns = lower(string(patterns));
for i = 1:numel(report.rows)
    quantity = lower(fieldString(report.rows(i), "quantity"));
    if any(contains(quantity, patterns))
        value = firstNumber(report.rows(i), ["simulation_value", "measured_value", "hand_value", "result"]);
        source = "Lab Delta row " + fieldString(report.rows(i), "quantity");
        return
    end
end
end

function value = firstNumber(container, names)
value = [];
if ~isstruct(container) || isempty(container)
    return
end
for i = 1:numel(names)
    name = char(names(i));
    if isfield(container, name)
        value = numericValue(container.(name));
        if ~isempty(value)
            return
        end
    end
end
end

function value = firstLogical(container, names)
value = [];
if ~isstruct(container) || isempty(container)
    return
end
for i = 1:numel(names)
    name = char(names(i));
    if isfield(container, name)
        raw = container.(name);
        if islogical(raw) && isscalar(raw)
            value = raw;
            return
        elseif isnumeric(raw) && isscalar(raw)
            value = raw ~= 0;
            return
        elseif isstring(raw) || ischar(raw)
            value = any(lower(string(raw)) == ["true", "yes", "1"]);
            return
        end
    end
end
end

function value = numericValue(raw)
value = [];
if isnumeric(raw) && isscalar(raw)
    value = double(raw);
elseif isstring(raw) || ischar(raw)
    candidate = str2double(raw);
    if ~isnan(candidate)
        value = candidate;
    end
end
end

function tf = logicalField(container, name, defaultValue)
tf = defaultValue;
if isstruct(container) && isfield(container, name)
    raw = container.(name);
    if islogical(raw)
        tf = raw;
    elseif isnumeric(raw)
        tf = raw ~= 0;
    elseif isstring(raw) || ischar(raw)
        tf = any(lower(string(raw)) == ["true", "yes", "1"]);
    end
end
end

function text = fieldString(container, name)
if isstruct(container) && isfield(container, name)
    text = string(container.(name));
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

function summary = summarize(rows)
statuses = string({rows.status});
summary = struct();
summary.pass = sum(statuses == "PASS");
summary.warn = sum(statuses == "WARN");
summary.fail = sum(statuses == "FAIL");
summary.not_run = sum(statuses == "NOT_RUN");
summary.not_evaluated = sum(statuses == "NOT_EVALUATED");
summary.recorded = sum(statuses == "RECORDED");
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Requirement Check"
    ""
    "Created: " + report.created_at
    ""
    "| Requirement | Result | Status | Evidence |"
    "| --- | --- | --- | --- |"
];
for i = 1:numel(report.rows)
    r = report.rows(i);
    lines(end + 1) = "| " + md(r.requirement) + " | " + md(r.result) + " | " + md(r.status) + " | " + md(r.evidence) + " |"; %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
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
