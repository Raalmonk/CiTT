function result = buildSimscapeModelFromSpec(specInput, options)
%BUILDSIMSCAPEMODELFROMSPEC Legacy alias for the explicit local fallback.

if nargin < 1
    specInput = [];
end
if nargin < 2
    options = struct();
end

result = feval('citt.buildLocalSimscapeFallback', specInput, options);
end
