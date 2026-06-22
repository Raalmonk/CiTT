function report = compareLabDelta(handValues, simulationValues, labCsvPath, options)
%COMPARELABDELTA Back-compatible entry point for lab error analysis.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(handValues)
    handValues = struct();
end
if nargin < 2 || isempty(simulationValues)
    simulationValues = struct();
end
if nargin < 3 || isempty(labCsvPath)
    labCsvPath = "";
end
if nargin < 4 || isempty(options)
    options = struct();
end

if isstruct(handValues) && isfield(handValues, "hand_values")
    request = handValues;
    handValues = getOrDefault(request, "hand_values", struct());
    simulationValues = getOrDefault(request, "simulation_values", struct());
    labCsvPath = getOrDefault(request, "lab_csv_path", labCsvPath);
end

context = struct();
context.HandValues = handValues;
context.SimulationValues = simulationValues;
context.SpecPath = config.LastSpecPath;
context.ProbeMapPath = config.ProbeMapPath;

if isfield(options, "Context") && isstruct(options.Context)
    context = mergeStructs(context, options.Context);
end

report = feval('citt.analyzeLabError', labCsvPath, context, options);
end

function value = getOrDefault(container, fieldName, defaultValue)
if isstruct(container) && isfield(container, fieldName)
    value = container.(fieldName);
else
    value = defaultValue;
end
end

function merged = mergeStructs(base, extra)
merged = base;
names = fieldnames(extra);
for i = 1:numel(names)
    merged.(names{i}) = extra.(names{i});
end
end
