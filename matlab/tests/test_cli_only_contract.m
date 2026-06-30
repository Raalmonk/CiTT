function test_cli_only_contract()
%TEST_CLI_ONLY_CONTRACT Verify removed provider and local-builder routes stay removed.

repoMatlabRoot = fileparts(fileparts(mfilename("fullpath")));
addpath(repoMatlabRoot);

assert(strlength(string(which("citt.parseCircuitWithCli"))) > 0);
removedProvider = "ge" + "mini";
assert(strlength(string(which("citt.parseCircuitWith" + upperFirst(removedProvider)))) == 0);
assert(strlength(string(which("citt.buildLocal" + "Simscape" + "Fall" + "back"))) == 0);
assert(strlength(string(which("citt.build" + "Simscape" + "ModelFromSpec"))) == 0);

config = feval('citt.loadConfig');
removedTitle = upperFirst(removedProvider);
assert(~isfield(config, removedTitle + "ApiKey"));
assert(~isfield(config, removedTitle + "Model"));
assert(~isfield(config, removedTitle + "CliPath"));
assert(~isfield(config, "ParserBackend"));

promptRoot = fullfile(repoMatlabRoot, "resources", "prompts");
assert(isfile(fullfile(promptRoot, "cli_circuit_parse_system.txt")));
assert(~isfile(fullfile(promptRoot, removedProvider + "_circuit_parse_system.txt")));

report = feval('citt.checkSetup');
cliNames = string({report.agent_clis.name});
assert(~any(cliNames == removedProvider));
assert(all(ismember(cliNames, ["codex", "claude", "deepseek"])));
end

function value = upperFirst(value)
value = string(value);
value = upper(extractBefore(value, 2)) + extractAfter(value, 1);
end
