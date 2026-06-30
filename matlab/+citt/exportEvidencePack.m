function result = exportEvidencePack(context, options)
%EXPORTEVIDENCEPACK Export a proposal-ready functional proof package.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

outputPath = config.EvidencePackPath;
if isfield(options, "OutputPath")
    outputPath = string(options.OutputPath);
end

context = normalizeContext(context, config, outputPath);
[spec, specSource] = loadSpec(context);
focusMap = loadJsonArtifact(context.FocusMapPath);
probeMap = loadJsonArtifact(context.ProbeMapPath);
modelCheck = loadModelCheck(context, config);
simulation = loadSimulation(context, config);
labDelta = loadLabDelta(context, config);
requirementReport = loadReport(context, "LastRequirements", config.RequirementReportPath);
sweepReport = loadReport(context, "LastSweep", config.ParameterSweepReportPath);
faultReport = loadReport(context, "LastFaults", config.FaultInjectionReportPath);
explainabilityReport = loadReport(context, "LastExplainability", config.ExplainabilityMapPath);
assessmentReport = loadReport(context, "LastAssessment", config.AssessmentReportPath);
economicsReport = loadReport(context, "LastEconomics", config.EconomicsPlanPath);
scopeReport = loadReport(context, "LastScopeGuardrail", config.ScopeGuardrailPath);

requirements = buildRequirementRows(context, spec, focusMap, probeMap, modelCheck, simulation, labDelta, requirementReport);
limitations = buildLimitations(spec, requirements, simulation, labDelta);
risks = buildRiskRows(spec, labDelta, scopeReport);
functionalProofDraft = buildFunctionalProofDraft(context, requirements, limitations);

lines = strings(0, 1);
lines = appendLines(lines, [
    "# CiTT Performance Evidence Pack"
    ""
    "Generated: " + string(datetime("now", "Format", "yyyy-MM-dd HH:mm:ss"))
    "Purpose: functional proof and technical-feasibility evidence for the CiTT MATLAB plugin workflow."
    ""
]);

lines = appendLines(lines, sourceCircuitSection(context, spec, specSource));
lines = appendLines(lines, structuredSpecSection(spec, specSource));
lines = appendLines(lines, modelArtifactSection(context));
lines = appendLines(lines, modelCheckSection(modelCheck, config));
lines = appendLines(lines, simulationSection(simulation, config));
lines = appendLines(lines, requirementSection(requirements));
lines = appendLines(lines, featureReportSection("6A. Detailed Requirement-to-Simulation Report", config.RequirementReportMarkdownPath, requirementReport));
lines = appendLines(lines, mapSection("7. Focus Map / Highlight Map", context.FocusMapPath, focusMap));
lines = appendLines(lines, mapSection("8. Probe Map", context.ProbeMapPath, probeMap));
lines = appendLines(lines, probeActionSection(context));
lines = appendLines(lines, labDeltaSection(labDelta));
lines = appendLines(lines, featureReportSection("10A. Parameter Sweep / Tolerance Analysis", config.ParameterSweepMarkdownPath, sweepReport));
lines = appendLines(lines, featureReportSection("10B. Risk / Fault Injection", config.FaultInjectionMarkdownPath, faultReport));
lines = appendLines(lines, featureReportSection("10C. Explainability Action Map", config.ExplainabilityMarkdownPath, explainabilityReport));
lines = appendLines(lines, featureReportSection("10D. Learning Gain / Student Assessment", config.AssessmentMarkdownPath, assessmentReport));
lines = appendLines(lines, featureReportSection("10E. BOM / Cost + Licensing Reality", config.EconomicsMarkdownPath, economicsReport));
lines = appendLines(lines, featureReportSection("10F. Regulatory / Scope Guardrail", config.ScopeGuardrailMarkdownPath, scopeReport));
lines = appendLines(lines, limitationsSection(limitations));
lines = appendLines(lines, riskSection(risks));
lines = appendLines(lines, functionalProofSection(functionalProofDraft));
lines = appendLines(lines, artifactIndexSection(context, config, modelCheck, simulation, labDelta));

writeText(outputPath, strjoin(lines, newline));

result = struct();
result.success = true;
result.pack_path = string(outputPath);
result.requirements = requirements;
result.limitations = limitations;
result.risks = risks;
result.functional_proof_draft = functionalProofDraft;
result.status_summary = requirementStatusSummary(requirements);
end

function context = normalizeContext(context, config, outputPath)
defaults = struct();
defaults.ImagePath = "";
defaults.PromptText = "";
defaults.Spec = [];
defaults.SpecPath = config.LastSpecPath;
defaults.AgentTaskPath = config.AgentTaskPath;
defaults.AgentRun = [];
defaults.ModelPath = config.GeneratedModelPath;
defaults.FocusMapPath = config.FocusMapPath;
defaults.ProbeMapPath = config.ProbeMapPath;
defaults.LastModelCheck = [];
defaults.LastSimulation = [];
defaults.LastProbe = [];
defaults.LabCsvPath = "";
defaults.LastLabDelta = [];
defaults.EvidencePackPath = outputPath;
defaults.LastRequirements = [];
defaults.LastSweep = [];
defaults.LastFaults = [];
defaults.LastExplainability = [];
defaults.LastAssessment = [];
defaults.LastEconomics = [];
defaults.LastScopeGuardrail = [];

names = fieldnames(defaults);
for i = 1:numel(names)
    name = names{i};
    if ~isfield(context, name)
        context.(name) = defaults.(name);
    end
end
end

function [spec, source] = loadSpec(context)
spec = [];
source = "";
if isstruct(context.Spec) && ~isempty(context.Spec)
    spec = context.Spec;
    source = "MATLAB app state";
    return
end
path = string(context.SpecPath);
if existFile(path)
    try
        spec = jsondecode(fileread(path));
        source = path;
    catch
        spec = [];
        source = path + " (could not parse)";
    end
end
end

function value = loadJsonArtifact(path)
value = [];
path = string(path);
if ~existFile(path)
    return
end
try
    value = jsondecode(fileread(path));
catch
    value = [];
end
end

function modelCheck = loadModelCheck(context, config)
modelCheck = context.LastModelCheck;
if isstruct(modelCheck) && ~isempty(modelCheck)
    return
end

reportPath = config.ModelCheckReportPath;
modelCheck = [];
if ~existFile(reportPath)
    return
end

reportText = string(fileread(reportPath));
modelCheck = struct();
modelCheck.success = contains(lower(reportText), "success: true") || contains(lower(reportText), "success: 1");
modelCheck.model_path = "";
modelCheck.report_path = string(reportPath);
modelCheck.messages = splitlines(reportText);
modelCheck.error = "";
end

function simulation = loadSimulation(context, config)
simulation = context.LastSimulation;
if isstruct(simulation) && ~isempty(simulation)
    return
end

simulation = loadJsonArtifact(config.SimulationSummaryPath);
end

function labDelta = loadLabDelta(context, config)
labDelta = context.LastLabDelta;
if isstruct(labDelta) && ~isempty(labDelta)
    return
end

labDelta = loadJsonArtifact(config.LabDeltaReportPath);
end

function report = loadReport(context, stateField, path)
report = [];
if isstruct(context) && isfield(context, stateField)
    candidate = context.(stateField);
    if isstruct(candidate) && ~isempty(candidate)
        report = candidate;
        return
    end
end
report = loadJsonArtifact(path);
end

function rows = buildRequirementRows(context, spec, focusMap, probeMap, modelCheck, simulation, labDelta, requirementReport)
rows = struct("requirement", {}, "evidence", {}, "result", {}, "status", {});
if isstruct(requirementReport) && isfield(requirementReport, "rows") && ~isempty(requirementReport.rows)
    for i = 1:numel(requirementReport.rows)
        source = requirementReport.rows(i);
        rows(end + 1) = reqRow( ...
            firstFieldText(source, ["requirement"], "Requirement " + string(i)), ...
            firstFieldText(source, ["evidence"], "Requirement report"), ...
            firstFieldText(source, ["result"], ""), ...
            normalizeStatus(firstFieldText(source, ["status"], "RECORDED"))); %#ok<AGROW>
    end
    return
end

rows(end + 1) = reqRow( ...
    "Original circuit input captured", ...
    artifactEvidence(context.ImagePath, "prompt text"), ...
    capturedInputResult(context), ...
    statusFromFlag(strlength(string(context.ImagePath)) > 0 || strlength(strtrim(string(context.PromptText))) > 0, "PASS", "WARN"));

rows(end + 1) = reqRow( ...
    "Structured circuit spec available", ...
    artifactEvidence(context.SpecPath, "MATLAB app state"), ...
    specAvailableResult(spec), ...
    statusFromFlag(isstruct(spec) && ~isempty(spec), "PASS", "WARN"));

blocking = getSpecBlockingText(spec);
rows(end + 1) = reqRow( ...
    "Spec has no blocking topology ambiguity", ...
    "unsupported_or_unclear_regions / ambiguities", ...
    emptyText(blocking, "no blocking regions recorded"), ...
    statusFromFlag(strlength(blocking) == 0, "PASS", "WARN"));

rows(end + 1) = reqRow( ...
    "Simscape model artifact generated", ...
    context.ModelPath, ...
    pathResult(context.ModelPath), ...
    statusFromFlag(existFile(context.ModelPath), "PASS", "NOT_RUN"));

rows(end + 1) = reqRow( ...
    "Model check completed without update errors", ...
    modelCheckPath(modelCheck), ...
    successResult(modelCheck, "model check"), ...
    statusFromResultStruct(modelCheck));

rows(end + 1) = reqRow( ...
    "Simulation executed and summary captured", ...
    simulationPath(simulation), ...
    simulationResult(simulation), ...
    statusFromSimulation(simulation));

rows(end + 1) = reqRow( ...
    "Focus/highlight map available", ...
    context.FocusMapPath, ...
    mapResult(focusMap), ...
    statusFromFlag(mapCount(focusMap) > 0, "PASS", "NOT_RUN"));

rows(end + 1) = reqRow( ...
    "Probe map or probe action available", ...
    context.ProbeMapPath, ...
    probeResult(probeMap, context.LastProbe), ...
    statusFromFlag(mapCount(probeMap) > 0 || (isstruct(context.LastProbe) && ~isempty(context.LastProbe)), "PASS", "NOT_RUN"));

rows(end + 1) = reqRow( ...
    "Lab Delta comparison available", ...
    labDeltaPath(labDelta), ...
    labDeltaResult(labDelta), ...
    statusFromFlag(isstruct(labDelta) && isfield(labDelta, "rows") && numel(labDelta.rows) > 0, "PASS", "NOT_RUN"));

rows(end + 1) = reqRow( ...
    "Educational scope guardrail stated", ...
    "Evidence Pack risk section", ...
    "pack states educational use, not clinical/device verification", ...
    "PASS");
end

function row = reqRow(requirement, evidence, result, status)
row = struct();
row.requirement = string(requirement);
row.evidence = string(evidence);
row.result = string(result);
row.status = string(status);
end

function text = capturedInputResult(context)
parts = strings(0, 1);
if strlength(string(context.ImagePath)) > 0
    parts(end + 1) = "image path recorded"; %#ok<AGROW>
end
if strlength(strtrim(string(context.PromptText))) > 0
    parts(end + 1) = "prompt recorded"; %#ok<AGROW>
end
text = emptyText(strjoin(parts, ", "), "no source input recorded in app state");
end

function text = specAvailableResult(spec)
if isstruct(spec) && ~isempty(spec)
    text = "structured spec loaded";
    circuitType = fieldText(spec, "circuit_type");
    if strlength(circuitType) > 0
        text = text + ": " + circuitType;
    end
else
    text = "spec missing or unreadable";
end
end

function text = pathResult(path)
if existFile(path)
    text = "file exists";
elseif strlength(string(path)) > 0
    text = "path recorded but file missing";
else
    text = "no path recorded";
end
end

function text = successResult(value, label)
if ~isstruct(value) || isempty(value)
    text = label + " not run";
elseif getLogicalField(value, "success", false)
    text = label + " succeeded";
else
    err = fieldText(value, "error");
    text = label + " failed";
    if strlength(err) > 0
        text = text + ": " + err;
    end
end
end

function text = simulationResult(simulation)
if ~isstruct(simulation) || isempty(simulation)
    text = "simulation not run";
    return
end
if getLogicalField(simulation, "success", false)
    outputs = fieldText(simulation, "output_variables");
    if strlength(outputs) > 0
        text = "simulation succeeded; outputs: " + outputs;
    else
        text = "simulation succeeded; no output variables recorded";
    end
else
    text = successResult(simulation, "simulation");
end
end

function text = mapResult(mapValue)
count = mapCount(mapValue);
if count > 0
    text = string(count) + " map item(s)";
else
    text = "map missing or empty";
end
end

function text = probeResult(probeMap, lastProbe)
count = mapCount(probeMap);
if count > 0
    text = string(count) + " probe map item(s)";
elseif isstruct(lastProbe) && ~isempty(lastProbe)
    text = "last probe action recorded";
else
    text = "probe evidence not recorded";
end
end

function text = labDeltaResult(labDelta)
if isstruct(labDelta) && isfield(labDelta, "rows") && numel(labDelta.rows) > 0
    text = string(numel(labDelta.rows)) + " comparison row(s)";
else
    text = "Lab Delta not run";
end
end

function status = statusFromResultStruct(value)
if ~isstruct(value) || isempty(value)
    status = "NOT_RUN";
elseif getLogicalField(value, "success", false)
    status = "PASS";
else
    status = "FAIL";
end
end

function status = statusFromSimulation(simulation)
if ~isstruct(simulation) || isempty(simulation)
    status = "NOT_RUN";
elseif getLogicalField(simulation, "success", false)
    if isfield(simulation, "output_variables") && numel(simulation.output_variables) > 0
        status = "PASS";
    else
        status = "WARN";
    end
else
    status = "FAIL";
end
end

function status = statusFromFlag(flag, trueStatus, falseStatus)
if flag
    status = string(trueStatus);
else
    status = string(falseStatus);
end
end

function status = normalizeStatus(status)
status = upper(strtrim(string(status)));
if any(status == ["PASS", "WARN", "FAIL", "NOT_RUN"])
    return
end
if status == "NOT_EVALUATED"
    status = "WARN";
elseif status == "RECORDED"
    status = "PASS";
elseif strlength(status) == 0
    status = "WARN";
end
end

function lines = sourceCircuitSection(context, spec, specSource)
promptText = strtrim(string(context.PromptText));
if strlength(promptText) == 0
    promptText = "not recorded";
end

lines = [
    "## 1. Original Circuit / Prompt"
    ""
    artifactLine("Image", context.ImagePath)
    "- **Prompt:** " + promptText
    "- **Spec source:** " + emptyText(specSource, "not available")
    "- **Circuit type:** " + emptyText(fieldText(spec, "circuit_type"), "not specified")
    ""
];
end

function lines = structuredSpecSection(spec, specSource)
lines = [
    "## 2. Structured Circuit Spec"
    ""
];
if ~isstruct(spec) || isempty(spec)
    lines = appendLines(lines, [
        "Structured spec is not available yet."
        ""
    ]);
    return
end

lines = appendLines(lines, [
    "- **Source:** " + emptyText(specSource, "MATLAB app state")
    "- **Likely analysis:** " + emptyText(fieldText(spec, "likely_analysis"), "not specified")
    "- **Components:** " + string(countValue(getFieldValue(spec, "components")))
    "- **Nodes:** " + emptyText(valueToText(getFieldValue(spec, "nodes")), "not specified")
    "- **Requested outputs:** " + emptyText(valueToText(getFieldValue(spec, "requested_outputs")), "not specified")
    ""
    "```json"
    truncateText(string(feval('citt.util.jsonEncode', spec)), 6000)
    "```"
    ""
]);
end

function lines = modelArtifactSection(context)
lines = [
    "## 3. SATK / Simscape Model Artifacts"
    ""
    artifactLine("Generated model", context.ModelPath)
    artifactLine("Agent task", context.AgentTaskPath)
    agentRunLine(context.AgentRun)
    ""
];
end

function lines = modelCheckSection(modelCheck, config)
lines = [
    "## 4. Model Check Result"
    ""
];
if ~isstruct(modelCheck) || isempty(modelCheck)
    lines = appendLines(lines, [
        "Model check has not been run or no report was found."
        artifactLine("Expected report", config.ModelCheckReportPath)
        ""
    ]);
    return
end

lines = appendLines(lines, [
    "- **Status:** " + statusTextFromStruct(modelCheck)
    artifactLine("Report", modelCheckPath(modelCheck))
    ""
    "Messages:"
    listBlock(getFieldValue(modelCheck, "messages"), 18)
    ""
]);
end

function lines = simulationSection(simulation, config)
lines = [
    "## 5. Simulation Curve / Data Summary"
    ""
];
if ~isstruct(simulation) || isempty(simulation)
    lines = appendLines(lines, [
        "Simulation has not been run or no summary JSON was found."
        artifactLine("Expected summary", config.SimulationSummaryPath)
        ""
    ]);
    return
end

plotPath = firstExistingStructPath(simulation, ["plot_path", "figure_path", "screenshot_path"]);
if strlength(plotPath) == 0
    plotLine = "- **Plot/screenshot:** not captured by the current simulation run";
else
    plotLine = artifactLine("Plot/screenshot", plotPath);
end

lines = appendLines(lines, [
    "- **Status:** " + statusTextFromStruct(simulation)
    artifactLine("Summary", simulationPath(simulation))
    plotLine
    "- **Output variables:** " + emptyText(fieldText(simulation, "output_variables"), "none recorded")
    ""
    "Messages:"
    listBlock(getFieldValue(simulation, "messages"), 18)
    ""
]);
end

function lines = requirementSection(requirements)
lines = [
    "## 6. Requirement Pass/Fail Table"
    ""
    "This table uses only evidence currently present in the MATLAB plugin state and saved artifacts."
    ""
];
lines = appendLines(lines, requirementTable(requirements));
lines = appendLines(lines, "");
end

function lines = mapSection(titleText, path, mapValue)
lines = [
    "## " + titleText
    ""
    artifactLine("Artifact", path)
];
items = unwrapMapItems(mapValue);
if isempty(items)
    lines = appendLines(lines, [
        "No map entries were found."
        ""
    ]);
    return
end

lines = appendLines(lines, [
    ""
    "| ID | Label | Model / Block Paths | Teaching Note |"
    "| --- | --- | --- | --- |"
]);
limit = min(numel(items), 12);
for i = 1:limit
    item = items(i);
    id = firstFieldText(item, ["focus_id", "probe_id", "id"], "item_" + string(i));
    label = firstFieldText(item, ["label", "name"], "");
    paths = firstFieldText(item, ["model_paths", "block_paths", "target_paths", "paths"], "");
    note = firstFieldText(item, ["teaching_question", "explanation", "signal", "quantity"], "");
    lines(end + 1) = "| " + mdCell(id) + " | " + mdCell(label) + " | " + mdCell(paths) + " | " + mdCell(note) + " |"; %#ok<AGROW>
end
if numel(items) > limit
    lines(end + 1) = ""; %#ok<AGROW>
    lines(end + 1) = "_Additional map entries omitted from the preview: " + string(numel(items) - limit) + "_"; %#ok<AGROW>
end
lines = appendLines(lines, "");
end

function lines = probeActionSection(context)
lines = [
    "## 9. Last Probe Action"
    ""
];
if isstruct(context.LastProbe) && ~isempty(context.LastProbe)
    lines = appendLines(lines, [
        "```json"
        truncateText(string(feval('citt.util.jsonEncode', context.LastProbe)), 4000)
        "```"
        ""
    ]);
else
    lines = appendLines(lines, [
        "No probe action is recorded in the current app state."
        ""
    ]);
end
end

function lines = labDeltaSection(labDelta)
lines = [
    "## 10. Lab Delta Analysis"
    ""
];
if ~isstruct(labDelta) || isempty(labDelta) || ~isfield(labDelta, "rows") || isempty(labDelta.rows)
    lines = appendLines(lines, [
        "Lab Delta has not been run or no comparison rows were found."
        ""
    ]);
    return
end

lines = appendLines(lines, [
    artifactLine("CSV", fieldText(labDelta, "csv_path"))
    artifactLine("Report", fieldText(labDelta, "report_path"))
    ""
    "| Quantity | Hand | Simulation | Measured | Difference | Status |"
    "| --- | --- | --- | --- | --- | --- |"
]);
for i = 1:numel(labDelta.rows)
    row = labDelta.rows(i);
    pct = numericField(row, "percent_difference");
    if isempty(pct)
        difference = "not comparable";
        status = "WARN";
    else
        difference = sprintf("%.3g%%", pct);
        if abs(pct) <= 10
            status = "PASS";
        elseif abs(pct) <= 20
            status = "WARN";
        else
            status = "INVESTIGATE";
        end
    end
    lines(end + 1) = "| " + mdCell(fieldText(row, "quantity")) + ...
        " | " + mdCell(fieldText(row, "hand_value")) + ...
        " | " + mdCell(fieldText(row, "simulation_value")) + ...
        " | " + mdCell(fieldText(row, "measured_value")) + ...
        " | " + mdCell(difference) + ...
        " | " + mdCell(status) + " |"; %#ok<AGROW>
end

if isfield(labDelta, "likely_causes")
    lines = appendLines(lines, [
        ""
        "Likely causes / checks:"
        listBlock(causeSummary(labDelta.likely_causes), 12)
    ]);
end
lines = appendLines(lines, "");
end

function lines = featureReportSection(titleText, markdownPath, report)
lines = [
    "## " + string(titleText)
    ""
    artifactLine("Markdown report", markdownPath)
];
if ~isstruct(report) || isempty(report)
    lines = appendLines(lines, [
        "Report has not been generated yet."
        ""
    ]);
    return
end

lines = appendLines(lines, [
    artifactLine("JSON report", firstFieldText(report, ["report_path"], ""))
    ""
    "```json"
    truncateText(string(feval('citt.util.jsonEncode', report)), 3500)
    "```"
    ""
]);
end

function lines = limitationsSection(limitations)
lines = [
    "## 11. Limitations"
    ""
    listBlock(limitations, 20)
    ""
];
end

function lines = riskSection(risks)
lines = [
    "## 12. Risk Table"
    ""
    "| Risk | Evidence / Trigger | Mitigation | Severity |"
    "| --- | --- | --- | --- |"
];
for i = 1:numel(risks)
    row = risks(i);
    lines(end + 1) = "| " + mdCell(row.risk) + " | " + mdCell(row.evidence) + " | " + mdCell(row.mitigation) + " | " + mdCell(row.severity) + " |"; %#ok<AGROW>
end
lines = appendLines(lines, "");
end

function lines = functionalProofSection(draft)
lines = [
    "## 13. BMES Functional Proof Draft"
    ""
    draft
    ""
];
end

function lines = artifactIndexSection(context, config, modelCheck, simulation, labDelta)
lines = [
    "## Artifact Index"
    ""
    artifactLine("Circuit image", context.ImagePath)
    artifactLine("Circuit spec", context.SpecPath)
    artifactLine("Agent task", context.AgentTaskPath)
    artifactLine("Generated model", context.ModelPath)
    artifactLine("Focus map", context.FocusMapPath)
    artifactLine("Probe map", context.ProbeMapPath)
    artifactLine("Model check report", modelCheckPathOrDefault(modelCheck, config.ModelCheckReportPath))
    artifactLine("Simulation summary", simulationPathOrDefault(simulation, config.SimulationSummaryPath))
    artifactLine("Lab Delta report", labDeltaPathOrDefault(labDelta, config.LabDeltaReportPath))
    artifactLine("Requirement report", config.RequirementReportMarkdownPath)
    artifactLine("Parameter sweep report", config.ParameterSweepMarkdownPath)
    artifactLine("Fault injection report", config.FaultInjectionMarkdownPath)
    artifactLine("Explainability map report", config.ExplainabilityMarkdownPath)
    artifactLine("Assessment report", config.AssessmentMarkdownPath)
    artifactLine("Economics plan", config.EconomicsMarkdownPath)
    artifactLine("Scope guardrail", config.ScopeGuardrailMarkdownPath)
    "- **Evidence pack:** " + string(context.EvidencePackPath)
    ""
];
end

function tableLines = requirementTable(requirements)
tableLines = [
    "| Requirement | Evidence | Result | Status |"
    "| --- | --- | --- | --- |"
];
for i = 1:numel(requirements)
    row = requirements(i);
    tableLines(end + 1) = "| " + mdCell(row.requirement) + " | " + mdCell(row.evidence) + " | " + mdCell(row.result) + " | " + mdCell(row.status) + " |"; %#ok<AGROW>
end
end

function limitations = buildLimitations(spec, requirements, simulation, labDelta)
limitations = strings(0, 1);

if ~isstruct(spec) || isempty(spec)
    limitations(end + 1) = "No structured circuit spec is available, so topology and component assumptions cannot be audited."; %#ok<AGROW>
else
    blocking = getSpecBlockingText(spec);
    if strlength(blocking) > 0
        limitations(end + 1) = "The spec still contains unresolved ambiguity: " + blocking; %#ok<AGROW>
    end
end

for i = 1:numel(requirements)
    status = string(requirements(i).status);
    if status ~= "PASS"
        limitations(end + 1) = requirements(i).requirement + " is marked " + status + "."; %#ok<AGROW>
    end
end

if ~isstruct(simulation) || isempty(simulation)
    limitations(end + 1) = "No simulation data summary or curve screenshot has been captured in this run."; %#ok<AGROW>
elseif ~isfield(simulation, "output_variables") || isempty(simulation.output_variables)
    limitations(end + 1) = "Simulation completed without recorded output variables; quantitative performance claims should be added after signal logging is configured."; %#ok<AGROW>
end

if ~isstruct(labDelta) || isempty(labDelta) || ~isfield(labDelta, "rows") || isempty(labDelta.rows)
    limitations(end + 1) = "No lab measurement CSV has been compared against simulation yet."; %#ok<AGROW>
end

if isempty(limitations)
    limitations(end + 1) = "No unresolved limitation was detected from the current evidence artifacts; review model assumptions before external use."; %#ok<AGROW>
end
limitations = unique(limitations, "stable");
end

function risks = buildRiskRows(spec, labDelta, scopeReport)
risks = struct("risk", {}, "evidence", {}, "mitigation", {}, "severity", {});
specText = lower(valueToText(spec));

risks(end + 1) = riskRow( ...
    "Student mistakes a teaching model for certified device behavior", ...
    "CiTT generates educational Simscape evidence", ...
    "State scope boundary in every export and show model assumptions before use.", ...
    "Medium");

if containsAny(specText, ["ecg", "emg", "eeg", "electrode", "patient"])
    risks(end + 1) = riskRow( ...
        "Patient-connected circuit hazards are under-modeled", ...
        "Spec appears to involve biosignals or electrodes", ...
        "Require isolation, leakage-current, EMC, and hardware safety review outside CiTT before patient-connected use.", ...
        "High");
else
    risks(end + 1) = riskRow( ...
        "Generated model omits physical safety context", ...
        "No patient-connected trigger detected", ...
        "Keep explicit educational boundary and require instructor review for hardware labs.", ...
        "Medium");
end

if containsAny(specText, ["adc", "sampling", "sample", "alias"])
    risks(end + 1) = riskRow( ...
        "ADC undersampling or aliasing is missed", ...
        "Spec mentions sampling or ADC behavior", ...
        "Add a requirement row for Nyquist margin and verify it from logged simulation data.", ...
        "Medium");
end

if isstruct(labDelta) && isfield(labDelta, "likely_causes")
    causes = lower(causeSummary(labDelta.likely_causes));
    if containsAny(causes, ["unit prefix", "2*pi"])
        risks(end + 1) = riskRow( ...
            "Unit or formula mismatch shifts performance claims", ...
            "Lab Delta flagged a unit/formula check", ...
            "Run parameter sanity checks and display units beside every requirement.", ...
            "Medium");
    end
end
if isstruct(scopeReport) && isfield(scopeReport, "risks")
    for i = 1:numel(scopeReport.risks)
        item = scopeReport.risks(i);
        risks(end + 1) = riskRow( ...
            firstFieldText(item, ["risk"], "Scope risk " + string(i)), ...
            firstFieldText(item, ["trigger", "evidence"], "Scope guardrail"), ...
            firstFieldText(item, ["mitigation"], "Review scope guardrail."), ...
            firstFieldText(item, ["severity"], "Medium")); %#ok<AGROW>
    end
end
end

function row = riskRow(risk, evidence, mitigation, severity)
row = struct();
row.risk = string(risk);
row.evidence = string(evidence);
row.mitigation = string(mitigation);
row.severity = string(severity);
end

function draft = buildFunctionalProofDraft(context, requirements, limitations)
summary = requirementStatusSummary(requirements);
modelText = "the generated Simscape model";
if existFile(context.ModelPath)
    modelText = "the generated Simscape model at " + string(context.ModelPath);
end

draft = strjoin([
    "CiTT demonstrates functional feasibility by turning a circuit image or prompt into auditable MATLAB evidence rather than a standalone chatbot answer."
    "In the current workflow, the selected CLI produces a structured circuit specification; the build step then hands that specification to a Simulink Agentic Toolkit-compatible task, producing " + modelText + "."
    "The Evidence Pack records the original input, the structured spec, model path, focus map, probe map, model-check output, simulation summary, Lab Delta comparison, limitations, and risk controls in one reviewable artifact."
    "For this run, the requirement table contains " + string(summary.pass) + " PASS, " + string(summary.warn) + " WARN, " + string(summary.fail) + " FAIL, and " + string(summary.not_run) + " NOT_RUN items."
    "This makes the proof falsifiable: missing model checks, absent signal logging, unresolved topology ambiguity, or unavailable lab measurements are visible instead of hidden."
    "The teaching value comes from connecting each verification artifact back to focus-map highlights and probe locations, allowing students to inspect why a node, component, or requirement matters."
    "The current scope remains educational and proposal-facing, not medical-device verification."
    "The next strongest evidence would be logged performance requirements, parameter sweeps, and a measured lab CSV for the same circuit."
], " ");

if ~isempty(limitations)
    draft = draft + " Primary current limitation: " + limitations(1);
end
end

function summary = requirementStatusSummary(requirements)
statuses = strings(0, 1);
if ~isempty(requirements)
    statuses = string({requirements.status});
end
summary = struct();
summary.pass = sum(statuses == "PASS");
summary.warn = sum(statuses == "WARN");
summary.fail = sum(statuses == "FAIL");
summary.not_run = sum(statuses == "NOT_RUN");
summary.other = numel(statuses) - summary.pass - summary.warn - summary.fail - summary.not_run;
end

function text = getSpecBlockingText(spec)
parts = strings(0, 1);
if isstruct(spec) && ~isempty(spec)
    if isfield(spec, "unsupported_or_unclear_regions")
        value = valueToText(spec.unsupported_or_unclear_regions);
        if strlength(strtrim(value)) > 0
            parts(end + 1) = value; %#ok<AGROW>
        end
    end
    if isfield(spec, "ambiguities")
        value = valueToText(spec.ambiguities);
        if strlength(strtrim(value)) > 0
            parts(end + 1) = value; %#ok<AGROW>
        end
    end
end
text = strjoin(parts, "; ");
end

function lines = appendLines(lines, moreLines)
lines = [lines(:); string(moreLines(:))];
end

function line = artifactLine(label, path)
path = string(path);
if strlength(path) == 0
    line = "- **" + string(label) + ":** not recorded";
elseif existFile(path)
    line = "- **" + string(label) + ":** " + path;
else
    line = "- **" + string(label) + ":** " + path + " (missing)";
end
end

function text = artifactEvidence(path, defaultText)
path = string(path);
if strlength(path) > 0
    text = path;
else
    text = string(defaultText);
end
end

function line = agentRunLine(agentRun)
if isstruct(agentRun) && ~isempty(agentRun)
    mode = fieldText(agentRun, "mode");
    success = fieldText(agentRun, "success");
    line = "- **Agent run:** recorded";
    if strlength(mode) > 0
        line = line + " (" + mode + ")";
    end
    if strlength(success) > 0
        line = line + ", success=" + success;
    end
else
    line = "- **Agent run:** not recorded in current app state";
end
end

function path = modelCheckPath(modelCheck)
path = fieldText(modelCheck, "report_path");
end

function path = modelCheckPathOrDefault(modelCheck, defaultPath)
path = modelCheckPath(modelCheck);
if strlength(path) == 0
    path = string(defaultPath);
end
end

function path = simulationPath(simulation)
path = fieldText(simulation, "summary_path");
end

function path = simulationPathOrDefault(simulation, defaultPath)
path = simulationPath(simulation);
if strlength(path) == 0
    path = string(defaultPath);
end
end

function path = labDeltaPath(labDelta)
path = fieldText(labDelta, "report_path");
if strlength(path) == 0
    path = fieldText(labDelta, "csv_path");
end
end

function path = labDeltaPathOrDefault(labDelta, defaultPath)
path = labDeltaPath(labDelta);
if strlength(path) == 0
    path = string(defaultPath);
end
end

function text = statusTextFromStruct(value)
if getLogicalField(value, "success", false)
    text = "PASS";
else
    text = "FAIL";
end
end

function text = listBlock(value, maxItems)
parts = valueToList(value);
if isempty(parts)
    text = "- none";
    return
end
limit = min(numel(parts), maxItems);
lines = strings(limit, 1);
for i = 1:limit
    lines(i) = "- " + parts(i);
end
if numel(parts) > limit
    lines(end + 1) = "- ... " + string(numel(parts) - limit) + " more";
end
text = strjoin(lines, newline);
end

function parts = valueToList(value)
if isempty(value)
    parts = strings(0, 1);
elseif isstring(value)
    parts = value(:);
elseif ischar(value)
    parts = splitlines(string(value));
elseif iscell(value)
    parts = strings(0, 1);
    for i = 1:numel(value)
        parts = [parts; valueToList(value{i})]; %#ok<AGROW>
    end
elseif isstruct(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value(i));
    end
elseif isnumeric(value) || islogical(value)
    parts = string(value(:));
else
    parts = string(value);
end
parts = parts(strlength(strtrim(parts)) > 0);
end

function text = fieldText(value, fieldName)
if isstruct(value) && ~isempty(value) && isfield(value, char(fieldName))
    text = valueToText(value.(char(fieldName)));
else
    text = "";
end
end

function value = getFieldValue(container, fieldName)
if isstruct(container) && ~isempty(container) && isfield(container, char(fieldName))
    value = container.(char(fieldName));
else
    value = [];
end
end

function text = firstFieldText(value, fieldNames, defaultValue)
text = string(defaultValue);
for i = 1:numel(fieldNames)
    name = char(fieldNames(i));
    if isstruct(value) && isfield(value, name)
        text = valueToText(value.(name));
        return
    end
end
end

function tf = getLogicalField(value, fieldName, defaultValue)
tf = defaultValue;
if ~isstruct(value) || isempty(value) || ~isfield(value, char(fieldName))
    return
end
raw = value.(char(fieldName));
if islogical(raw)
    tf = logical(raw);
elseif isnumeric(raw)
    tf = raw ~= 0;
elseif isstring(raw) || ischar(raw)
    tf = any(lower(string(raw)) == ["true", "1", "yes"]);
end
end

function count = countValue(value)
if isempty(value)
    count = 0;
else
    count = numel(value);
end
end

function text = valueToText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isnumeric(value)
    if isscalar(value)
        text = string(value);
    else
        text = string(mat2str(value));
    end
elseif islogical(value)
    text = string(value);
elseif isstruct(value)
    if numel(value) == 1
        if isfield(value, "label")
            text = string(value.label);
        elseif isfield(value, "id")
            text = string(value.id);
        elseif isfield(value, "focus_id")
            text = string(value.focus_id);
        else
            text = string(feval('citt.util.jsonEncode', value));
        end
    else
        parts = strings(numel(value), 1);
        for i = 1:numel(value)
            parts(i) = valueToText(value(i));
        end
        text = strjoin(parts(:)', ", ");
    end
else
    text = string(value);
end
end

function text = emptyText(value, defaultText)
value = strtrim(string(value));
if strlength(value) == 0
    text = string(defaultText);
else
    text = value;
end
end

function text = truncateText(text, maxChars)
text = string(text);
if strlength(text) <= maxChars
    return
end
text = extractBefore(text, maxChars + 1) + newline + "... [truncated]";
end

function cellText = mdCell(value)
cellText = string(value);
cellText = replace(cellText, newline, "<br>");
cellText = replace(cellText, "|", "\|");
cellText = truncateText(cellText, 500);
if strlength(cellText) == 0
    cellText = " ";
end
end

function items = unwrapMapItems(mapValue)
if ~isstruct(mapValue) || isempty(mapValue)
    items = struct([]);
elseif isfield(mapValue, "focus_map")
    items = mapValue.focus_map;
elseif isfield(mapValue, "probe_map")
    items = mapValue.probe_map;
elseif isfield(mapValue, "items")
    items = mapValue.items;
elseif isfield(mapValue, "probes")
    items = mapValue.probes;
else
    items = mapValue;
end
if ~isstruct(items)
    items = struct([]);
end
end

function count = mapCount(mapValue)
items = unwrapMapItems(mapValue);
count = numel(items);
end

function path = firstExistingStructPath(value, fieldNames)
path = "";
for i = 1:numel(fieldNames)
    candidate = fieldText(value, fieldNames(i));
    if strlength(candidate) > 0
        path = candidate;
        return
    end
end
end

function value = numericField(container, fieldName)
value = [];
if ~isstruct(container) || ~isfield(container, char(fieldName))
    return
end
raw = container.(char(fieldName));
if isnumeric(raw) && isscalar(raw)
    value = double(raw);
elseif isstring(raw) || ischar(raw)
    candidate = str2double(raw);
    if ~isnan(candidate)
        value = candidate;
    end
end
end

function text = causeSummary(causes)
parts = strings(0, 1);
if ~isstruct(causes)
    text = parts;
    return
end
for i = 1:numel(causes)
    label = firstFieldText(causes(i), ["label", "id"], "cause_" + string(i));
    severity = firstFieldText(causes(i), ["severity"], "");
    explanation = firstFieldText(causes(i), ["explanation"], "");
    item = label;
    if strlength(severity) > 0
        item = item + " (" + severity + ")";
    end
    if strlength(explanation) > 0
        item = item + ": " + explanation;
    end
    parts(end + 1) = item; %#ok<AGROW>
end
text = parts;
end

function tf = containsAny(text, patterns)
text = string(text);
patterns = string(patterns);
tf = false;
for i = 1:numel(patterns)
    if any(contains(text, patterns(i), "IgnoreCase", true))
        tf = true;
        return
    end
end
end

function tf = existFile(path)
path = string(path);
tf = strlength(path) > 0 && isfile(path);
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid < 0
    error("CiTT:EvidencePackWriteFailed", "Could not write evidence pack: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end
