function turn = runSocraticTurn(teachingPlanInput, stepIndex, studentAnswer, options)
%RUNSOCRATICTURN Return one Socratic question, hint, classification, or reveal.

if nargin < 2 || isempty(stepIndex)
    stepIndex = 1;
end
if nargin < 3 || isempty(studentAnswer)
    studentAnswer = "";
end
if nargin < 4 || isempty(options)
    options = struct();
end

action = "question";
if isfield(options, "Action")
    action = string(options.Action);
end
hintLevel = 0;
if isfield(options, "HintLevel")
    hintLevel = double(options.HintLevel);
end

plan = readPlan(teachingPlanInput);
steps = plan.steps;
stepIndex = max(1, min(numel(steps), round(stepIndex)));
step = steps(stepIndex);

turn = struct();
turn.step_index = stepIndex;
turn.step_id = string(step.id);
turn.focus_id = string(step.focus_id);
turn.title = string(step.title);
turn.action = action;
turn.classification = "not_evaluated";
turn.reveal_allowed = false;
turn.message = "";
turn.next_hint_level = hintLevel;

if action == "reveal"
    turn.reveal_allowed = true;
    turn.classification = "revealed";
    turn.message = "Reasoning to compare with: " + string(step.expected_reasoning) + ...
        newline + "Common mistake to watch: " + string(step.common_mistake);
    return
end

if strlength(strtrim(string(studentAnswer))) == 0 || action == "question"
    turn.message = string(step.student_question);
    return
end

classification = classifyAnswer(step, studentAnswer, options);
turn.classification = classification.label;

if classification.is_reasonable
    if strlength(strtrim(classification.next_hint)) > 0
        turn.message = "Good. " + classification.next_hint;
    else
        turn.message = "Good. This connects the measured node to the reference and shows why loading through the electrode resistance would corrupt the voltage reading.";
    end
    turn.next_hint_level = hintLevel;
else
    turn.next_hint_level = hintLevel + 1;
    if hintLevel <= 0
        turn.message = string(step.reveal_hint);
    else
        turn.message = "Try checking this possible trap: " + string(step.common_mistake);
    end
end
end

function classification = classifyAnswer(step, studentAnswer, options)
if isfield(options, "UseGemini") && ~logical(options.UseGemini)
    error("CiTT:GeminiRequired", "Socratic teaching requires Gemini in real-run mode.");
end
classification = classifyWithGemini(step, studentAnswer);
end

function classification = classifyWithGemini(step, studentAnswer)
config = feval('citt.loadConfig');
if strlength(config.GeminiApiKey) == 0
    error("CiTT:GeminiKeyMissing", "No Gemini key for Socratic classification.");
end

systemPrompt = fileread(fullfile(config.MatlabRoot, "resources", "prompts", "socratic_teaching_system.txt"));
prompt = strjoin([
    string(systemPrompt)
    ""
    "Classify this student answer as exactly one JSON object with fields label, is_reasonable, misconception, next_hint."
    "Do not wrap the JSON in markdown. Do not include text before or after the JSON object."
    "Use only JSON strings, booleans, and nulls. Escape any quotes or newlines inside strings."
    "Keep next_hint as one short line."
    "Do not solve the circuit or reveal final numerical values."
    ""
    "Teaching step:"
    string(feval('citt.util.jsonEncode', step))
    ""
    "Student answer encoded as JSON:"
    string(feval('citt.util.jsonEncode', struct("answer", string(studentAnswer))))
], newline);

content = struct();
content.role = "user";
content.parts = {struct("text", char(prompt))};
body = struct();
body.contents = {content};
body.generationConfig = struct("response_mime_type", "application/json");
url = "https://generativelanguage.googleapis.com/v1beta/models/" + ...
    config.GeminiModel + ":generateContent?key=" + config.GeminiApiKey;
response = webwrite(char(url), body, weboptions("MediaType", "application/json", "Timeout", 45));
raw = string(response.candidates(1).content.parts(1).text);
data = decodeClassification(raw, step, studentAnswer);

classification = struct();
classification.label = string(data.label);
classification.is_reasonable = logical(data.is_reasonable);
classification.misconception = getOptionalString(data, "misconception");
classification.next_hint = getOptionalString(data, "next_hint");
end

function data = decodeClassification(raw, step, studentAnswer)
cleaned = stripJsonFences(raw);
try
    data = jsondecode(char(cleaned));
    data = normalizeClassification(data);
    return
catch
end

jsonObject = extractJsonObject(cleaned);
if strlength(jsonObject) > 0
    try
        data = jsondecode(char(jsonObject));
        data = normalizeClassification(data);
        return
    catch
    end
end

data = fallbackClassification(step, studentAnswer);
end

function text = stripJsonFences(text)
text = strtrim(string(text));
text = regexprep(text, "^```(?:json)?\s*", "");
text = regexprep(text, "\s*```$", "");
text = strtrim(text);
end

function jsonObject = extractJsonObject(text)
text = char(string(text));
startIndex = find(text == "{", 1, "first");
endIndex = find(text == "}", 1, "last");
if isempty(startIndex) || isempty(endIndex) || endIndex <= startIndex
    jsonObject = "";
else
    jsonObject = string(text(startIndex:endIndex));
end
end

function data = normalizeClassification(data)
if ~isfield(data, "label")
    data.label = "uncertain";
end
if ~isfield(data, "is_reasonable")
    data.is_reasonable = false;
end
if ~isfield(data, "misconception")
    data.misconception = "";
end
if ~isfield(data, "next_hint")
    data.next_hint = "";
end
end

function data = fallbackClassification(step, studentAnswer)
answer = lower(string(studentAnswer));
concept = lower(string(step.concept));
hasMeasuredNode = contains(answer, "v_m") || contains(answer, "vm") || contains(answer, "membrane");
hasReference = contains(answer, "reference") || contains(answer, "ground") || contains(answer, "gnd");
hasUnits = contains(answer, "ohm") || contains(answer, "ω") || contains(answer, "\omega") || ...
    contains(answer, "amp") || contains(answer, " a") || contains(answer, "volt") || contains(answer, " v");
hasLoading = contains(answer, "input impedance") || contains(answer, "high impedance") || ...
    contains(answer, "voltage drop") || contains(answer, "i_c") || contains(answer, "current") || ...
    contains(answer, "r_c") || contains(answer, "rc");

data = struct();
if hasMeasuredNode && hasReference && hasUnits && hasLoading
    data.label = "reasonable";
    data.is_reasonable = true;
    data.misconception = "";
    data.next_hint = "Connect the measured node to the reference node and state why the electrode drop is approximately zero volts.";
elseif contains(concept, "reference") && ~hasReference
    data.label = "missing_reference";
    data.is_reasonable = false;
    data.misconception = "The answer does not name the reference node.";
    data.next_hint = "Say what voltage is measured relative to ground before discussing the buffer.";
elseif ~hasUnits
    data.label = "missing_units";
    data.is_reasonable = false;
    data.misconception = "The answer skips units.";
    data.next_hint = "Use Ohm's law with amperes, ohms, and volts.";
else
    data.label = "uncertain";
    data.is_reasonable = false;
    data.misconception = "The answer could not be safely classified as complete.";
    data.next_hint = "Name the measured node, reference node, current through Rc, and voltage drop across Rc.";
end
end

function plan = readPlan(inputValue)
if isstruct(inputValue)
    if isfield(inputValue, "plan")
        plan = inputValue.plan;
    else
        plan = inputValue;
    end
    return
end
path = string(inputValue);
if strlength(path) == 0
    config = feval('citt.loadConfig');
    path = config.TeachingPlanPath;
end
if exist(path, "file") ~= 2
    error("CiTT:TeachingPlanMissing", "Teaching plan not found: %s", path);
end
plan = jsondecode(fileread(path));
end

function value = getOptionalString(data, fieldName)
if isfield(data, fieldName)
    value = string(data.(fieldName));
else
    value = "";
end
end
