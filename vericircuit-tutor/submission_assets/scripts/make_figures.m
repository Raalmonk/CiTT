%MAKE_FIGURES Regenerate benchmark plots and top-level comparison figures.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("figures");
