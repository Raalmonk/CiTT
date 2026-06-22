%MAKE_REPORT Regenerate markdown reports and scorecards.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("report");
