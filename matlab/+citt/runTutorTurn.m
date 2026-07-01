function turn = runTutorTurn(context, request)
%RUNTUTORTURN Decide one adaptive, model-grounded tutor move.
%
% The selected CLI produces a JSON teaching decision. MATLAB then records the
% student-model update and can execute exactly one allowed model tool.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(context)
    context = struct();
end
if nargin < 2 || isempty(request)
    request = struct();
end

context = normalizeContext(context, config);
request = normalizeRequest(request, context);
[plan, step, stepIndex] = currentTeachingStep(context, config);
studentModel = feval('citt.defaultStudentModel', context.StudentModel);

turn = baseTurn(step, stepIndex, request, studentModel);
if request.Action == "reveal"
    socratic = feval('citt.runSocraticTurn', plan, stepIndex, request.StudentText, ...
        struct("Action", "reveal", "AnswerImagePath", request.AnswerImagePath));
    turn.intent = "reveal_request";
    turn.classification = string(socratic.classification);
    turn.student_level = string(socratic.student_level);
    turn.pedagogical_move = "reveal";
    turn.reveal_allowed = true;
    turn.message = string(socratic.message);
    turn.student_model = appendTutorTurn(studentModel, turn, request.StudentText);
    return
end

if strlength(strtrim(request.StudentText)) == 0 || request.Action == "question"
    turn.intent = "question";
    turn.pedagogical_move = "ask";
    turn.message = string(firstFieldText(step, ["student_question", "question"], ...
        "What do you notice in the highlighted model evidence?"));
    turn.student_model = studentModel;
    return
end

decision = decideWithCli(context, step, request, studentModel, config);
turn = applyDecision(turn, decision, request);
studentModel = applyMasteryUpdates(studentModel, turn.student_model_update);

if request.ExecuteTools && turn.tool_action ~= "none"
    [toolResult, toolPayload] = executeTutorTool(turn.tool_action, turn.tool_target, context, step);
    turn.tool_result = toolResult;
    turn.tool_payload = toolPayload;
    if strlength(strtrim(turn.evidence_used)) == 0
        turn.evidence_used = fieldText(toolResult, "message");
    end
end

turn.student_model = appendTutorTurn(studentModel, turn, request.StudentText);
end

function context = normalizeContext(context, config)
defaults = struct();
defaults.TeachingPlan = [];
defaults.TeachingStepIndex = 1;
defaults.HintLevel = 0;
defaults.StudentModel = [];
defaults.ModelPath = config.GeneratedModelPath;
defaults.SpecPath = config.LastSpecPath;
defaults.FocusMapPath = config.FocusMapPath;
defaults.ProbeMapPath = config.ProbeMapPath;
defaults.LastModelCheck = [];
defaults.LastSimulation = [];
defaults.LastBode = [];
defaults.LastTeachingReview = [];
defaults.LastProbe = [];
defaults.LastSimulationScenarios = [];
defaults.LastLabDelta = [];

names = fieldnames(defaults);
for i = 1:numel(names)
    name = names{i};
    if ~isfield(context, name)
        context.(name) = defaults.(name);
    end
end
end

function request = normalizeRequest(request, context)
defaults = struct();
defaults.StudentText = "";
defaults.Action = "student_message";
defaults.HintLevel = context.HintLevel;
defaults.AnswerImagePath = "";
defaults.ExecuteTools = false;

names = fieldnames(defaults);
for i = 1:numel(names)
    name = names{i};
    if ~isfield(request, name)
        request.(name) = defaults.(name);
    end
end

request.StudentText = string(request.StudentText);
request.Action = lower(strtrim(string(request.Action)));
if request.Action == "hint"
    request.Action = "student_message";
end
request.HintLevel = max(0, round(double(request.HintLevel)));
request.AnswerImagePath = string(request.AnswerImagePath);
request.ExecuteTools = logical(request.ExecuteTools);
end

function [plan, step, stepIndex] = currentTeachingStep(context, config)
plan = context.TeachingPlan;
if isempty(plan) && exist(config.TeachingPlanPath, "file") == 2
    plan = jsondecode(fileread(config.TeachingPlanPath));
end
if isstruct(plan) && isfield(plan, "plan")
    plan = plan.plan;
end
if ~isstruct(plan) || ~isfield(plan, "steps") || isempty(plan.steps)
    error("CiTT:TutorTurnTeachingPlanMissing", ...
        "Tutor turn requires a teaching plan with at least one step.");
end

stepIndex = max(1, min(numel(plan.steps), round(double(context.TeachingStepIndex))));
step = plan.steps(stepIndex);
end

function turn = baseTurn(step, stepIndex, request, studentModel)
turn = struct();
turn.success = true;
turn.step_index = stepIndex;
turn.step_id = firstFieldText(step, ["id", "step_id"], "step_" + string(stepIndex));
turn.focus_id = firstFieldText(step, ["focus_id"], "");
turn.title = firstFieldText(step, ["title", "label"], "");
turn.action = request.Action;
turn.intent = "answer";
turn.classification = "tutor_decision";
turn.student_level = "developing";
turn.misconception = "";
turn.student_model_update = struct();
turn.pedagogical_move = "hint";
turn.tool_action = "none";
turn.tool_target = "";
turn.tool_payload = struct();
turn.tool_result = [];
turn.message = "";
turn.evidence_used = "";
turn.reveal_allowed = false;
turn.advance_allowed = false;
turn.next_hint_level = request.HintLevel;
turn.student_model = studentModel;
end

function decision = decideWithCli(context, step, request, studentModel, config)
[raw, runner] = callConfiguredCli(context, step, request, studentModel, config);
decision = decodeTutorDecision(raw, runner.name);
end

function [rawText, runner] = callConfiguredCli(context, step, request, studentModel, config)
runner = selectCliRunner(config);
taskPath = string(fullfile(config.WorkDir, "citt_tutor_turn_task.md"));
stdoutPath = string(fullfile(config.WorkDir, "citt_tutor_turn_stdout.log"));
stderrPath = string(fullfile(config.WorkDir, "citt_tutor_turn_stderr.log"));

writeText(taskPath, buildTutorPrompt(context, step, request, studentModel, config, runner.name));

command = runner.command;
if runner.uses_template
    command = commandFromTemplate(command, taskPath);
end
if runner.name == "codex" && strlength(strtrim(request.AnswerImagePath)) > 0 && ...
        exist(request.AnswerImagePath, "file") == 2
    command = replace(command, " -", " --image " + shellQuote(request.AnswerImagePath) + " -");
end

systemResult = feval('citt.util.safeSystem', command);
writeText(stdoutPath, systemResult.stdout);
writeText(stderrPath, systemResult.stderr);
if systemResult.status ~= 0
    error("CiTT:TutorCliFailed", ...
        "%s tutor planner exited with status %d. See %s and %s.", ...
        runner.name, systemResult.status, stdoutPath, stderrPath);
end
rawText = string(systemResult.stdout);
end

function prompt = buildTutorPrompt(context, step, request, studentModel, config, runnerName)
systemPrompt = string(fileread(fullfile(config.MatlabRoot, "resources", "prompts", "dynamic_tutor_system.txt")));
schemaText = string(fileread(fullfile(config.MatlabRoot, "resources", "schemas", "tutor_turn_schema.json")));
studentModelForPrompt = studentModel;
studentModelForPrompt.turns = recentTurns(studentModel.turns, 6);
evidence = tutorEvidenceContext(context, step);

imageLine = "No student answer image attached.";
if strlength(strtrim(request.AnswerImagePath)) > 0
    imageLine = "Student answer image source path: " + request.AnswerImagePath + ...
        ". Use the selected CLI image capability if available; otherwise mention image uncertainty in misconception.";
end

prompt = strjoin([
    "You are CiTT's selected CLI dynamic tutor planner."
    "Selected CLI: " + string(runnerName)
    string(systemPrompt)
    ""
    "Return exactly one JSON object. Do not wrap the JSON in markdown."
    "Use only facts present in the teaching step, model evidence, focus map, probe map, or simulation summaries below."
    "Allowed tool_action values are: none, highlight_focus, measure_probe, run_simulation, run_bode, next_step, reveal."
    "Request at most one tool action. Prefer none when the next visible check can be asked in the message."
    "Do not reveal final numerical values unless reveal_allowed is true and the student asked to reveal."
    ""
    "Tutor turn JSON schema:"
    schemaText
    ""
    "Current teaching step JSON:"
    string(feval('citt.util.jsonEncode', step))
    ""
    "Persistent student model JSON:"
    string(feval('citt.util.jsonEncode', studentModelForPrompt))
    ""
    "Current model evidence JSON:"
    string(feval('citt.util.jsonEncode', evidence))
    ""
    "Student utterance JSON:"
    string(feval('citt.util.jsonEncode', struct("text", request.StudentText)))
    ""
    string(imageLine)
], newline);
end

function evidence = tutorEvidenceContext(context, step)
focusId = firstFieldText(step, ["focus_id"], "");
evidence = struct();
evidence.model_path = string(context.ModelPath);
evidence.spec_path = string(context.SpecPath);
evidence.focus_map_path = string(context.FocusMapPath);
evidence.probe_map_path = string(context.ProbeMapPath);
evidence.current_focus = compactValue(findMapItem(context.FocusMapPath, ["focus_map", "items"], ["focus_id", "id"], focusId), 2500);
evidence.current_probe = compactValue(findProbeForFocus(context.ProbeMapPath, focusId), 2500);
evidence.model_check = compactValue(context.LastModelCheck, 1800);
evidence.simulation = compactValue(context.LastSimulation, 2200);
evidence.bode = compactValue(context.LastBode, 2200);
evidence.last_probe = compactValue(context.LastProbe, 2200);
evidence.teaching_review = compactValue(context.LastTeachingReview, 1800);
evidence.simulation_scenarios = compactValue(context.LastSimulationScenarios, 1800);
evidence.lab_delta = compactValue(context.LastLabDelta, 1600);
end

function item = findProbeForFocus(probeMapPath, focusId)
item = [];
items = readMapItems(probeMapPath, ["probe_map", "probes", "items"]);
if isempty(items)
    return
end
for i = 1:numel(items)
    itemFocus = firstFieldText(items(i), ["focus_id"], "");
    if strlength(itemFocus) == 0 || itemFocus == focusId
        item = items(i);
        return
    end
end
item = items(1);
end

function item = findMapItem(mapPath, wrapperFields, idFields, idValue)
item = [];
items = readMapItems(mapPath, wrapperFields);
if isempty(items)
    return
end
for i = 1:numel(items)
    itemId = firstFieldText(items(i), idFields, "");
    if itemId == idValue
        item = items(i);
        return
    end
end
item = items(1);
end

function items = readMapItems(path, wrapperFields)
items = struct([]);
path = string(path);
if strlength(strtrim(path)) == 0 || exist(path, "file") ~= 2
    return
end
try
    data = jsondecode(fileread(path));
catch
    return
end
if ~isstruct(data)
    return
end
for i = 1:numel(wrapperFields)
    fieldName = wrapperFields(i);
    if isfield(data, fieldName)
        items = data.(fieldName);
        return
    end
end
items = data;
end

function value = compactValue(value, maxChars)
if isempty(value)
    value = "";
    return
end
try
    text = string(feval('citt.util.jsonEncode', value));
catch
    text = string(value);
end
value = truncateText(text, maxChars);
end

function turns = recentTurns(turns, count)
if ~isstruct(turns) || isempty(turns)
    defaultModel = feval('citt.defaultStudentModel');
    turns = defaultModel.turns;
    return
end
startIndex = max(1, numel(turns) - count + 1);
turns = turns(startIndex:end);
end

function turn = applyDecision(turn, decision, request)
turn.intent = normalizeChoice(firstFieldText(decision, ["intent"], "answer"), ...
    ["answer", "question", "confusion", "measure_request", "reveal_request", "off_track", "challenge"], "answer");
turn.student_level = normalizeChoice(firstFieldText(decision, ["student_level"], "developing"), ...
    ["novice", "developing", "advanced"], "developing");
turn.misconception = firstFieldText(decision, ["misconception"], "");
turn.student_model_update = optionalStruct(decision, "mastery_updates");
turn.pedagogical_move = normalizeChoice(firstFieldText(decision, ["pedagogical_move", "next_teaching_move"], "hint"), ...
    ["ask", "hint", "probe", "highlight", "simulate", "compare", "reveal", "advance", "remediate"], "hint");
turn.tool_action = normalizeToolAction(firstFieldText(decision, ["tool_action"], "none"));
turn.tool_target = firstFieldText(decision, ["tool_target", "target"], "");
turn.message = firstNonempty( ...
    firstFieldText(decision, ["message", "student_message"], ""), ...
    firstFieldText(decision, ["next_hint"], ""), ...
    defaultTutorMessage(turn));
turn.evidence_used = evidenceText(decision);
turn.reveal_allowed = optionalBool(decision, "reveal_allowed", turn.intent == "reveal_request");
turn.advance_allowed = optionalBool(decision, "advance_allowed", turn.pedagogical_move == "advance");
turn.next_hint_level = nextHintLevel(request.HintLevel, turn);
end

function level = nextHintLevel(currentLevel, turn)
if turn.pedagogical_move == "advance" || turn.student_level == "advanced"
    level = currentLevel;
elseif ismember(turn.pedagogical_move, ["hint", "probe", "highlight", "compare", "remediate"])
    level = currentLevel + 1;
else
    level = currentLevel;
end
end

function message = defaultTutorMessage(turn)
if strlength(strtrim(turn.focus_id)) > 0
    message = "Check the highlighted model region for " + turn.focus_id + ...
        ". Name the measured node and its reference before calculating.";
else
    message = "Check the visible model evidence first. Name the measured node and its reference before calculating.";
end
end

function text = evidenceText(decision)
text = firstFieldText(decision, ["evidence_used", "why"], "");
if strlength(strtrim(text)) > 0
    return
end
needed = firstFieldText(decision, ["evidence_needed"], "");
if strlength(strtrim(needed)) > 0
    text = "Needs evidence: " + needed;
end
end

function model = applyMasteryUpdates(model, updates)
if ~isstruct(updates) || isempty(updates)
    return
end
fields = string(fieldnames(updates));
for i = 1:numel(fields)
    name = matlab.lang.makeValidName(char(fields(i)));
    if strlength(string(name)) == 0
        continue
    end
    model.(name) = firstFieldText(updates, fields(i), "unknown");
end
end

function model = appendTutorTurn(model, turn, studentText)
entry = struct( ...
    "time", string(datetime("now")), ...
    "step_id", string(turn.step_id), ...
    "focus_id", string(turn.focus_id), ...
    "student_text", truncateText(string(studentText), 500), ...
    "intent", string(turn.intent), ...
    "student_level", string(turn.student_level), ...
    "misconception", truncateText(string(turn.misconception), 500), ...
    "pedagogical_move", string(turn.pedagogical_move), ...
    "tool_action", string(turn.tool_action), ...
    "tool_target", string(turn.tool_target), ...
    "message", truncateText(string(turn.message), 800), ...
    "evidence_used", truncateText(string(turn.evidence_used), 500));

model = feval('citt.defaultStudentModel', model);
model.turns(end + 1, 1) = entry;
if numel(model.turns) > 50
    model.turns = model.turns(end - 49:end);
end
end

function [result, payload] = executeTutorTool(toolAction, toolTarget, context, step)
toolAction = normalizeToolAction(toolAction);
target = firstNonempty(toolTarget, firstFieldText(step, ["focus_id"], ""));
payload = struct("command", "", "target", target);
result = [];

try
    switch toolAction
        case "highlight_focus"
            payload.command = "highlight " + target;
            result = feval('citt.runNaturalCommand', payload.command, context);
        case "measure_probe"
            payload.command = "measure " + target;
            result = feval('citt.runNaturalCommand', payload.command, context);
        case "run_simulation"
            result = struct("success", false, "action", "run_simulation", "message", "Simulation was not run.", "details", []);
            details = feval('citt.runSimulation', context.ModelPath);
            result.success = isTruthy(fieldText(details, "success"));
            result.message = "Simulation complete.";
            result.details = details;
        case "run_bode"
            result = struct("success", false, "action", "bode_analysis", "message", "Bode analysis was not run.", "details", []);
            details = feval('citt.runBodeAnalysis', context);
            result.success = isTruthy(fieldText(details, "success"));
            result.message = "Bode analysis complete.";
            result.details = details;
        otherwise
            result = struct("success", true, "action", "none", "message", "No tool action requested.", "details", []);
    end
catch toolError
    result = struct( ...
        "success", false, ...
        "action", toolAction, ...
        "message", "Tutor tool action failed: " + string(toolError.message), ...
        "details", []);
end
end

function decision = decodeTutorDecision(raw, runnerName)
cleaned = stripJsonFences(raw);
try
    decision = jsondecode(char(cleaned));
    return
catch
end

candidates = extractJsonObjectCandidates(cleaned);
for i = numel(candidates):-1:1
    try
        decision = jsondecode(char(candidates(i)));
        return
    catch
    end
end

error("CiTT:TutorCliNoJson", ...
    "%s did not return a valid tutor decision JSON object.", runnerName);
end

function runner = selectCliRunner(config)
runner = struct("name", "", "command", "", "uses_template", false);
if strlength(strtrim(config.AgentCommand)) > 0
    runner.name = "configured_cli";
    runner.command = string(config.AgentCommand);
    runner.uses_template = true;
    return
end

error("CiTT:TutorCliMissing", ...
    "No selected CLI command is configured for tutor turns. Set CITT_AGENT_COMMAND or save a CLI template in Settings; CiTT will not auto-select another CLI.");
end

function command = commandFromTemplate(commandTemplate, taskPath)
command = string(commandTemplate);
quotedTaskPath = shellQuote(taskPath);
if contains(command, "{taskPath}")
    command = replace(command, "{taskPath}", quotedTaskPath);
elseif contains(command, "{task}")
    command = replace(command, "{task}", quotedTaskPath);
else
    command = strtrim(command) + " " + quotedTaskPath;
end
end

function text = stripJsonFences(text)
text = strtrim(string(text));
text = regexprep(text, "^```(?:json)?\s*", "");
text = regexprep(text, "\s*```$", "");
text = strtrim(text);
end

function candidates = extractJsonObjectCandidates(text)
text = char(string(text));
candidates = strings(0, 1);
starts = find(text == '{');
quote = char(34);
backslash = char(92);
for i = 1:numel(starts)
    startIndex = starts(i);
    depth = 0;
    inString = false;
    escaped = false;
    for j = startIndex:numel(text)
        ch = text(j);
        if inString
            if escaped
                escaped = false;
            elseif ch == backslash
                escaped = true;
            elseif ch == quote
                inString = false;
            end
            continue
        end

        if ch == quote
            inString = true;
        elseif ch == '{'
            depth = depth + 1;
        elseif ch == '}'
            depth = depth - 1;
            if depth == 0
                candidates(end + 1, 1) = string(text(startIndex:j)); %#ok<AGROW>
                break
            end
        end
    end
end
end

function value = normalizeToolAction(value)
value = lower(strtrim(string(value)));
switch value
    case {"", "null", "none", "no_tool"}
        value = "none";
    case {"highlight", "highlight_focus", "show_model_region"}
        value = "highlight_focus";
    case {"measure", "measure_probe", "probe"}
        value = "measure_probe";
    case {"simulate", "run_simulation"}
        value = "run_simulation";
    case {"bode", "run_bode", "frequency_response"}
        value = "run_bode";
    case {"advance", "next_step"}
        value = "next_step";
    case {"reveal", "show_reveal"}
        value = "reveal";
    otherwise
        value = "none";
end
end

function value = normalizeChoice(value, allowed, fallback)
value = lower(strtrim(string(value)));
if ~any(value == allowed)
    value = string(fallback);
end
end

function value = optionalStruct(data, fieldName)
value = struct();
if isstruct(data) && isfield(data, fieldName) && isstruct(data.(fieldName))
    value = data.(fieldName);
end
end

function value = optionalBool(data, fieldName, fallback)
value = logical(fallback);
if ~isstruct(data) || ~isfield(data, fieldName)
    return
end
raw = data.(fieldName);
if islogical(raw)
    value = logical(raw);
elseif isnumeric(raw)
    value = raw ~= 0;
else
    text = lower(strtrim(string(raw)));
    value = any(text == ["true", "1", "yes"]);
end
end

function text = firstFieldText(data, fieldNames, fallback)
if nargin < 3
    fallback = "";
end
text = string(fallback);
if ~isstruct(data)
    return
end
for i = 1:numel(fieldNames)
    fieldName = string(fieldNames(i));
    if isfield(data, fieldName)
        text = scalarText(data.(fieldName), fallback);
        if strlength(strtrim(text)) > 0
            return
        end
    end
end
end

function text = fieldText(data, fieldName)
text = firstFieldText(data, string(fieldName), "");
end

function text = scalarText(value, fallback)
if nargin < 2
    fallback = "";
end
try
    values = string(value);
catch
    text = string(fallback);
    return
end
values = values(:);
if isempty(values)
    text = string(fallback);
else
    text = values(1);
end
end

function text = firstNonempty(varargin)
text = "";
for i = 1:nargin
    candidate = string(varargin{i});
    if strlength(strtrim(candidate)) > 0
        text = candidate;
        return
    end
end
end

function tf = isTruthy(value)
text = lower(strtrim(scalarText(value, "")));
tf = any(text == ["true", "1", "yes"]);
end

function text = truncateText(text, maxChars)
text = string(text);
if strlength(text) <= maxChars
    return
end
text = extractBefore(text, maxChars) + "...";
end

function writeText(path, text)
[folder, ~, ~] = fileparts(char(path));
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(char(path), "w");
if fid < 0
    error("CiTT:FileWriteFailed", "Could not write file: %s", path);
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
delete(cleanup);
end

function quoted = shellQuote(value)
raw = char(string(value));
if ispc
    raw = strrep(raw, '"', '\"');
    quoted = """" + string(raw) + """";
else
    singleQuote = char(39);
    doubleQuote = char(34);
    replacement = [singleQuote doubleQuote singleQuote doubleQuote singleQuote];
    raw = strrep(raw, singleQuote, replacement);
    quoted = string([singleQuote raw singleQuote]);
end
end
