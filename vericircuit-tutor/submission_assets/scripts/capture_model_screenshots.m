%CAPTURE_MODEL_SCREENSHOTS Generate or refresh model screenshot panels.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("model_screenshots");
