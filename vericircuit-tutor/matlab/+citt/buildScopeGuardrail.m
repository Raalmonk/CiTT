function report = buildScopeGuardrail(context, options)
%BUILDSCOPEGUARDRAIL Export educational/regulatory scope guardrails.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

context = normalizeContext(context, config);
jsonPath = optionString(options, "OutputPath", config.ScopeGuardrailPath);
markdownPath = optionString(options, "MarkdownPath", config.ScopeGuardrailMarkdownPath);
spec = readSpec(context);
specText = lower(valueText(spec));
patientConnected = containsAny(specText, ["ecg", "emg", "eeg", "electrode", "patient", "bioelectric", "biopotential"]);

boundaries = [
    "This model is educational and proposal-facing."
    "This is not clinical diagnosis."
    "This is not medical-device verification."
    "Generated model behavior depends on explicit assumptions, component values, and solver configuration."
];
if patientConnected
    category = "educational design-training tool with patient-connected-topic warnings";
    standards = ["isolation/leakage-current review"; "EMC review"; "front-end safety review"; "institutional lab safety policy"];
else
    category = "educational software / design training tool, not patient-facing device software";
    standards = ["instructor review"; "model-assumption display"; "hardware lab safety policy if physical circuits are used"];
end

risks = struct("risk", {}, "trigger", {}, "mitigation", {}, "severity", {});
risks(end + 1) = riskRow("Student mistakes simulation for certified device behavior", ...
    "Any generated model or performance table", ...
    "Display educational boundary and assumptions in every export.", "Medium");
if patientConnected
    risks(end + 1) = riskRow("Generated circuit omits patient isolation or leakage-current constraints", ...
        "Spec contains biomedical/patient-connected terms", ...
        "Warn that patient-connected hardware needs separate isolation, leakage, and EMC analysis.", "High");
else
    risks(end + 1) = riskRow("Hardware lab context exceeds simulation scope", ...
        "Spec does not include explicit safety constraints", ...
        "Require instructor review before building physical circuits.", "Medium");
end
risks(end + 1) = riskRow("LLM parse error becomes hidden design assumption", ...
    "Gemini structured spec drives model generation", ...
    "Expose parsed spec, assumptions, ambiguities, and model-check status in Evidence Pack.", "Medium");

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.patient_connected_trigger_detected = patientConnected;
report.potential_regulatory_category = category;
report.boundaries = boundaries;
report.additional_standards_to_consider = standards;
report.risks = risks;
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

function row = riskRow(risk, trigger, mitigation, severity)
row = struct();
row.risk = string(risk);
row.trigger = string(trigger);
row.mitigation = string(mitigation);
row.severity = string(severity);
end

function tf = containsAny(text, patterns)
tf = false;
for i = 1:numel(patterns)
    if contains(text, patterns(i), "IgnoreCase", true)
        tf = true;
        return
    end
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

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Regulatory / Scope Guardrail"
    ""
    "Created: " + report.created_at
    ""
    "- Potential regulatory category: " + report.potential_regulatory_category
    "- Patient-connected trigger detected: " + string(report.patient_connected_trigger_detected)
    ""
    "## Boundaries"
    ""
    "- " + report.boundaries(:)
    ""
    "## Standards / Reviews To Consider"
    ""
    "- " + report.additional_standards_to_consider(:)
    ""
    "## Risks"
    ""
    "| Risk | Trigger | Mitigation | Severity |"
    "| --- | --- | --- | --- |"
];
for i = 1:numel(report.risks)
    r = report.risks(i);
    lines(end + 1) = "| " + md(r.risk) + " | " + md(r.trigger) + " | " + md(r.mitigation) + " | " + md(r.severity) + " |"; %#ok<AGROW>
end
text = strjoin(lines, newline);
end

function text = md(value)
text = replace(string(value), "|", "\|");
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
