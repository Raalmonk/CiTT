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
promptPath = fullfile(config.MatlabRoot, "resources", "prompts", "agent_build_simscape_model.txt");
basePrompt = string(fileread(promptPath));
specJson = string(feval('citt.util.jsonEncode', spec));

taskText = strjoin([
    "# CiTT Simscape Model Build Task"
    ""
    "You are operating inside MATLAB/Simulink with Simulink Agentic Toolkit."
    "Use the available MCP tools to inspect, build, edit, and check the model."
    "Required tools to prefer when present: model_overview, model_read, model_edit, model_check, model_query_params, model_resolve_params."
    ""
    "## Product Boundary"
    "Gemini parsed the circuit image/prompt into a structured model specification. Treat that spec as a starting point, not as numerical authority."
    "Your job is to build/check the Simulink/Simscape model. Do not write educational prose yet; CiTT will teach after the model exists."
    ""
    "## Simscape-First Requirements"
    "- Build a Simscape-first model from the structured circuit spec."
    "- Use Simscape and Simscape Electrical physical components when available."
    "- Use physical electrical connections and component schematics."
    "- Include Electrical Reference and Solver Configuration blocks as needed."
    "- Add voltage/current sensors or logging for requested outputs."
    "- If a source/component value is symbolic or omitted, keep it as a named model parameter instead of inventing a number."
    "- Values outside the requested/connected teaching path should not block structural model generation."
    "- Do not use a Simulink signal-flow substitute for the circuit."
    "- Do not solve with standalone MATLAB numeric code as the model-generation output."
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
    ""
    "## Probe Map Contract"
    "Each probe map item must include: probe_id, focus_id, label, target_type, model_paths, block_paths, quantity, unit, suggested_sensor_or_logging, instructions."
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
source = path;
end

function rejectBlockingSpec(spec)
problems = strings(0, 1);
if isfield(spec, "unsupported_or_unclear_regions") && ~isempty(spec.unsupported_or_unclear_regions)
    text = valueToText(spec.unsupported_or_unclear_regions);
    if strlength(strtrim(text)) > 0
        problems(end + 1) = "unsupported_or_unclear_regions: " + text;
    end
end
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
