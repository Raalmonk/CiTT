function test_real_config()
%TEST_REAL_CONFIG Verify real-run defaults and setup report fields.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
assert(config.GeminiModel == "gemini-3.1-pro-preview");

report = feval('citt.checkSetup');
assert(isfield(report, "gemini_key_found"));
assert(isfield(report, "satk_initialize_available"));
assert(isfield(report, "matlab_mcp_available"));
assert(isfield(report, "agent_clis"));
end
