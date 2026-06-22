function report = runParameterSweep(context, options)
%RUNPARAMETERSWEEP Run a lightweight RC tolerance sweep from the circuit spec.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.ParameterSweepReportPath);
markdownPath = optionString(options, "MarkdownPath", config.ParameterSweepMarkdownPath);
spec = readSpec(context);

[rOhm, rId] = firstComponentValue(spec, ["resistor", "resistance", "r"], "ohm");
[cFarad, cId] = firstComponentValue(spec, ["capacitor", "capacitance", "c"], "f");
[targetHz, tolerance] = cutoffTarget(spec);

rTolerances = optionNumberArray(options, "RTolerances", [0.01 0.05]);
cTolerances = optionNumberArray(options, "CTolerances", [0.10 0.20]);
rows = struct("case_id", {}, "r_tolerance_percent", {}, "c_tolerance_percent", {}, ...
    "cutoff_min_hz", {}, "cutoff_nominal_hz", {}, "cutoff_max_hz", {}, ...
    "pass_rate", {}, "status", {});

messages = strings(0, 1);
if isempty(rOhm) || isempty(cFarad)
    messages(end + 1) = "Numeric R/C values were not found. Sweep report records the limitation without inventing results.";
    nominalHz = [];
    worstRange = [];
    mostSensitive = "not evaluated";
    suggestion = "Add numeric resistor/capacitor values to the structured spec or model parameters.";
else
    nominalHz = cutoffHz(rOhm, cFarad);
    for i = 1:numel(rTolerances)
        for j = 1:numel(cTolerances)
            rt = rTolerances(i);
            ct = cTolerances(j);
            rValues = rOhm * [1 - rt, 1, 1 + rt];
            cValues = cFarad * [1 - ct, 1, 1 + ct];
            fc = zeros(numel(rValues), numel(cValues));
            passCount = 0;
            totalCount = 0;
            for ri = 1:numel(rValues)
                for ci = 1:numel(cValues)
                    value = cutoffHz(rValues(ri), cValues(ci));
                    fc(ri, ci) = value;
                    totalCount = totalCount + 1;
                    if isempty(targetHz) || abs(value - targetHz) <= abs(targetHz) * tolerance
                        passCount = passCount + 1;
                    end
                end
            end
            passRate = passCount / totalCount;
            status = "PASS";
            if isempty(targetHz)
                status = "RECORDED";
            elseif passRate < 0.8
                status = "FAIL";
            elseif passRate < 1
                status = "WARN";
            end
            rows(end + 1) = struct( ...
                "case_id", "R" + string(rt * 100) + "_C" + string(ct * 100), ...
                "r_tolerance_percent", rt * 100, ...
                "c_tolerance_percent", ct * 100, ...
                "cutoff_min_hz", min(fc(:)), ...
                "cutoff_nominal_hz", nominalHz, ...
                "cutoff_max_hz", max(fc(:)), ...
                "pass_rate", passRate, ...
                "status", status); %#ok<AGROW>
        end
    end
    allMin = min([rows.cutoff_min_hz]);
    allMax = max([rows.cutoff_max_hz]);
    worstRange = [allMin allMax];
    mostSensitive = "capacitor tolerance";
    if max(rTolerances) > max(cTolerances)
        mostSensitive = "resistor tolerance";
    end
    if isempty(targetHz)
        suggestion = "Record a cutoff target to turn the sweep into a pass/fail robustness check.";
    elseif any(string({rows.status}) == "FAIL" | string({rows.status}) == "WARN")
        suggestion = "Use tighter capacitor tolerance, recalibrate cutoff, or move nominal cutoff away from the requirement edge.";
    else
        suggestion = "Nominal design is robust for the tested tolerance grid.";
    end
end

summary = struct();
summary.resistor_id = rId;
summary.capacitor_id = cId;
summary.nominal_cutoff_hz = numericOrEmpty(nominalHz);
summary.target_cutoff_hz = numericOrEmpty(targetHz);
summary.target_tolerance_percent = tolerance * 100;
summary.worst_case_cutoff_range_hz = numericOrEmpty(worstRange);
summary.most_sensitive_parameter = string(mostSensitive);
summary.suggested_design_change = string(suggestion);

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.analysis_type = "rc_tolerance_sweep";
report.summary = summary;
report.rows = rows;
report.messages = messages;
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

function [value, id] = firstComponentValue(spec, typeHints, unitFamily)
value = [];
id = "";
components = getField(spec, "components");
if isempty(components)
    return
end
for i = 1:numel(components)
    component = components(i);
    text = lower(valueText(component));
    if any(contains(text, lower(string(typeHints))))
        id = fieldText(component, "id");
        if strlength(id) == 0
            id = "component_" + string(i);
        end
        raw = firstField(component, ["value", "nominal_value", "resistance", "capacitance"]);
        value = parseSi(raw, unitFamily);
        if ~isempty(value)
            return
        end
    end
end
end

function [target, tolerance] = cutoffTarget(spec)
target = firstNumber(spec, ["cutoff_frequency_hz", "fc_hz", "target_cutoff_hz"]);
tolerance = 0.10;
if isempty(target)
    text = lower(valueText(spec));
    tokens = regexp(char(text), '(\d+(\.\d+)?)\s*hz', 'tokens');
    if ~isempty(tokens)
        target = str2double(tokens{1}{1});
    elseif contains(text, "ecg") || contains(text, "anti") || contains(text, "alias")
        target = 40;
    end
end
end

function value = cutoffHz(rOhm, cFarad)
value = 1 / (2 * pi * rOhm * cFarad);
end

function value = parseSi(raw, unitFamily)
value = [];
text = lower(strtrim(valueText(raw)));
if strlength(text) == 0
    return
end
tokens = regexp(char(text), '([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zµ]*)', 'tokens', 'once');
if isempty(tokens)
    return
end
base = str2double(tokens{1});
suffix = string(tokens{2});
suffix = replace(suffix, "µ", "u");
factor = 1;
if startsWith(suffix, "meg")
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

function value = firstNumber(container, names)
value = [];
if ~isstruct(container) || isempty(container)
    return
end
for i = 1:numel(names)
    name = char(names(i));
    if isfield(container, name)
        raw = container.(name);
        if isnumeric(raw) && isscalar(raw)
            value = double(raw);
            return
        elseif isstring(raw) || ischar(raw)
            value = str2double(raw);
            if ~isnan(value)
                return
            end
        end
    end
end
end

function value = getField(container, name)
if isstruct(container) && isfield(container, name)
    value = container.(name);
else
    value = [];
end
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

function values = optionNumberArray(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    values = double(options.(fieldName));
else
    values = defaultValue;
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
    "# CiTT Parameter Sweep / Tolerance Analysis"
    ""
    "Created: " + report.created_at
    ""
    "- Nominal cutoff: " + valueText(report.summary.nominal_cutoff_hz) + " Hz"
    "- Worst-case cutoff range: " + valueText(report.summary.worst_case_cutoff_range_hz) + " Hz"
    "- Most sensitive parameter: " + report.summary.most_sensitive_parameter
    "- Suggested design change: " + report.summary.suggested_design_change
    ""
    "| Case | R tol % | C tol % | Cutoff min Hz | Cutoff max Hz | Pass rate | Status |"
    "| --- | --- | --- | --- | --- | --- | --- |"
];
if isempty(report.rows)
    lines(end + 1) = "| not evaluated |  |  |  |  |  | WARN |";
else
    for i = 1:numel(report.rows)
        r = report.rows(i);
        lines(end + 1) = "| " + r.case_id + " | " + string(r.r_tolerance_percent) + " | " + ...
            string(r.c_tolerance_percent) + " | " + sprintf("%.4g", r.cutoff_min_hz) + " | " + ...
            sprintf("%.4g", r.cutoff_max_hz) + " | " + sprintf("%.0f%%", r.pass_rate * 100) + ...
            " | " + r.status + " |"; %#ok<AGROW>
    end
end
if ~isempty(report.messages)
    lines = [lines; ""; "Messages:"; "- " + report.messages(:)];
end
text = strjoin(lines, newline);
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
