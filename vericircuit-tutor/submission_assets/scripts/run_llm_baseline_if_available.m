%RUN_LLM_BASELINE_IF_AVAILABLE Regenerate LLM-only baseline prompts/outputs.

thisFile = mfilename("fullpath");
scriptDir = fileparts(thisFile);
addpath(scriptDir);
citt_submission_generate("baseline");
