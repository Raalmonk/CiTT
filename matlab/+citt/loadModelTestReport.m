function report = loadModelTestReport(path)
%LOADMODELTESTREPORT Load or normalize the CiTT SATK model_test report.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(path)
    path = config.ModelTestReportPath;
end
path = string(path);

report = struct();
report.success = false;
report.status = "NOT_RUN";
report.report_path = path;
report.markdown_path = config.ModelTestMarkdownPath;
report.feature_path = config.ModelTestFeaturePath;
report.manifest_path = config.ModelTestManifestPath;
report.scenarios = struct([]);
report.summary = "Model tests have not been run.";
report.recommendations = strings(0, 1);

if exist(path, "file") ~= 2
    return
end

try
    loaded = jsondecode(fileread(path));
catch readError
    report.status = "FAIL";
    report.summary = "Model test report exists but could not be parsed: " + string(readError.message);
    return
end

if isstruct(loaded)
    report = mergeStruct(report, loaded);
end
if ~isfield(report, "status") || strlength(strtrim(string(report.status))) == 0
    if isfield(report, "success") && logicalValue(report.success)
        report.status = "PASS";
    else
        report.status = "FAIL";
    end
end
end

function out = mergeStruct(defaults, loaded)
out = defaults;
names = fieldnames(loaded);
for i = 1:numel(names)
    out.(names{i}) = loaded.(names{i});
end
end

function tf = logicalValue(value)
if islogical(value)
    tf = logical(value);
elseif isnumeric(value)
    tf = value ~= 0;
elseif isstring(value) || ischar(value)
    tf = any(lower(string(value)) == ["true", "1", "yes", "pass"]);
else
    tf = false;
end
end
