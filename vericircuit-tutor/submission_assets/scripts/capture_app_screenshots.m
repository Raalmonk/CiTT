%CAPTURE_APP_SCREENSHOTS Generate or refresh CiTT app evidence panels.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("app_screenshots");
