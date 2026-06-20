function report = compareLabDelta(handValues, simulationValues, labCsvPath, options)
%COMPARELABDELTA Compare hand, simulation, and lab CSV values.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(handValues)
    handValues = struct();
end
if nargin < 2 || isempty(simulationValues)
    simulationValues = struct();
end
if nargin < 3 || isempty(labCsvPath)
    error("CiTT:LabCsvRequired", "Lab Delta real-run mode requires a lab CSV path.");
end
if nargin < 4 || isempty(options)
    options = struct();
end

outputPath = config.LabDeltaReportPath;
if isfield(options, "OutputPath")
    outputPath = string(options.OutputPath);
end

if isstruct(handValues) && isfield(handValues, "hand_values")
    request = handValues;
    handValues = getOrDefault(request, "hand_values", struct());
    simulationValues = getOrDefault(request, "simulation_values", struct());
    labCsvPath = getOrDefault(request, "lab_csv_path", labCsvPath);
end

handMap = structToScalarMap(handValues);
simMap = structToScalarMap(simulationValues);
labRows = readLabRows(labCsvPath);
if isempty(labRows)
    error("CiTT:LabCsvEmpty", "Lab CSV did not contain comparable rows: %s", string(labCsvPath));
end

rows = struct([]);
for i = 1:numel(labRows)
    quantity = labRows(i).quantity;
    handValue = chooseValue(handMap, quantity, labRows(i).hand_value);
    simValue = chooseValue(simMap, quantity, labRows(i).simulation_value);
    measuredValue = labRows(i).measured_value;
    row = comparisonRow(quantity, handValue, simValue, measuredValue, labRows(i).unit);
    rows = [rows; row]; %#ok<AGROW>
end

report = struct();
report.success = true;
report.csv_path = string(labCsvPath);
report.rows = rows;
report.likely_causes = likelyCauses(rows);
report.next_probe_suggestion = "Probe the quantity with the largest percent difference, then verify units, reference node, and settling time.";
report.report_path = string(outputPath);

writeJson(outputPath, report);
end

function rows = readLabRows(labCsvPath)
rows = struct([]);
labCsvPath = string(labCsvPath);
if strlength(labCsvPath) == 0
    return
end
if exist(labCsvPath, "file") ~= 2
    error("CiTT:LabCsvMissing", "Lab CSV file not found: %s", labCsvPath);
end

tbl = readtable(labCsvPath, "TextType", "string");
names = string(tbl.Properties.VariableNames);
lowerNames = lower(names);
quantityIndex = find(lowerNames == "quantity" | lowerNames == "name" | lowerNames == "signal", 1);
unitIndex = find(lowerNames == "unit" | lowerNames == "units", 1);
measuredIndex = find(lowerNames == "measured" | lowerNames == "lab" | lowerNames == "value", 1);
handIndex = find(lowerNames == "hand" | lowerNames == "hand_value", 1);
simIndex = find(lowerNames == "simulation" | lowerNames == "sim" | lowerNames == "simulation_value", 1);

if ~isempty(quantityIndex)
    for r = 1:height(tbl)
        row = baseLabRow();
        row.quantity = string(tbl{r, quantityIndex});
        row.unit = tableString(tbl, r, unitIndex);
        row.measured_value = tableNumber(tbl, r, measuredIndex);
        row.hand_value = tableNumber(tbl, r, handIndex);
        row.simulation_value = tableNumber(tbl, r, simIndex);
        rows = [rows; row]; %#ok<AGROW>
    end
    return
end

numericNames = names(varfun(@isnumeric, tbl, "OutputFormat", "uniform"));
for i = 1:numel(numericNames)
    values = tbl.(numericNames(i));
    if isempty(values)
        continue
    end
    row = baseLabRow();
    row.quantity = numericNames(i);
    row.measured_value = values(end);
    rows = [rows; row]; %#ok<AGROW>
end
end

function row = baseLabRow()
row = struct();
row.quantity = "";
row.hand_value = [];
row.simulation_value = [];
row.measured_value = [];
row.unit = "";
end

function row = comparisonRow(quantity, handValue, simValue, measuredValue, unit)
row = struct();
row.quantity = string(quantity);
row.hand_value = numericOrEmpty(handValue);
row.simulation_value = numericOrEmpty(simValue);
row.measured_value = numericOrEmpty(measuredValue);
row.unit = string(unit);
reference = row.simulation_value;
if isempty(row.hand_value) || isempty(row.simulation_value) || isempty(row.measured_value) || reference == 0
    error("CiTT:LabDeltaIncomplete", ...
        "Quantity %s requires hand, simulation, and measured values with nonzero simulation reference.", string(quantity));
else
    row.absolute_difference = row.measured_value - reference;
    row.percent_difference = 100 * (row.measured_value - reference) / reference;
end
end

function causes = likelyCauses(rows)
catalog = [
    cause("two_pi_error", "2*pi error", "Check rad/s versus Hz and cutoff-frequency formulas.", "check")
    cause("unit_prefix_error", "unit prefix error", "Check k, m, u, n, and p prefixes in component or instrument values.", "check")
    cause("sampling_nyquist", "sampling/Nyquist", "Check sample rate, Nyquist frequency, and aliasing near the requested output.", "check")
    cause("component_tolerance", "component tolerance", "Compare actual resistor/capacitor values against nominal values.", "check")
    cause("source_load_impedance", "source/load impedance", "Check whether source resistance or measurement loading changes the modeled circuit.", "check")
    cause("transient_not_settled", "transient not settled", "Check simulation/lab capture after the settling interval.", "check")
    cause("measurement_noise", "measurement noise", "Check noise floor, probe grounding, and averaging.", "check")
];

causes = catalog;
for r = 1:numel(rows)
    row = rows(r);
    if isempty(row.measured_value)
        continue
    end
    ref = row.simulation_value;
    if isempty(ref)
        ref = row.hand_value;
    end
    if isempty(ref) || ref == 0
        continue
    end
    ratio = abs(row.measured_value / ref);
    if nearRatio(ratio, 2*pi)
        causes(1).severity = "likely";
    end
    if nearRatio(ratio, 1e3) || nearRatio(ratio, 1e-3) || nearRatio(ratio, 1e6) || nearRatio(ratio, 1e-6)
        causes(2).severity = "likely";
    end
    if ~isempty(row.percent_difference) && abs(row.percent_difference) > 20
        causes(4).severity = "possible";
        causes(5).severity = "possible";
    end
end
end

function c = cause(id, label, explanation, severity)
c = struct();
c.id = string(id);
c.label = string(label);
c.explanation = string(explanation);
c.severity = string(severity);
end

function tf = nearRatio(value, target)
tf = abs(value - target) / target < 0.08 || abs(1 / value - target) / target < 0.08;
end

function map = structToScalarMap(value)
map = struct();
if ~isstruct(value)
    return
end
names = fieldnames(value);
for i = 1:numel(names)
    raw = value.(names{i});
    if isnumeric(raw) && isscalar(raw)
        map.(names{i}) = raw;
    end
end
end

function value = chooseValue(map, quantity, defaultValue)
quantity = matlab.lang.makeValidName(char(quantity));
if isstruct(map) && isfield(map, quantity)
    value = map.(quantity);
else
    value = defaultValue;
end
end

function value = getOrDefault(container, fieldName, defaultValue)
if isstruct(container) && isfield(container, fieldName)
    value = container.(fieldName);
else
    value = defaultValue;
end
end

function value = numericOrEmpty(value)
if isempty(value)
    value = [];
elseif isnumeric(value)
    value = double(value);
elseif isstring(value) || ischar(value)
    candidate = str2double(value);
    if isnan(candidate)
        value = [];
    else
        value = candidate;
    end
else
    value = [];
end
end

function value = tableNumber(tbl, rowIndex, columnIndex)
if isempty(columnIndex)
    value = [];
    return
end
raw = tbl{rowIndex, columnIndex};
if iscell(raw)
    raw = raw{1};
end
value = numericOrEmpty(raw);
end

function value = tableString(tbl, rowIndex, columnIndex)
if isempty(columnIndex)
    value = "";
    return
end
raw = tbl{rowIndex, columnIndex};
if iscell(raw)
    raw = raw{1};
end
value = string(raw);
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
