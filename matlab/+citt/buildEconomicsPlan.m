function report = buildEconomicsPlan(options)
%BUILDECONOMICSPLAN Export budget and deployment assumptions for CiTT.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(options)
    options = struct();
end

jsonPath = optionString(options, "OutputPath", config.EconomicsPlanPath);
markdownPath = optionString(options, "MarkdownPath", config.EconomicsMarkdownPath);
students = optionNumber(options, "Students", 30);
labsPerCourse = optionNumber(options, "LabsPerCourse", 4);
apiCallsPerLab = optionNumber(options, "ApiCallsPerLab", 3);
assumedApiCostPerCall = optionNumber(options, "AssumedApiCostPerCallUsd", 0.005);
instructorHours = optionNumber(options, "InstructorSetupHours", 4);

totalCalls = students * labsPerCourse * apiCallsPerLab;
estimatedApiCost = totalCalls * assumedApiCostPerCall;

software = [
    item("MATLAB / Simulink / Simscape", "assumed campus license", 0, "Budget separately if no campus license exists.")
    item("Selected agent CLI", sprintf("%d calls at assumed $%.4f/call", totalCalls, assumedApiCostPerCall), estimatedApiCost, "Assumption only; update from current provider billing before purchase.")
    item("CiTT MATLAB plugin", "local toolbox / course deployment", 0, "No per-seat cost modeled for prototype.")
];
hardware = [
    item("Breadboard biomedical circuit kit", "optional per lab team", optionNumber(options, "BreadboardKitUsd", 35), "Resistors, capacitors, jumpers, rails.")
    item("ADC / microcontroller", "optional per lab team", optionNumber(options, "AdcKitUsd", 25), "Only needed for hardware comparison labs.")
    item("ECG/EMG front-end components", "optional per lab team", optionNumber(options, "FrontEndKitUsd", 40), "Use educational isolation/safety policy.")
];
deployment = struct();
deployment.students = students;
deployment.labs_per_course = labsPerCourse;
deployment.api_calls_per_lab = apiCallsPerLab;
deployment.estimated_api_cost_usd = estimatedApiCost;
deployment.instructor_setup_hours = instructorHours;
deployment.assumptions = [
    "MATLAB toolboxes are available through an institution or competition sponsor."
    "API cost is an editable planning assumption, not a live price quote."
    "Hardware kits are optional for simulation-only courses."
];

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.software = software;
report.hardware = hardware;
report.deployment = deployment;
report.total_optional_hardware_per_team_usd = sum([hardware.estimated_cost_usd]);
report.total_estimated_api_cost_usd = estimatedApiCost;
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function row = item(name, assumption, cost, note)
row = struct();
row.name = string(name);
row.assumption = string(assumption);
row.estimated_cost_usd = double(cost);
row.note = string(note);
end

function value = optionNumber(options, fieldName, defaultValue)
value = defaultValue;
if isstruct(options) && isfield(options, fieldName)
    raw = options.(fieldName);
    if isnumeric(raw) && isscalar(raw)
        value = double(raw);
    elseif isstring(raw) || ischar(raw)
        candidate = str2double(raw);
        if ~isnan(candidate)
            value = candidate;
        end
    end
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
    "# CiTT BOM / Cost + Licensing Reality Plan"
    ""
    "Created: " + report.created_at
    ""
    "## Deployment"
    ""
    "- Students: " + string(report.deployment.students)
    "- Labs per course: " + string(report.deployment.labs_per_course)
    "- API calls per lab: " + string(report.deployment.api_calls_per_lab)
    "- Estimated API cost: $" + sprintf("%.2f", report.total_estimated_api_cost_usd)
    "- Instructor setup time: " + string(report.deployment.instructor_setup_hours) + " hours"
    ""
    "## Software"
    ""
    "| Item | Assumption | Estimated Cost | Note |"
    "| --- | --- | --- | --- |"
];
for i = 1:numel(report.software)
    row = report.software(i);
    lines(end + 1) = "| " + md(row.name) + " | " + md(row.assumption) + " | $" + ...
        sprintf("%.2f", row.estimated_cost_usd) + " | " + md(row.note) + " |"; %#ok<AGROW>
end
lines = [lines; ""; "## Optional Hardware"; ""; "| Item | Assumption | Estimated Cost | Note |"; "| --- | --- | --- | --- |"];
for i = 1:numel(report.hardware)
    row = report.hardware(i);
    lines(end + 1) = "| " + md(row.name) + " | " + md(row.assumption) + " | $" + ...
        sprintf("%.2f", row.estimated_cost_usd) + " | " + md(row.note) + " |"; %#ok<AGROW>
end
lines = [lines; ""; "Assumptions:"; "- " + report.deployment.assumptions(:)];
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
