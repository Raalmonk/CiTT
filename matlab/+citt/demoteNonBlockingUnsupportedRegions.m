function spec = demoteNonBlockingUnsupportedRegions(spec)
%DEMOTENONBLOCKINGUNSUPPORTEDREGIONS Move accepted simplifications to assumptions.

if ~isstruct(spec)
    return
end

readiness = feval('citt.classifyBuildReadiness', spec);
if isempty(readiness.nonblocking_regions)
    return
end

spec.unsupported_or_unclear_regions = cellstr(readiness.blocking_regions(:)');
assumptions = valueToCell(specField(spec, "assumptions"));
for i = 1:numel(readiness.nonblocking_regions)
    assumptions{end + 1} = char("Accepted modeling simplification: " + readiness.nonblocking_regions(i)); %#ok<AGROW>
end
spec.assumptions = assumptions;
end

function value = specField(spec, fieldName)
if isfield(spec, fieldName)
    value = spec.(fieldName);
else
    value = {};
end
end

function values = valueToCell(value)
if isempty(value)
    values = {};
elseif iscell(value)
    values = value(:)';
elseif isstring(value)
    values = cellstr(value(:)');
elseif ischar(value)
    values = {value};
else
    values = num2cell(value(:)');
end
end
