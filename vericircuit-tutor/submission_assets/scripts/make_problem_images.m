%MAKE_PROBLEM_IMAGES Regenerate input schematic images for all benchmarks.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("images");
