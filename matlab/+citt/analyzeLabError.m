function report = analyzeLabError(labCsvPath, context, options)
%ANALYZELABERROR Diagnose lab/simulation mismatch from CSV and CiTT artifacts.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(labCsvPath)
    labCsvPath = "";
end
if nargin < 2 || isempty(context)
    context = struct();
end
if nargin < 3 || isempty(options)
    options = struct();
end

labCsvPath = string(labCsvPath);
if strlength(labCsvPath) == 0
    labCsvPath = contextText(context, "LabCsvPath", "");
end
if strlength(labCsvPath) == 0 || exist(labCsvPath, "file") ~= 2
    error("CiTT:LabCsvMissing", "Lab CSV file not found: %s", labCsvPath);
end

outputPath = optionText(options, "OutputPath", config.LabDeltaReportPath);
markdownPath = optionText(options, "MarkdownPath", config.LabErrorMarkdownPath);
specPath = contextText(context, "SpecPath", config.LastSpecPath);
probeMapPath = contextText(context, "ProbeMapPath", config.ProbeMapPath);

parsed = readLabCsv(labCsvPath);
spec = contextStruct(context, "Spec");
if ~isstruct(spec) || isempty(fieldnames(spec))
    spec = readJsonIfPresent(specPath);
end
probeMap = readJsonIfPresent(probeMapPath);
profiles = mergeProfiles( ...
    feval('citt.opAmpNonidealProfile', spec), ...
    feval('citt.opAmpNonidealProfile', contextText(context, "OpAmpPart", "")));
handValues = contextStruct(context, "HandValues");
simulationValues = contextStruct(context, "SimulationValues");

rows = parsed.rows;
for i = 1:numel(rows)
    rows(i) = applyExternalReferences(rows(i), handValues, simulationValues);
    rows(i) = attachProbeContext(rows(i), probeMap);
    rows(i) = finalizeComparison(rows(i));
end

modelCheck = contextStruct(context, "LastModelCheck");
simulation = contextStruct(context, "LastSimulation");
diagnostics = buildDiagnostics(rows, parsed, spec, probeMap, profiles, modelCheck, simulation);

report = struct();
report.success = true;
report.csv_path = labCsvPath;
report.report_path = string(outputPath);
report.markdown_report_path = string(markdownPath);
report.spec_path = string(specPath);
report.probe_map_path = string(probeMapPath);
report.nonideal_profiles = profiles;
report.detected_columns = parsed.detected_columns;
report.rows = rows;
report.likely_causes = diagnostics;
report.next_probe_suggestion = nextProbeSuggestion(rows, diagnostics);
report.prioritized_next_actions = nextActions(diagnostics);
report.notes = parsed.notes;

writeJson(outputPath, report);
writeMarkdown(markdownPath, report);
end

function parsed = readLabCsv(labCsvPath)
tbl = readtable(labCsvPath, "TextType", "string", "VariableNamingRule", "preserve");
names = string(tbl.Properties.VariableNames);
lowerNames = lower(normalizeName(names));

timeIndex = firstIndex(lowerNames, ["time", "t", "seconds", "second", "sec", "ms"]);
quantityIndex = firstIndex(lowerNames, ["quantity", "name", "signal", "probe", "channel"]);
unitIndex = firstIndex(lowerNames, ["unit", "units"]);
measuredIndex = firstIndex(lowerNames, ["measured", "measurement", "lab", "value", "actual"]);
handIndex = firstIndex(lowerNames, ["hand", "handvalue", "hand_value", "calculated", "analytic", "expected_hand"]);
simIndex = firstIndex(lowerNames, ["simulation", "sim", "simvalue", "simulation_value", "model", "reference", "expected"]);

parsed = struct();
parsed.detected_columns = struct( ...
    "names", names(:), ...
    "time", columnName(names, timeIndex), ...
    "quantity", columnName(names, quantityIndex), ...
    "unit", columnName(names, unitIndex), ...
    "measured", columnName(names, measuredIndex), ...
    "hand", columnName(names, handIndex), ...
    "simulation", columnName(names, simIndex));
parsed.notes = strings(0, 1);

if height(tbl) == 0
    parsed.rows = emptyRows();
    parsed.notes(end + 1) = "CSV has headers but no rows.";
    return
end

if ~isempty(quantityIndex) && ~isempty(measuredIndex)
    parsed.rows = readLongRows(tbl, names, quantityIndex, unitIndex, measuredIndex, handIndex, simIndex, timeIndex);
else
    parsed.rows = readWideRows(tbl, names, timeIndex);
end

if isempty(parsed.rows)
    parsed.rows = emptyRows();
    parsed.notes(end + 1) = "No numeric lab measurement columns were found.";
end

if isempty(timeIndex)
    parsed.notes(end + 1) = "No time column was detected, so settling and transient checks are limited.";
else
    timeValues = columnNumbers(tbl, timeIndex);
    if numel(timeValues) > 1 && any(diff(timeValues(~isnan(timeValues))) < 0)
        parsed.notes(end + 1) = "Time column is not monotonic.";
    end
end
end

function rows = readLongRows(tbl, ~, quantityIndex, unitIndex, measuredIndex, handIndex, simIndex, timeIndex)
quantities = string(tbl{:, quantityIndex});
uniqueQuantities = unique(quantities);
rows = emptyRows();
for i = 1:numel(uniqueQuantities)
    quantity = uniqueQuantities(i);
    if strlength(strtrim(quantity)) == 0
        continue
    end
    mask = quantities == quantity;
    row = baseRow(quantity);
    row.unit = firstString(tbl, find(mask, 1), unitIndex);
    row = applySeriesStats(row, columnNumbers(tbl(mask, :), measuredIndex), columnNumbers(tbl(mask, :), timeIndex));
    row.hand_value = scalarFromValues(columnNumbers(tbl(mask, :), handIndex));
    row.simulation_value = scalarFromValues(columnNumbers(tbl(mask, :), simIndex));
    rows = appendRow(rows, row);
end
end

function rows = readWideRows(tbl, names, timeIndex)
rows = emptyRows();
lowerNames = lower(normalizeName(names));
numericMask = false(size(names));
for i = 1:numel(names)
    values = columnNumbers(tbl, i);
    numericMask(i) = any(~isnan(values));
end

referenceMask = contains(lowerNames, "sim") | contains(lowerNames, "model") | ...
    contains(lowerNames, "reference") | contains(lowerNames, "expected") | contains(lowerNames, "hand");
measurementIndexes = find(numericMask & ~referenceMask);
measurementIndexes(measurementIndexes == timeIndex) = [];

timeValues = columnNumbers(tbl, timeIndex);
for i = 1:numel(measurementIndexes)
    idx = measurementIndexes(i);
    quantity = stripMeasurementName(names(idx));
    row = baseRow(quantity);
    row = applySeriesStats(row, columnNumbers(tbl, idx), timeValues);

    simIdx = matchingReferenceColumn(names, idx, ["sim", "simulation", "model", "reference", "expected"]);
    handIdx = matchingReferenceColumn(names, idx, ["hand", "analytic", "calculated"]);
    row.simulation_value = scalarFromValues(columnNumbers(tbl, simIdx));
    row.hand_value = scalarFromValues(columnNumbers(tbl, handIdx));
    rows = appendRow(rows, row);
end
end

function row = baseRow(quantity)
row = struct();
row.quantity = string(quantity);
row.unit = "";
row.measured_value = [];
row.hand_value = [];
row.simulation_value = [];
row.reference_source = "";
row.absolute_difference = [];
row.percent_difference = [];
row.status = "NO_REFERENCE";
row.sample_count = 0;
row.mean_value = [];
row.std_value = [];
row.min_value = [];
row.max_value = [];
row.first_value = [];
row.final_value = [];
row.time_start = [];
row.time_end = [];
row.probe_id = "";
row.probe_label = "";
row.probe_unit = "";
row.notes = strings(0, 1);
end

function rows = emptyRows()
rows = repmat(baseRow(""), 0, 1);
end

function rows = appendRow(rows, row)
if isempty(rows)
    rows = row;
else
    rows(end + 1, 1) = row; %#ok<AGROW>
end
end

function row = applySeriesStats(row, values, timeValues)
values = values(:);
values = values(~isnan(values));
row.sample_count = numel(values);
if isempty(values)
    row.notes(end + 1) = "No numeric measured values for this quantity.";
    return
end
row.measured_value = values(end);
row.final_value = values(end);
row.first_value = values(1);
row.mean_value = mean(values, "omitnan");
row.std_value = std(values, "omitnan");
row.min_value = min(values);
row.max_value = max(values);

timeValues = timeValues(:);
timeValues = timeValues(~isnan(timeValues));
if ~isempty(timeValues)
    row.time_start = timeValues(1);
    row.time_end = timeValues(end);
end
end

function row = applyExternalReferences(row, handValues, simulationValues)
quantityKey = matlab.lang.makeValidName(char(row.quantity));
if isempty(row.hand_value) && isstruct(handValues) && isfield(handValues, quantityKey)
    row.hand_value = numericScalar(handValues.(quantityKey));
end
if isempty(row.simulation_value) && isstruct(simulationValues) && isfield(simulationValues, quantityKey)
    row.simulation_value = numericScalar(simulationValues.(quantityKey));
end
end

function row = attachProbeContext(row, probeMap)
items = unwrapItems(probeMap, "probe_map");
bestIndex = 0;
bestScore = 0;
query = lower(normalizeName(row.quantity));
for i = 1:numel(items)
    text = lower(string(feval('citt.util.jsonEncode', items(i))));
    score = 0;
    if contains(text, query)
        score = score + strlength(query);
    end
    tokens = split(query, "_");
    for j = 1:numel(tokens)
        if strlength(tokens(j)) > 1 && contains(text, tokens(j))
            score = score + strlength(tokens(j));
        end
    end
    if score > bestScore
        bestScore = score;
        bestIndex = i;
    end
end
if bestIndex > 0 && bestScore >= 2
    probe = items(bestIndex);
    row.probe_id = fieldText(probe, "probe_id");
    row.probe_label = fieldText(probe, "label");
    row.probe_unit = fieldText(probe, "unit");
    if strlength(row.unit) > 0 && strlength(row.probe_unit) > 0 && lower(row.unit) ~= lower(row.probe_unit)
        row.notes(end + 1) = "CSV unit differs from probe map unit: " + row.unit + " vs " + row.probe_unit + ".";
    end
else
    row.notes(end + 1) = "No matching probe-map entry was found for this lab quantity.";
end
end

function row = finalizeComparison(row)
reference = row.simulation_value;
row.reference_source = "simulation";
if isempty(reference)
    reference = row.hand_value;
    row.reference_source = "hand";
end

if isempty(row.measured_value)
    row.status = "NO_MEASUREMENT";
    return
end
if isempty(reference)
    row.status = "NO_REFERENCE";
    row.notes(end + 1) = "No hand/simulation reference was available for numeric error calculation.";
    return
end
if reference == 0
    row.absolute_difference = row.measured_value - reference;
    row.status = "ZERO_REFERENCE";
    row.notes(end + 1) = "Reference is zero, so percent difference is undefined.";
    return
end

row.absolute_difference = row.measured_value - reference;
row.percent_difference = 100 * row.absolute_difference / reference;
absPct = abs(row.percent_difference);
if absPct <= 5
    row.status = "PASS";
elseif absPct <= 15
    row.status = "WARN";
else
    row.status = "INVESTIGATE";
end
end

function diagnostics = buildDiagnostics(rows, parsed, spec, probeMap, profiles, modelCheck, simulation)
diagnostics = repmat(diagnostic("", "", "", "", "", ""), 0, 1);
diagnostics = addContextDiagnostics(diagnostics, rows, parsed, spec, probeMap, profiles, modelCheck, simulation);
for i = 1:numel(rows)
    diagnostics = addRowDiagnostics(diagnostics, rows(i), spec, profiles);
end
diagnostics = addCrossRowReadoutDiagnostics(diagnostics, rows);
diagnostics = prioritizeDiagnostics(diagnostics);
end

function diagnostics = addContextDiagnostics(diagnostics, rows, parsed, spec, probeMap, profiles, modelCheck, simulation)
if isempty(rows)
    diagnostics = addDiagnostic(diagnostics, "csv_no_measurements", "CSV has no comparable numeric measurements", ...
        "critical", "CiTT could not find lab measurement values in the selected CSV.", ...
        strjoin(parsed.notes, "; "), "Export quantity/unit/measured/simulation columns or a wide table with numeric measurement columns.");
end

if any([rows.status] == "NO_REFERENCE")
    diagnostics = addDiagnostic(diagnostics, "missing_reference", "Missing hand/simulation reference", ...
        "warning", "Some lab quantities cannot be converted into percent error without a hand or simulation baseline.", ...
        "Rows: " + rowList(rows, "NO_REFERENCE"), "Add simulation/reference/expected columns or run a simulation export for the same probes.");
end

if isfield(parsed.detected_columns, "time") && strlength(parsed.detected_columns.time) == 0
    diagnostics = addDiagnostic(diagnostics, "missing_time_axis", "No time column", ...
        "check", "Settling, transient capture, and sampling-rate errors cannot be ruled out without time data.", ...
        "CSV columns: " + strjoin(parsed.detected_columns.names(:)', ", "), "Include a time column in seconds for lab captures.");
end

if isstruct(modelCheck) && isfield(modelCheck, "success") && ~logical(modelCheck.success)
    diagnostics = addDiagnostic(diagnostics, "model_check_failed", "Model check failed", ...
        "critical", "The simulation baseline may be invalid because the model check did not pass.", ...
        fieldText(modelCheck, "error"), "Fix model check errors before comparing lab data.");
elseif ~isstruct(modelCheck) || isempty(modelCheck)
    diagnostics = addDiagnostic(diagnostics, "model_check_missing", "Model check not available", ...
        "check", "CiTT has no current model-check result attached to this lab comparison.", ...
        "", "Run Model > Check before using lab data as evidence.");
end

if isstruct(simulation) && isfield(simulation, "success") && ~logical(simulation.success)
    diagnostics = addDiagnostic(diagnostics, "simulation_failed", "Simulation failed", ...
        "critical", "The simulation reference may be missing or stale.", ...
        fieldText(simulation, "error"), "Fix simulation errors, then compare against fresh lab data.");
elseif ~isstruct(simulation) || isempty(simulation)
    diagnostics = addDiagnostic(diagnostics, "simulation_missing", "Simulation result not attached", ...
        "check", "No current simulation summary is attached to this lab comparison.", ...
        "", "Run Model > Simulate or include simulation/reference columns in the lab CSV.");
end

if isempty(unwrapItems(probeMap, "probe_map"))
    diagnostics = addDiagnostic(diagnostics, "probe_map_missing", "Probe map missing", ...
        "warning", "CiTT cannot verify that lab CSV quantities correspond to SATK-generated probes.", ...
        "", "Build or reload the SATK probe map, then place probes before lab comparison.");
end

if ~isempty(profiles)
    diagnostics = addProfileContextDiagnostics(diagnostics, profiles, spec);
end

assumptionText = lower(string(feval('citt.util.jsonEncode', spec)));
if containsAny(assumptionText, ["ideal", "ignored", "simplified", "equilibrium", "fully charged", "capacit", "ion channel"])
    diagnostics = addDiagnostic(diagnostics, "model_assumption_gap", "Model assumption may not match lab hardware", ...
        "possible", "The circuit spec includes idealized or simplified assumptions that can produce lab/model mismatch.", ...
        assumptionExcerpt(spec), "Check which assumptions are invalid in the lab setup before treating the error as a component fault.");
end
end

function diagnostics = addProfileContextDiagnostics(diagnostics, profiles, spec)
for i = 1:numel(profiles)
    profile = profiles(i);
    if string(profile.part_number) == "LM741"
        diagnostics = addDiagnostic(diagnostics, "lm741_nonideal_profile", "LM741 nonideal op-amp effects", ...
            "possible", "LM741 is not an ideal infinite-input-impedance op-amp; input bias current and offset voltage can create measurable DC error.", ...
            profileSummary(profile), "Model LM741 with explicit input bias current sources, input offset voltage, finite input resistance, finite gain, and output limits.");
        if specMentionsIdealOpAmp(spec)
            diagnostics = addDiagnostic(diagnostics, "lm741_ideal_model_mismatch", "LM741 modeled as ideal op-amp", ...
                "warning", "The circuit spec still contains ideal-op-amp assumptions while an LM741 profile is active.", ...
                assumptionExcerpt(spec), "Rebuild or edit the model so the LM741 nonidealities are included rather than relying on the ideal Op-Amp block.");
        end
    end
end
end

function diagnostics = addRowDiagnostics(diagnostics, row, spec, profiles)
if row.status == "INVESTIGATE"
    diagnostics = addDiagnostic(diagnostics, "large_error_" + validId(row.quantity), "Large error in " + row.quantity, ...
        "likely", "Measured value differs from the reference by more than 15%.", ...
        rowEvidence(row), "Check units, reference node, probe placement, and settling for this quantity first.");
end

if isResistanceLike(row) && ~isempty(row.percent_difference) && abs(row.percent_difference) > 5
    severity = "possible";
    if abs(row.percent_difference) > 20
        severity = "likely";
    end
    diagnostics = addDiagnostic(diagnostics, "resistor_value_readback_" + validId(row.quantity), "Resistor value or readback error", ...
        severity, "A resistance-related row differs from its reference beyond normal tight-tolerance expectations.", ...
        rowEvidence(row), "Verify resistor color code/DMM reading, nominal-vs-actual value, temperature coefficient, and whether the model used the measured resistance.");
end

if ~isempty(row.simulation_value) && ~isempty(row.measured_value) && row.simulation_value ~= 0
    ratio = row.measured_value / row.simulation_value;
    if ratio < -0.8 && ratio > -1.25
        diagnostics = addDiagnostic(diagnostics, "sign_reference_" + validId(row.quantity), "Sign or reference-node mismatch", ...
            "likely", "Measured value is approximately the negative of the simulation reference.", ...
            rowEvidence(row), "Verify current direction, voltage reference node, and probe polarity.");
    end
    if nearRatio(abs(ratio), 2*pi)
        diagnostics = addDiagnostic(diagnostics, "two_pi_" + validId(row.quantity), "2*pi error", ...
            "likely", "The measured/reference ratio is close to 2*pi or 1/(2*pi).", ...
            rowEvidence(row), "Check whether one side used Hz and the other used rad/s.");
    end
    if nearAny(abs(ratio), [1e-9 1e-6 1e-3 1e3 1e6 1e9])
        diagnostics = addDiagnostic(diagnostics, "unit_prefix_" + validId(row.quantity), "Metric prefix or unit scaling mismatch", ...
            "likely", "The measured/reference ratio is close to a metric prefix factor.", ...
            rowEvidence(row), "Check m/u/n/k/M prefixes and instrument display units.");
    end
    if nearAny(abs(ratio), [0.1 10])
        diagnostics = addDiagnostic(diagnostics, "scope_probe_scale_" + validId(row.quantity), "10x probe or input attenuation setting", ...
            "likely", "The measured/reference ratio is close to 10x or 0.1x.", ...
            rowEvidence(row), "Check oscilloscope probe attenuation, DAQ input range, and software scaling.");
    end
end

if ~isempty(profiles)
    diagnostics = addOpAmpProfileRowDiagnostics(diagnostics, row, spec, profiles);
end

if row.sample_count > 3 && ~isempty(row.first_value) && ~isempty(row.final_value)
    scale = max(abs([row.final_value, row.mean_value, 1]));
    drift = abs(row.final_value - row.first_value) / scale;
    if drift > 0.05
        diagnostics = addDiagnostic(diagnostics, "not_settled_" + validId(row.quantity), "Transient or not-settled capture", ...
            "possible", "The first and final lab samples differ by more than 5% of the signal scale.", ...
            rowEvidence(row), "Compare only after settling or extend the simulation/lab capture window.");
    end
end

if row.sample_count > 5 && ~isempty(row.std_value) && ~isempty(row.mean_value)
    noiseRatio = row.std_value / max(abs(row.mean_value), eps);
    if noiseRatio > 0.05
        diagnostics = addDiagnostic(diagnostics, "noise_" + validId(row.quantity), "Measurement noise or unstable signal", ...
            "possible", "The lab signal standard deviation is more than 5% of its mean.", ...
            rowEvidence(row), "Check grounding, averaging, bandwidth limits, and probe loading.");
    end
end

if any(contains(row.notes, "probe-map", "IgnoreCase", true))
    diagnostics = addDiagnostic(diagnostics, "probe_missing_" + validId(row.quantity), "Lab quantity not covered by probe map", ...
        "warning", "The CSV quantity does not clearly map to an SATK-generated probe.", ...
        row.quantity, "Add or rename a probe so lab and simulation signals align.");
end

if any(contains(row.notes, "unit differs", "IgnoreCase", true))
    diagnostics = addDiagnostic(diagnostics, "probe_unit_" + validId(row.quantity), "Probe unit mismatch", ...
        "warning", "The CSV unit differs from the probe-map unit.", ...
        strjoin(row.notes, "; "), "Normalize units before comparing numeric values.");
end
end

function diagnostics = addOpAmpProfileRowDiagnostics(diagnostics, row, spec, profiles)
if isempty(row.measured_value)
    return
end

for i = 1:numel(profiles)
    profile = profiles(i);
    if string(profile.part_number) ~= "LM741"
        continue
    end
    if ~isVoltageLike(row)
        continue
    end

    observedError = abs(row.absolute_difference);
    if isempty(observedError) && ~isempty(row.simulation_value)
        observedError = abs(row.measured_value - row.simulation_value);
    end

    offsetTyp = scalarField(profile, "input_offset_voltage_typ_V");
    offsetMax = scalarField(profile, "input_offset_voltage_max_full_temp_V");
    if ~isempty(observedError) && ~isempty(offsetTyp) && observedError >= 0.1 * offsetTyp && observedError <= 3 * offsetMax
        diagnostics = addDiagnostic(diagnostics, "lm741_input_offset_" + validId(row.quantity), "LM741 input offset voltage", ...
            "likely", "The voltage error is in the same order as an LM741 input offset voltage.", ...
            rowEvidence(row) + "; LM741 Vos typ=" + numberText(offsetTyp) + " V, max=" + numberText(offsetMax) + " V", ...
            "Add an LM741 input offset voltage source to the model or subtract measured zero-input offset from the lab data.");
    end

    sourceResistance = estimateInputSourceResistance(spec, row);
    biasTyp = scalarField(profile, "input_bias_current_typ_A");
    biasMax = scalarField(profile, "input_bias_current_max_full_temp_A");
    if ~isempty(sourceResistance) && ~isempty(biasTyp)
        expectedTyp = abs(biasTyp * sourceResistance);
        expectedMax = abs(biasMax * sourceResistance);
        severity = "possible";
        if ~isempty(observedError) && expectedTyp > 0 && observedError >= 0.25 * expectedTyp && observedError <= 4 * max(expectedMax, expectedTyp)
            severity = "likely";
        end
        diagnostics = addDiagnostic(diagnostics, "lm741_input_bias_" + validId(row.quantity), "LM741 input bias current through source resistance", ...
            severity, "LM741 input bias current flowing through the source/electrode resistance creates a DC voltage error: V_error = I_bias * R_source.", ...
            rowEvidence(row) + "; R_source=" + numberText(sourceResistance) + " ohm; expected typ=" + numberText(expectedTyp) + " V; expected max=" + numberText(expectedMax) + " V", ...
            "Add input-bias current sources at LM741 inputs and verify the source/electrode resistance used by the lab setup.");
    else
        diagnostics = addDiagnostic(diagnostics, "lm741_bias_source_resistance_missing_" + validId(row.quantity), "LM741 bias-current check needs source resistance", ...
            "check", "LM741 input bias current can be important, but CiTT could not estimate I_bias * R_source because the source/electrode resistance is missing.", ...
            rowEvidence(row), "Add R_source/R_c/electrode resistance to the spec or CSV so bias-current voltage error can be estimated.");
    end

    inputResistance = scalarField(profile, "input_resistance_typ_ohm");
    if ~isempty(sourceResistance) && ~isempty(inputResistance) && sourceResistance > 0.05 * inputResistance
        diagnostics = addDiagnostic(diagnostics, "lm741_input_loading_" + validId(row.quantity), "LM741 finite input resistance loading", ...
            "possible", "The source resistance is not negligible compared with LM741 input resistance, so the measurement node may be loaded.", ...
            "R_source=" + numberText(sourceResistance) + " ohm; LM741 Rin typ=" + numberText(inputResistance) + " ohm", ...
            "Model finite LM741 input resistance and compare against the ideal buffer assumption.");
    end
end
end

function diagnostics = addCrossRowReadoutDiagnostics(diagnostics, rows)
ratios = [];
errors = [];
for i = 1:numel(rows)
    row = rows(i);
    if isempty(row.measured_value) || isempty(row.simulation_value) || row.simulation_value == 0
        continue
    end
    if ~isVoltageOrCurrentLike(row)
        continue
    end
    ratios(end + 1) = row.measured_value / row.simulation_value; %#ok<AGROW>
    errors(end + 1) = row.measured_value - row.simulation_value; %#ok<AGROW>
end
if numel(ratios) < 2
    return
end

ratioMean = mean(ratios);
ratioSpread = std(ratios) / max(abs(ratioMean), eps);
if abs(ratioMean - 1) > 0.05 && ratioSpread < 0.08
    diagnostics = addDiagnostic(diagnostics, "common_input_gain_readout_scale", "Common input gain/readout scale error", ...
        "likely", "Multiple measured channels share nearly the same gain error relative to simulation.", ...
        "mean ratio=" + numberText(ratioMean) + ", relative spread=" + numberText(ratioSpread), ...
        "Check DAQ gain, scope probe factor, ADC full-scale conversion, amplifier gain setting, and CSV import scaling.");
end

errorMean = mean(errors);
errorSpread = std(errors) / max(abs(errorMean), eps);
if abs(errorMean) > 1e-6 && errorSpread < 0.15
    diagnostics = addDiagnostic(diagnostics, "common_input_offset_zeroing", "Common input offset/zeroing error", ...
        "possible", "Multiple channels share a similar absolute offset.", ...
        "mean offset=" + numberText(errorMean) + ", relative spread=" + numberText(errorSpread), ...
        "Check zero calibration, ADC offset, reference node, input bias/offset, and baseline subtraction.");
end
end

function diagnostics = addDiagnostic(diagnostics, id, label, severity, explanation, evidence, nextAction)
id = string(id);
for i = 1:numel(diagnostics)
    if diagnostics(i).id == id
        diagnostics(i).severity = strongerSeverity(diagnostics(i).severity, severity);
        return
    end
end
diagnostics(end + 1, 1) = diagnostic(id, label, severity, explanation, evidence, nextAction); %#ok<AGROW>
end

function item = diagnostic(id, label, severity, explanation, evidence, nextAction)
item = struct();
item.id = string(id);
item.label = string(label);
item.severity = string(severity);
item.explanation = string(explanation);
item.evidence = string(evidence);
item.next_action = string(nextAction);
end

function diagnostics = prioritizeDiagnostics(diagnostics)
if isempty(diagnostics)
    return
end
weights = zeros(numel(diagnostics), 1);
for i = 1:numel(diagnostics)
    weights(i) = severityWeight(diagnostics(i).severity);
end
[~, order] = sort(weights, "descend");
diagnostics = diagnostics(order);
end

function value = severityWeight(severity)
switch lower(string(severity))
    case "critical"
        value = 5;
    case "likely"
        value = 4;
    case "warning"
        value = 3;
    case "possible"
        value = 2;
    otherwise
        value = 1;
end
end

function severity = strongerSeverity(left, right)
if severityWeight(right) > severityWeight(left)
    severity = string(right);
else
    severity = string(left);
end
end

function suggestion = nextProbeSuggestion(rows, diagnostics)
suggestion = "Probe the quantity with the largest percent error, then verify units, reference node, sign convention, and settling time.";
if isempty(rows)
    return
end
bestIndex = 0;
bestPct = -Inf;
for i = 1:numel(rows)
    if ~isempty(rows(i).percent_difference) && abs(rows(i).percent_difference) > bestPct
        bestPct = abs(rows(i).percent_difference);
        bestIndex = i;
    end
end
if bestIndex > 0
    suggestion = "Start with " + rows(bestIndex).quantity + " (" + rows(bestIndex).status + ...
        "), then verify probe " + emptyText(rows(bestIndex).probe_id, "mapping") + ".";
elseif any([diagnostics.id] == "missing_reference")
    suggestion = "Add a simulation/reference column for each measured lab quantity before ranking errors.";
end
end

function actions = nextActions(diagnostics)
actions = strings(0, 1);
limit = min(numel(diagnostics), 5);
for i = 1:limit
    if strlength(diagnostics(i).next_action) > 0
        actions(end + 1) = diagnostics(i).next_action; %#ok<AGROW>
    end
end
actions = unique(actions, "stable");
end

function writeMarkdown(path, report)
lines = [
    "# CiTT Lab Error Report"
    ""
    "- CSV: " + report.csv_path
    "- JSON: " + report.report_path
    "- Spec: " + report.spec_path
    "- Probe map: " + report.probe_map_path
    ""
    "## Rows"
    ""
    "| Quantity | Unit | Measured | Reference | Difference | Status | Probe |"
    "| --- | --- | --- | --- | --- | --- | --- |"
];
for i = 1:numel(report.rows)
    row = report.rows(i);
    lines(end + 1) = "| " + md(row.quantity) + " | " + md(row.unit) + " | " + ...
        md(numberText(row.measured_value)) + " | " + md(referenceText(row)) + " | " + ...
        md(percentText(row.percent_difference)) + " | " + md(row.status) + " | " + ...
        md(emptyText(row.probe_id, "unmatched")) + " |"; %#ok<AGROW>
end

lines = [lines; ""; "## Nonideal Device Profiles"; ""];
if isempty(report.nonideal_profiles)
    lines(end + 1) = "- None detected.";
else
    for i = 1:numel(report.nonideal_profiles)
        profile = report.nonideal_profiles(i);
        lines(end + 1) = "- **" + profile.part_number + "**: " + profileSummary(profile) + ...
            ". Source: " + profile.source_url; %#ok<AGROW>
    end
end

lines = [lines; ""; "## Likely Causes"; ""];
if isempty(report.likely_causes)
    lines(end + 1) = "- No diagnostic causes were triggered.";
else
    for i = 1:numel(report.likely_causes)
        cause = report.likely_causes(i);
        lines(end + 1) = "- **" + cause.label + "** (" + cause.severity + "): " + ...
            cause.explanation + " Next: " + cause.next_action; %#ok<AGROW>
    end
end

lines = [lines; ""; "## Next Actions"; ""];
if isempty(report.prioritized_next_actions)
    lines(end + 1) = "- " + report.next_probe_suggestion;
else
    for i = 1:numel(report.prioritized_next_actions)
        lines(end + 1) = "- " + report.prioritized_next_actions(i); %#ok<AGROW>
    end
end

[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid >= 0
    cleanup = onCleanup(@() fclose(fid));
    fprintf(fid, "%s", char(strjoin(lines, newline)));
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

function value = readJsonIfPresent(path)
path = string(path);
if strlength(path) == 0 || exist(path, "file") ~= 2
    value = struct();
    return
end
try
    value = jsondecode(fileread(path));
catch
    value = struct();
end
end

function items = unwrapItems(value, wrapperField)
items = struct([]);
if ~isstruct(value) || isempty(value)
    return
end
if isfield(value, wrapperField)
    items = value.(wrapperField);
elseif isfield(value, "items")
    items = value.items;
else
    items = value;
end
end

function value = contextText(context, fieldName, defaultValue)
if isstruct(context) && isfield(context, fieldName) && ~isempty(context.(fieldName))
    value = string(context.(fieldName));
else
    value = string(defaultValue);
end
end

function value = optionText(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName) && ~isempty(options.(fieldName))
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function value = contextStruct(context, fieldName)
if isstruct(context) && isfield(context, fieldName)
    value = context.(fieldName);
else
    value = struct();
end
end

function names = normalizeName(names)
names = string(names);
names = regexprep(names, "[^A-Za-z0-9]+", "_");
names = regexprep(names, "^_+|_+$", "");
end

function index = firstIndex(lowerNames, candidates)
index = [];
candidates = lower(string(candidates));
for i = 1:numel(candidates)
    exact = find(lowerNames == candidates(i), 1);
    if ~isempty(exact)
        index = exact;
        return
    end
end
for i = 1:numel(candidates)
    partial = find(contains(lowerNames, candidates(i)), 1);
    if ~isempty(partial)
        index = partial;
        return
    end
end
end

function name = columnName(names, index)
if isempty(index)
    name = "";
else
    name = string(names(index));
end
end

function values = columnNumbers(tbl, index)
if isempty(index)
    values = [];
    return
end
try
    raw = tbl{:, index};
catch
    values = [];
    return
end
if iscell(raw)
    raw = string(raw);
end
if isstring(raw) || ischar(raw)
    values = str2double(string(raw));
elseif isnumeric(raw) || islogical(raw)
    values = double(raw);
elseif isduration(raw)
    values = seconds(raw);
else
    values = NaN(size(raw));
end
values = values(:);
end

function value = scalarFromValues(values)
values = values(:);
values = values(~isnan(values));
if isempty(values)
    value = [];
else
    value = values(end);
end
end

function value = numericScalar(value)
if isempty(value)
    value = [];
elseif isnumeric(value) && isscalar(value)
    value = double(value);
elseif isstring(value) || ischar(value)
    value = str2double(value);
    if isnan(value)
        value = [];
    end
else
    value = [];
end
end

function value = firstString(tbl, rowIndex, columnIndex)
if isempty(rowIndex) || isempty(columnIndex)
    value = "";
    return
end
raw = tbl{rowIndex, columnIndex};
if iscell(raw)
    raw = raw{1};
end
value = string(raw);
end

function idx = matchingReferenceColumn(names, measurementIndex, referenceTokens)
idx = [];
base = lower(stripMeasurementName(names(measurementIndex)));
lowerNames = lower(normalizeName(names));
referenceTokens = lower(string(referenceTokens));
scores = zeros(numel(names), 1);
for i = 1:numel(names)
    if i == measurementIndex
        continue
    end
    name = lowerNames(i);
    if ~any(contains(name, referenceTokens))
        continue
    end
    if contains(name, base) || contains(base, name)
        scores(i) = strlength(base) + 10;
    elseif any(contains(split(base, "_"), split(name, "_")))
        scores(i) = 1;
    end
end
[score, candidate] = max(scores);
if score > 0
    idx = candidate;
end
end

function name = stripMeasurementName(name)
name = string(name);
name = regexprep(name, "(?i)(^measured_|^lab_|_measured$|_lab$|_value$)", "");
name = regexprep(name, "[^A-Za-z0-9]+", "_");
name = regexprep(name, "^_+|_+$", "");
if strlength(name) == 0
    name = "measurement";
end
end

function text = fieldText(value, fieldName)
if isstruct(value) && isfield(value, fieldName)
    text = valueToText(value.(fieldName));
else
    text = "";
end
end

function text = valueToText(value)
if isempty(value)
    text = "";
elseif ischar(value)
    text = string(value);
elseif isstring(value)
    text = strjoin(string(value(:))', ", ");
elseif isnumeric(value) || islogical(value)
    text = string(mat2str(value));
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function tf = containsAny(text, patterns)
tf = any(contains(string(text), string(patterns), "IgnoreCase", true));
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

function tf = isVoltageLike(row)
text = lower(row.quantity + " " + row.unit + " " + row.probe_label + " " + row.probe_unit);
tf = containsAny(text, ["voltage", "volt", "vm", "v_m", "vout", "v_in"]) || lower(row.unit) == "v";
end

function tf = isVoltageOrCurrentLike(row)
text = lower(row.quantity + " " + row.unit + " " + row.probe_label + " " + row.probe_unit);
tf = isVoltageLike(row) || containsAny(text, ["current", "ampere", "icl", "i_cl"]) || any(lower(row.unit) == ["a", "ma", "ua", "na"]);
end

function tf = isResistanceLike(row)
text = lower(row.quantity + " " + row.unit + " " + row.probe_label + " " + row.probe_unit);
tf = containsAny(text, ["resistor", "resistance", "r_", " rc", "rm", "ro"]) || contains(lower(row.unit), "ohm");
end

function value = scalarField(item, fieldName)
if isstruct(item) && isfield(item, fieldName) && ~isempty(item.(fieldName))
    value = double(item.(fieldName));
else
    value = [];
end
end

function tf = specMentionsIdealOpAmp(spec)
text = lower(string(feval('citt.util.jsonEncode', spec)));
tf = containsAny(text, ["ideal op", "ideal-op", "infinite input impedance", "no current flows", "ideal buffer"]);
end

function text = profileSummary(profile)
text = string(profile.part_number) + ...
    ": Ib typ=" + numberText(scalarField(profile, "input_bias_current_typ_A")) + " A" + ...
    ", Vos typ=" + numberText(scalarField(profile, "input_offset_voltage_typ_V")) + " V" + ...
    ", Rin typ=" + numberText(scalarField(profile, "input_resistance_typ_ohm")) + " ohm";
end

function resistance = estimateInputSourceResistance(spec, row)
resistance = [];
if ~isstruct(spec) || ~isfield(spec, "components")
    return
end

components = spec.components;
bestScore = -Inf;
for i = 1:numel(components)
    if iscell(components)
        component = components{i};
    else
        component = components(i);
    end
    componentText = lower(string(feval('citt.util.jsonEncode', component)));
    if ~(contains(componentText, "resistor") || contains(componentText, "ohm"))
        continue
    end

    value = componentResistanceOhm(component);
    if isempty(value)
        continue
    end

    score = 0;
    if containsAny(componentText, ["r_c", "rc", "source", "electrode", "input"])
        score = score + 20;
    end
    rowText = lower(row.quantity + " " + row.probe_label);
    if contains(rowText, "vm") || contains(rowText, "v_m") || contains(rowText, "membrane") || contains(rowText, "buffer")
        if containsAny(componentText, ["r_c", "rc", "voltage electrode", "source", "input"])
            score = score + 20;
        end
    end
    if containsAny(componentText, ["r_o", "ro", "output", "load", "current electrode"])
        score = score - 10;
    end

    if score > bestScore
        bestScore = score;
        resistance = value;
    end
end
end

function resistance = componentResistanceOhm(component)
resistance = [];
if ~isstruct(component)
    return
end
unit = "";
if isfield(component, "unit")
    unit = lower(string(component.unit));
end
if strlength(unit) > 0 && ~(contains(unit, "ohm") || unit == "r" || unit == "omega")
    return
end

raw = "";
if isfield(component, "value")
    raw = component.value;
elseif isfield(component, "nominal_value")
    raw = component.nominal_value;
end
resistance = parseEngineeringNumber(raw);
end

function value = parseEngineeringNumber(raw)
value = [];
if isempty(raw)
    return
end
if isnumeric(raw) && isscalar(raw)
    value = double(raw);
    return
end
text = lower(strtrim(string(raw)));
if text == "" || text == "null" || text == "nan"
    return
end

tokens = regexp(char(text), "([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([fpnumkmegµu]*)", "tokens", "once");
if isempty(tokens)
    return
end
base = str2double(tokens{1});
if isnan(base)
    return
end
suffix = string(tokens{2});
suffix = replace(suffix, "µ", "u");
switch suffix
    case {"f"}
        factor = 1e-15;
    case {"p"}
        factor = 1e-12;
    case {"n"}
        factor = 1e-9;
    case {"u"}
        factor = 1e-6;
    case {"m"}
        factor = 1e-3;
    case {"k"}
        factor = 1e3;
    case {"meg"}
        factor = 1e6;
    case {"g"}
        factor = 1e9;
    otherwise
        factor = 1;
end
value = base * factor;
end

function tf = nearRatio(value, target)
if isempty(value) || value == 0
    tf = false;
else
    tf = abs(value - target) / target < 0.08 || abs((1 / value) - target) / target < 0.08;
end
end

function tf = nearAny(value, targets)
tf = false;
for i = 1:numel(targets)
    if nearRatio(value, targets(i))
        tf = true;
        return
    end
end
end

function id = validId(value)
id = string(matlab.lang.makeValidName(char(value)));
if strlength(id) == 0
    id = "quantity";
end
end

function text = rowEvidence(row)
text = row.quantity + ": measured=" + numberText(row.measured_value) + ...
    ", simulation=" + numberText(row.simulation_value) + ...
    ", hand=" + numberText(row.hand_value) + ...
    ", diff=" + percentText(row.percent_difference);
end

function text = rowList(rows, status)
matches = strings(0, 1);
for i = 1:numel(rows)
    if rows(i).status == status
        matches(end + 1) = rows(i).quantity; %#ok<AGROW>
    end
end
text = strjoin(matches, ", ");
end

function text = assumptionExcerpt(spec)
text = string(feval('citt.util.jsonEncode', spec));
if strlength(text) > 500
    text = extractBefore(text, 501) + "...";
end
end

function text = numberText(value)
if isempty(value)
    text = "";
else
    text = string(sprintf("%.6g", value));
end
end

function text = percentText(value)
if isempty(value)
    text = "not comparable";
else
    text = string(sprintf("%.3g%%", value));
end
end

function text = referenceText(row)
if ~isempty(row.simulation_value)
    text = "sim " + numberText(row.simulation_value);
elseif ~isempty(row.hand_value)
    text = "hand " + numberText(row.hand_value);
else
    text = "";
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
text = string(value);
text = replace(text, "|", "\|");
text = replace(text, newline, " ");
end
