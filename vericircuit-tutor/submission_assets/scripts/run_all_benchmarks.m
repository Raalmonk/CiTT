%RUN_ALL_BENCHMARKS Generate the CiTT BMES/Medtronic evidence package.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("all");
