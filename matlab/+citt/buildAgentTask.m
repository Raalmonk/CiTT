function result = buildAgentTask(specInput, options)
%BUILDAGENTTASK Write the Simulink Agentic Toolkit build task markdown.

if nargin < 1 || isempty(specInput)
    config = feval('citt.loadConfig');
    specInput = config.LastSpecPath;
else
    config = feval('citt.loadConfig');
end
if nargin < 2 || isempty(options)
    options = struct();
end

taskPath = config.AgentTaskPath;
if isfield(options, "TaskPath")
    taskPath = string(options.TaskPath);
end

[spec, specSource] = readSpec(specInput);
rejectBlockingSpec(spec);
presetResult = [];
presetError = [];
try
    presetResult = feval('citt.ensureSatkProjectPreset', struct("AllowMissingApi", true));
    if isfield(presetResult, "success") && ~presetResult.success
        presetError = string(strjoin(presetResult.messages, newline));
    end
catch caughtPresetError
    presetError = string(caughtPresetError.message);
end
promptPath = fullfile(config.MatlabRoot, "resources", "prompts", "agent_build_simscape_model.txt");
basePrompt = string(fileread(promptPath));
satkInstructionsSection = repoLocalSatkInstructionsSection(config);
satkPolicySection = satkProjectPolicySection(config, presetResult, presetError);
simscapeContractSection = simscapeUtilizationContractSection();
testInterfaceSection = signalLevelTestInterfaceSection();
stateflowSection = stateflowTeachingLogicContractSection();
specJson = string(feval('citt.util.jsonEncode', spec));
nonidealProfiles = feval('citt.opAmpNonidealProfile', spec);
nonidealSection = nonidealProfileSection(nonidealProfiles);

taskText = strjoin([
    "# CiTT Simscape Model Build Task"
    ""
    "You are operating inside MATLAB/Simulink with Simulink Agentic Toolkit."
    "This task is self-contained. Do not read external agent skill files, do not invoke subagents, and do not use shell tools."
    "Use the available MATLAB MCP tools to inspect, build, edit, and check the model."
    "When running in an external agent CLI, use the actual registered tool names: mcp_matlab_model_overview, mcp_matlab_model_read, mcp_matlab_model_edit, mcp_matlab_model_check, mcp_matlab_model_query_params, and mcp_matlab_model_resolve_params."
    "Use mcp_matlab_evaluate_matlab_code only for required artifact file writes or MATLAB checks that have no dedicated MCP tool; do not use it to bypass mcp_matlab_model_edit for structural model construction."
    "If your runtime exposes unprefixed aliases, the equivalent aliases are model_overview, model_read, model_edit, model_check, model_query_params, and model_resolve_params."
    "The structured circuit spec is embedded below; do not read the Source file path."
    ""
    "## External Agent Guardrails"
    "- Do not call read_file for /Users/Raalm/.agents/skills or other external skill paths."
    "- Do not call run_shell_command; it is not available in this CiTT agent runner."
    "- Do not call invoke_agent or delegate to another agent."
    "- If the target model does not exist yet, create it with mcp_matlab_model_edit; do not treat an initial model_overview/model_read failure as permission to bypass SATK."
    "- Do not call local CiTT model-construction helpers or generate a model through raw MATLAB scripts."
    "- Do not write or run citt_build_simscape_model.m as the model-generation mechanism."
    "- If mcp_matlab_model_edit cannot create/edit the model, write an agent report explaining the SATK/MCP failure instead of producing model artifacts."
    ""
    satkInstructionsSection
    ""
    satkPolicySection
    ""
    simscapeContractSection
    ""
    testInterfaceSection
    ""
    stateflowSection
    ""
    "## Product Boundary"
    "The selected CLI parsed the circuit image/prompt into a structured model specification. Treat that spec as a starting point, not as numerical authority."
    "Your job is to build/check the Simulink/Simscape model. Do not write educational prose yet; CiTT will teach after the model exists."
    ""
    "## Simscape-First Requirements"
    "- Build a Simscape-first model from the structured circuit spec."
    "- Use Simscape and Simscape Electrical physical components when available."
    "- Use physical electrical connections and component schematics."
    "- Include Electrical Reference and Solver Configuration blocks as needed."
    "- Add voltage/current sensors or logging for requested outputs."
    "- Route physical measurements through sensors and PS-Simulink Converter blocks before logging or ADC/math blocks."
    "- If model_test may be used, add a signal-level subsystem named CiTT_TestInterface with Simulink Inport/Outport blocks around the physical network."
    "- Use model_query_params and model_resolve_params for symbolic or workspace parameters before making numeric claims."
    "- If a source/component value is symbolic or omitted, keep it as a named model parameter instead of inventing a number."
    "- Values outside the requested/connected teaching path should not block structural model generation."
    "- Do not use a Simulink signal-flow substitute for the circuit."
    "- Do not solve with standalone MATLAB numeric code as the model-generation output."
    "- Do not bypass SATK/model_edit by calling local deterministic builder functions."
    "- Treat the supplied spec as build-ready; report an error if a required modeling detail is still missing."
    ""
    "## Required Output Files"
    "- Save the model as `" + config.GeneratedModelPath + "`."
    "- Write focus map JSON to `" + config.FocusMapPath + "`."
    "- Write probe map JSON to `" + config.ProbeMapPath + "`."
    "- Run model_check or equivalent checks and save notes to `" + config.AgentReportPath + "`."
    ""
    "## Focus Map Contract"
    "Each focus map item must include: focus_id, label, explanation, model_paths, block_paths, line_handles_or_descriptions, related_components, related_nodes, teaching_question."
    "Keep focus-map text LaTeX-safe. Prefer plain text; if math is needed, use only short balanced inline `$...$` expressions."
    ""
    "## Probe Map Contract"
    "Each probe map item must include: probe_id, focus_id, label, target_type, model_paths, block_paths, quantity, unit, suggested_sensor_or_logging, instructions."
    "Probe instructions must include the physical sensor/logging path and unit. Prefer plain text over LaTeX."
    ""
    nonidealSection
    ""
    "## Additional CiTT Prompt"
    string(basePrompt)
    ""
    "## Structured Circuit Spec"
    "Source: " + specSource
    "```json"
    specJson
    "```"
], newline);

writeText(taskPath, taskText);

result = struct();
result.success = true;
result.task_path = string(taskPath);
result.spec_source = specSource;
result.produced_model_path = config.GeneratedModelPath;
result.produced_focus_map_path = config.FocusMapPath;
result.produced_probe_map_path = config.ProbeMapPath;
result.produced_report_path = config.AgentReportPath;
result.summary = "Wrote Simscape-first agent task for Simulink Agentic Toolkit.";
end

function [spec, source] = readSpec(specInput)
if isstruct(specInput)
    spec = specInput;
    source = "MATLAB struct";
    return
end

path = string(specInput);
if strlength(path) == 0 || exist(path, "file") ~= 2
    error("CiTT:SpecMissing", "Circuit spec JSON was not found: %s", path);
end
spec = jsondecode(fileread(path));
spec = feval('citt.demoteNonBlockingUnsupportedRegions', spec);
source = path;
end

function rejectBlockingSpec(spec)
readiness = feval('citt.classifyBuildReadiness', spec);
problems = readiness.blocking_issues;
if ~isempty(problems)
    error("CiTT:AmbiguousCircuitSpec", ...
        "Circuit spec has unclear or unsupported regions. Clarify before generating SATK task. %s", strjoin(problems, " | "));
end
end

function text = valueToText(value)
if isempty(value)
    text = "";
elseif isstring(value)
    text = strjoin(value(:)', ", ");
elseif ischar(value)
    text = string(value);
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value{i});
    end
    text = strjoin(parts(:)', ", ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end

function lines = nonidealProfileSection(profiles)
if isempty(profiles)
    lines = "## Nonideal Device Profiles" + newline + ...
        "No recognized part-number profile was detected. If the spec names a real op-amp part, preserve its nonideal behavior rather than silently replacing it with an ideal op-amp.";
    return
end

parts = [
    "## Nonideal Device Profiles"
    "The circuit spec names a real op-amp part. Model these nonidealities explicitly when they can affect the requested teaching/probe path."
    "Do not use the Foundation Library ideal Op-Amp alone for these devices."
    "If SATK cannot express every nonideality directly, add the closest Simscape Electrical sources/resistors/controlled sources and document any omission in the agent report."
    "```json"
    string(feval('citt.util.jsonEncode', profiles))
    "```"
];
lines = strjoin(parts, newline);
end

function text = repoLocalSatkInstructionsSection(config)
root = fullfile(config.MatlabRoot, "resources", "agent_instructions", "simulink_agentic_toolkit");
agentsPath = fullfile(root, "AGENTS.md");
cittAgentsPath = fullfile(root, "CITT_AGENTS.md");
registryPath = fullfile(root, "tools", "registry.json");
toolsPath = fullfile(root, "tools", "tools.json");

if exist(agentsPath, "file") ~= 2
    text = strjoin([
        "## Repo-Local SATK Agent Instructions"
        "CiTT expected a local SATK AGENTS.md copy but did not find it at `" + string(agentsPath) + "`."
        "Use the explicit tool rules in this task and do not read external skill directories."
    ], newline);
    return
end

cittAgentsText = "";
if exist(cittAgentsPath, "file") == 2
    cittAgentsText = string(fileread(cittAgentsPath));
end
agentsText = string(fileread(agentsPath));
text = strjoin([
    "## Repo-Local SATK Agent Instructions"
    "CiTT has vendored the Simulink Agentic Toolkit agent instructions into the repository. Use the embedded copy below; do not read external skill directories."
    "Local reference directory: `" + string(root) + "`"
    "CiTT addendum copy: `" + string(cittAgentsPath) + "`"
    "Tool registry copy: `" + string(registryPath) + "`"
    "Tool metadata copy: `" + string(toolsPath) + "`"
    ""
    "```markdown"
    agentsText
    "```"
    ""
    "```markdown"
    cittAgentsText
    "```"
], newline);
end

function text = simscapeUtilizationContractSection()
text = strjoin([
    "## Simscape Utilization Contract"
    "- Before editing, inspect the model with model_overview/model_read when a model already exists."
    "- For physical networks, use Simscape or Simscape Electrical library blocks rather than pure Simulink substitutes."
    "- Include Solver Configuration and domain reference blocks for every physical network."
    "- Preserve unit-bearing parameters and named workspace variables; resolve them with model_query_params/model_resolve_params when needed."
    "- Log requested outputs through sensors, PS-Simulink converters, To Workspace blocks, scopes, or outports."
    "- Run model_check after structural edits and report any unresolved unconnected ports, dangling lines, or lint failures."
    "- Write focus/probe maps that prove which physical blocks, sensors, and logged outputs support the lesson."
], newline);
end

function text = satkProjectPolicySection(config, presetResult, presetError)
lines = [
    "## SATK Project Library Policy"
    "CiTT project root: `" + string(config.SatkProjectRoot) + "`"
    ""
    "CiTT has no custom teaching block library configured for this release."
    "The SATK library gate should be satisfied by `.satk/reuse-libraries.json` with `confirmedNone=true`."
    "Do not stop to ask about reusable libraries for this build."
    "Use built-in MATLAB, Simulink, Simscape, and Simscape Electrical blocks unless the user later configures a CiTT teaching library."
];
if isstruct(presetResult) && ~isempty(presetResult) && isfield(presetResult, "messages")
    lines = [lines; ""; "Preset status:"; "- " + string(presetResult.messages(:))];
elseif ~isempty(presetError) && strlength(strtrim(string(presetError))) > 0
    lines = [lines; ""; "Preset status:"; "- CiTT could not confirm the SATK preset before writing this task: " + string(presetError)];
end
text = strjoin(lines, newline);
end

function text = signalLevelTestInterfaceSection()
text = strjoin([
    "## Signal-Level Teaching/Test Interface Contract"
    "- Keep the physical circuit in a subsystem named `CiTT_PhysicalCircuit` when practical."
    "- Add a signal-level wrapper subsystem named `CiTT_TestInterface` when the model includes Simscape physical ports or when CiTT model tests are expected."
    "- `CiTT_TestInterface` should expose standard Simulink Inport/Outport signals such as `Vin` and `Vout`."
    "- Inside the wrapper, use Simulink-PS Converter blocks to drive physical sources and sensor + PS-Simulink Converter blocks to expose measurements."
    "- Do not run behavioral model tests directly against Simscape physical modeling ports; test the signal-based wrapper."
    "- Add wrapper paths and measurement outputs to the probe map when they support the lesson."
], newline);
end

function text = stateflowTeachingLogicContractSection()
text = strjoin([
    "## Stateflow Teaching Logic Contract"
    "If the circuit spec includes ADC logic, threshold detection, artifact detection, mode switching, digital control, or state-dependent behavior:"
    "- Use Stateflow for explicit decision/state logic when it is clearer than ad hoc Simulink switch blocks."
    "- Keep analog and physical behavior in Simscape."
    "- Expose Stateflow state or decision outputs through named Simulink signals when they are part of requested teaching or probe evidence."
    "- Add Stateflow chart paths and state names to the focus map when they support a teaching question."
    "- Add probe entries for ADC code, threshold decision, mode state, or artifact-detected signals when requested."
    "- Run model_check with stateflow_lint after chart editing."
], newline);
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if strlength(string(folder)) > 0 && exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
if fid < 0
    error("CiTT:WriteFailed", "Could not write: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end
