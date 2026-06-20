function report = checkSetup()
%CHECKSETUP Inspect local MATLAB, Gemini, SATK, Simulink, and agent setup.

config = feval('citt.loadConfig');
toolboxes = feval('citt.util.findAvailableToolboxes');

report = struct();
report.checked_at = string(datetime("now"));
report.matlab_version = string(version);
report.matlab_root = string(matlabroot);
report.work_dir = config.WorkDir;
report.gemini_key_found = strlength(config.GeminiApiKey) > 0;
report.gemini_key_name = config.GeminiApiKeyName;
report.gemini_model = config.GeminiModel;
report.simulink_available = logical(toolboxes.simulink);
report.simulink_license = logical(toolboxes.simulink_license);
report.simscape_available = logical(toolboxes.simscape);
report.simscape_license = logical(toolboxes.simscape_license);
report.simscape_electrical_available = logical(toolboxes.simscape_electrical);
report.simscape_electrical_license = logical(toolboxes.simscape_electrical_license);
report.matlab_mcp_available = mcpAvailable(config);
report.satk_initialize_available = satkInitializeAvailable(config);
report.setup_agentic_toolkit_available = exist("setupAgenticToolkit", "file") == 2;
report.satk_path_hint = findSatkPathHint();
report.satk_install_path = config.SatkInstallPath;
report.matlab_agentic_toolkit_path = config.MatlabAgenticToolkitPath;
report.matlab_mcp_server_path = config.MatlabMcpServerPath;
report.agent_clis = findAgentClis();
report.configured_agent_command = config.AgentCommand;
report.guidance = setupGuidance(report);
report.summary_text = setupSummary(report);
end

function pathHint = findSatkPathHint()
pathHint = "";
try
    satkPath = which("satk_initialize");
    if strlength(string(satkPath)) > 0
        pathHint = string(satkPath);
    end
catch
    pathHint = "";
end
end

function available = satkInitializeAvailable(config)
available = exist("satk_initialize", "file") == 2 || exist("satk_initialize", "file") == 6;
if ~available && strlength(config.SatkInstallPath) > 0
    available = exist(fullfile(config.SatkInstallPath, "satk_initialize.m"), "file") == 2 || ...
        exist(fullfile(config.SatkInstallPath, "satk_initialize.p"), "file") == 6 || ...
        exist(fullfile(config.SatkInstallPath, "satk_initialize.p"), "file") == 2;
end
end

function available = mcpAvailable(config)
available = exist("shareMATLABSession", "file") == 2 || exist("shareMATLABSession", "file") == 6 || ...
    exist("matlab_mcp_server", "file") == 2 || exist("matlabMCPServer", "file") == 2 || ...
    exist("startMatlabMcpServer", "file") == 2;
if ~available && strlength(config.MatlabMcpServerPath) > 0
    available = exist(config.MatlabMcpServerPath, "file") == 2;
end
end

function clis = findAgentClis()
names = ["gemini", "codex"];
clis = struct([]);
for i = 1:numel(names)
    cli = struct();
    cli.name = names(i);
    cli.available = commandAvailable(names(i));
    cli.path = "";
    if cli.available
        cli.path = commandPath(names(i));
    end
    clis = [clis; cli]; %#ok<AGROW>
end
end

function available = commandAvailable(name)
available = strlength(commandPath(name)) > 0;
end

function pathText = commandPath(name)
if ispc
    cmd = "where " + name;
else
    cmd = "/bin/zsh -lc " + shellQuote("command -v " + name);
end
result = feval('citt.util.safeSystem', cmd);
if result.status == 0
    lines = splitlines(strtrim(result.stdout));
    pathText = string(lines(1));
else
    pathText = "";
end
end

function quoted = shellQuote(value)
raw = char(string(value));
raw = strrep(raw, '\', '\\');
raw = strrep(raw, '"', '\"');
raw = strrep(raw, '$', '\$');
raw = strrep(raw, '`', '\`');
quoted = string(['"', raw, '"']);
end

function lines = setupGuidance(report)
lines = strings(0, 1);
if ~report.gemini_key_found
    lines(end + 1) = "Set GEMINI_API_KEY before parsing circuit images or prompts.";
end
if ~report.simulink_available
    lines(end + 1) = "Install Simulink and make sure the license is available.";
end
if ~report.simscape_available
    lines(end + 1) = "Install Simscape for physical circuit modeling. CiTT real-run mode requires Simscape.";
end
if ~report.simscape_electrical_available
    lines(end + 1) = "Install Simscape Electrical for component-level electrical blocks when possible.";
end
if ~report.satk_initialize_available
    lines(end + 1) = "Install or initialize Simulink Agentic Toolkit. If installed, run addpath(""~/.matlab/agentic-toolkits/simulink"") and satk_initialize.";
end
if ~report.matlab_mcp_available
    lines(end + 1) = "If your SATK workflow uses MATLAB MCP Server, add it to the MATLAB path and start it before running the external agent.";
end
hasCli = false;
for i = 1:numel(report.agent_clis)
    hasCli = hasCli || report.agent_clis(i).available;
end
if ~hasCli && strlength(report.configured_agent_command) == 0
    lines(end + 1) = "Configure Gemini CLI, Codex CLI, or CITT_AGENT_COMMAND for automatic SATK agent execution.";
end
if isempty(lines)
    lines = "Setup looks ready for the MATLAB-native SATK agent flow.";
end
end

function text = setupSummary(report)
cliLines = strings(0, 1);
for i = 1:numel(report.agent_clis)
    status = "missing";
    if report.agent_clis(i).available
        status = "found";
    end
    cliLines(end + 1) = report.agent_clis(i).name + ": " + status + " " + report.agent_clis(i).path; %#ok<AGROW>
end

lines = [
    "MATLAB: " + report.matlab_version
    "Gemini key: " + foundMissing(report.gemini_key_found) + " (" + report.gemini_key_name + ")"
    "Gemini model: " + report.gemini_model
    "Simulink: " + foundMissing(report.simulink_available) + ", license " + foundMissing(report.simulink_license)
    "Simscape: " + foundMissing(report.simscape_available) + ", license " + foundMissing(report.simscape_license)
    "Simscape Electrical: " + foundMissing(report.simscape_electrical_available)
    "MATLAB MCP Server hint: " + foundMissing(report.matlab_mcp_available)
    "satk_initialize: " + foundMissing(report.satk_initialize_available)
    "setupAgenticToolkit: " + foundMissing(report.setup_agentic_toolkit_available)
    "SATK path hint: " + report.satk_path_hint
    "SATK install path: " + report.satk_install_path
    "MATLAB Agentic Toolkit path: " + report.matlab_agentic_toolkit_path
    "MCP server binary: " + report.matlab_mcp_server_path
    "Configured CITT_AGENT_COMMAND: " + report.configured_agent_command
    "Agent CLIs:"
    cliLines(:)
    "Setup guidance:"
    report.guidance(:)
    "Work dir: " + report.work_dir
];
text = strjoin(lines, newline);
end

function text = foundMissing(value)
if value
    text = "found";
else
    text = "missing";
end
end
