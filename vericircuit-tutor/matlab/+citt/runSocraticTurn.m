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
    turn.message = "Good local frame. Now connect that idea to " + string(step.concept) + ...
        " without skipping the reference node or units.";
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
    "Classify this student answer as JSON with fields label, is_reasonable, misconception, next_hint."
    "Do not solve the circuit or reveal final numerical values."
    ""
    "Teaching step:"
    string(feval('citt.util.jsonEncode', step))
    ""
    "Student answer:"
    string(studentAnswer)
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
data = jsondecode(char(regexprep(strtrim(raw), "^```json\s*|\s*```$", "")));

classification = struct();
classification.label = string(data.label);
classification.is_reasonable = logical(data.is_reasonable);
classification.misconception = getOptionalString(data, "misconception");
classification.next_hint = getOptionalString(data, "next_hint");
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
