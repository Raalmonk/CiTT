function citt_submission_generate(mode)
%CITT_SUBMISSION_GENERATE Generate CiTT BMES submission evidence assets.
%
% This wrapper delegates to the offline Python generator when live SATK model
% generation is not available. The generated reports clearly label offline and
% illustrative evidence so live Simscape screenshots can replace them later.

if nargin < 1 || strlength(string(mode)) == 0
    mode = "all";
end

scriptDir = fileparts(mfilename("fullpath"));
generator = fullfile(scriptDir, "generate_offline_assets.py");
if exist(generator, "file") ~= 2
    error("CiTTSubmission:MissingGenerator", "Missing generator: %s", generator);
end

pythonCmd = "python3";
if ispc
    pythonCmd = "python";
end

cmd = pythonCmd + " " + shellQuote(generator) + " --mode " + shellQuote(string(mode));
[status, output] = system(cmd);
disp(output);
if status ~= 0
    error("CiTTSubmission:GeneratorFailed", "Evidence generator failed with status %d.", status);
end
end

function quoted = shellQuote(value)
raw = char(string(value));
if ispc
    quoted = """" + string(strrep(raw, """", "\""")) + """";
else
    raw = strrep(raw, "'", "'\''");
    quoted = "'" + string(raw) + "'";
end
end
