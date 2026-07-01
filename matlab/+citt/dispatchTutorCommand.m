function result = dispatchTutorCommand(userText, state)
%DISPATCHTUTORCOMMAND Map a tutor text submission to a CiTT action.

if nargin < 1 || isempty(userText)
    userText = "";
end
if nargin < 2 || isempty(state)
    state = struct();
end

rawText = string(userText);
text = strtrim(rawText);
lowerText = lower(text);

result = struct();
result.action = "none";
result.payload = struct();
result.user_message = rawText;
result.assistant_preview = "I need a circuit prompt, image, or command.";

if strlength(text) == 0
    if hasImage(state)
        result.action = "run_pipeline";
        result.payload = struct("prompt", "");
        result.assistant_preview = "I will read the attached circuit image, build the model, and prepare the teaching evidence.";
    end
    return
end

[commandAction, commandPayload, preview] = slashCommand(lowerText, text);
if commandAction ~= ""
    result.action = commandAction;
    result.payload = commandPayload;
    result.assistant_preview = preview;
    return
end

if isMeasurementRequest(lowerText)
    result.action = "run_command";
    result.payload = struct("command", text, "probeAsk", stripMeasurementVerb(text));
    result.assistant_preview = "I will measure that from the current model evidence.";
    return
end

if teachingActive(state)
    result.action = "next_hint";
    result.payload = struct("studentAnswer", rawText);
    result.assistant_preview = "I will compare your answer with the current teaching focus.";
    return
end

if hasModel(state)
    result.action = "run_command";
    result.payload = struct("command", text);
    result.assistant_preview = "I will treat that as a model command.";
    return
end

result.action = "run_pipeline";
result.payload = struct("prompt", rawText);
result.assistant_preview = "I will read the circuit, build the model, and prepare the teaching evidence.";
end

function [action, payload, preview] = slashCommand(lowerText, originalText)
action = "";
payload = struct();
preview = "";

if startsWith(lowerText, "/test")
    action = "run_model_tests";
    preview = "I will run the SATK behavioral model tests.";
elseif startsWith(lowerText, "/review")
    action = "teaching_review";
    preview = "I will review the teaching model evidence.";
elseif startsWith(lowerText, "/trace")
    action = "learning_traceability";
    preview = "I will build the learning traceability report.";
elseif startsWith(lowerText, "/scenarios")
    action = "simulation_scenarios";
    preview = "I will run the SimulationInput teaching scenarios.";
elseif startsWith(lowerText, "/evidence") || contains(lowerText, "export evidence")
    action = "export_evidence";
    preview = "I will export the evidence pack.";
elseif startsWith(lowerText, "/simulate")
    action = "run_simulation";
    preview = "I will simulate the current model.";
elseif startsWith(lowerText, "/open model") || lowerText == "open model"
    action = "open_model";
    preview = "I will open the generated model.";
elseif startsWith(lowerText, "/open")
    action = "open_model";
    preview = "I will open the generated model.";
elseif startsWith(lowerText, "/")
    action = "run_command";
    payload = struct("command", extractAfter(originalText, 1));
    preview = "I will run that model command.";
end
end

function tf = isMeasurementRequest(lowerText)
tf = startsWith(lowerText, "measure ") || startsWith(lowerText, "probe ") || ...
    startsWith(lowerText, "scope ") || startsWith(lowerText, "观察") || ...
    startsWith(lowerText, "测量") || startsWith(lowerText, "探测");
end

function text = stripMeasurementVerb(rawText)
text = strtrim(regexprep(string(rawText), "^\s*(measure|probe|scope)\s+", "", "ignorecase"));
text = strtrim(regexprep(text, "^\s*(测量|探测|观察)\s*", ""));
end

function tf = teachingActive(state)
tf = isstruct(state) && isfield(state, "TeachingPlan") && ~isempty(state.TeachingPlan);
end

function tf = hasModel(state)
tf = false;
if ~isstruct(state) || ~isfield(state, "ModelPath")
    return
end
modelPath = string(state.ModelPath);
tf = strlength(strtrim(modelPath)) > 0 && (exist(modelPath, "file") == 2 || exist(modelPath, "file") == 4);
end

function tf = hasImage(state)
tf = isstruct(state) && isfield(state, "ImagePath") && strlength(strtrim(string(state.ImagePath))) > 0;
end
