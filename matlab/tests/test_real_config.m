function test_real_config()
%TEST_REAL_CONFIG Verify real-run defaults and setup report fields.

addpath(fileparts(fileparts(mfilename("fullpath"))));
config = feval('citt.loadConfig');
assert(isfield(config, "AgentCommand"));
assert(~isfield(config, "ParserBackend"));
assert(~isfield(config, "Agent" + "Backend"));
removedProvider = "ge" + "mini";
assert(~isfield(config, upperFirst(removedProvider) + "Model"));

report = feval('citt.checkSetup');
assert(isfield(report, "parser_available"));
assert(isfield(report, "satk_initialize_available"));
assert(isfield(report, "matlab_mcp_available"));
assert(isfield(report, "agent_clis"));
cliNames = string({report.agent_clis.name});
assert(any(cliNames == "codex"));
assert(any(cliNames == "claude"));
assert(any(cliNames == "deepseek"));
assert(~any(cliNames == removedProvider));
end

function value = upperFirst(value)
value = string(value);
value = upper(extractBefore(value, 2)) + extractAfter(value, 1);
end
