function result = classifyBuildReadiness(spec)
%CLASSIFYBUILDREADINESS Separate true build blockers from modeling notes.

issues = strings(0, 1);
notes = strings(0, 1);
blockingRegions = strings(0, 1);
nonblockingRegions = strings(0, 1);

if isstruct(spec) && isfield(spec, "unsupported_or_unclear_regions")
    regions = valueToStrings(spec.unsupported_or_unclear_regions);
    for i = 1:numel(regions)
        region = strtrim(regions(i));
        if strlength(region) == 0
            continue
        end
        if isNonBlockingBiophysicalSimplification(region, spec)
            nonblockingRegions(end + 1) = region; %#ok<AGROW>
            notes(end + 1) = "Non-blocking modeling simplification: " + region; %#ok<AGROW>
        else
            blockingRegions(end + 1) = region; %#ok<AGROW>
            issues(end + 1) = "Unclear region: " + region; %#ok<AGROW>
        end
    end
end

result = struct();
result.blocking_regions = blockingRegions;
result.nonblocking_regions = nonblockingRegions;
result.blocking_issues = issues;
result.nonblocking_notes = notes;
result.blocking_text = strjoin(issues, newline);
result.nonblocking_text = strjoin(notes, newline);
result.build_ready = isempty(issues);
end

function tf = isNonBlockingBiophysicalSimplification(issue, spec)
text = lower(string(issue));
context = lower(strjoin([
    fieldText(spec, "circuit_type")
    fieldText(spec, "likely_analysis")
    valueText(fieldValue(spec, "assumptions"))
    valueText(fieldValue(spec, "ambiguities"))
], " "));

mentionsBiology = any(contains(text, [
    "axon"
    "biological"
    "biophysical"
    "ion channel"
    "ion channels"
    "membrane capacitance"
    "membrane capacitor"
    "capacitive effects"
]));

mentionsSimplification = any(contains(text, [
    "simplified"
    "simplification"
    "not depicted"
    "not shown"
    "ignored"
    "omitted"
]));

isEquilibriumPassive = any(contains(context, [
    "tevc"
    "voltage clamp"
    "equilibrium"
    "steady-state"
    "steady state"
    "dc"
    "passive"
    "fully charged"
    "ignored"
]));

tf = mentionsBiology && mentionsSimplification && isEquilibriumPassive;
end

function value = fieldValue(data, fieldName)
if isstruct(data) && isfield(data, fieldName)
    value = data.(fieldName);
else
    value = "";
end
end

function text = fieldText(data, fieldName)
text = valueText(fieldValue(data, fieldName));
end

function text = valueText(value)
items = valueToStrings(value);
if isempty(items)
    text = "";
else
    text = strjoin(items(:)', " ");
end
end

function values = valueToStrings(value)
if isempty(value)
    values = strings(0, 1);
elseif isstring(value)
    values = value(:);
elseif ischar(value)
    values = string(value);
elseif iscell(value)
    values = strings(0, 1);
    for i = 1:numel(value)
        values = [values; valueToStrings(value{i})]; %#ok<AGROW>
    end
elseif isstruct(value)
    values = strings(numel(value), 1);
    for i = 1:numel(value)
        values(i) = string(feval('citt.util.jsonEncode', value(i)));
    end
else
    values = string(value(:));
end
end
