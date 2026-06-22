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
    turn.message = revealMessage(step);
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

function message = revealMessage(step)
focusId = lower(string(step.focus_id));
concept = string(step.concept);

if contains(focusId, "electrode_interface")
    message = strjoin([
        "Answer: the pacing pulse drives current through $R_{LEAD}$ into the electrode node. The double-layer capacitor $C_{DL}$ stores charge during the short pulse, so the electrode voltage makes a transient jump instead of instantly following a steady DC divider."
        "After the pulse, the stored charge leaks back through $R_{ETI}$ toward body reference. The first-order recovery time constant is $tau=R_{ETI} C_{DL}=2 kOhm x 10 uF=20 ms$, so the electrode artifact itself should decay over a few tens of milliseconds."
        "The learning check is polarity and node choice: this is the voltage at `electrode_node` relative to `body_ref_0V`, before the protection resistor and high-pass recovery path."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "protection_clamp") || contains(focusId, "clamp")
    message = strjoin([
        "Answer: a positive pacing artifact reaches the protected amplifier node through $R_{PROT}$. If that node rises above the upper rail plus the diode drop, the high clamp conducts first; if it swings below ground by about a diode drop, the low clamp conducts."
        "$R_{PROT}$ is what keeps the clamp current limited, so the right question is not just whether the node saturates, but how long the clamp is active and how much charge is pushed into the recovery filter."
        "In this ECG case the 5 V positive pacing pulse makes the upper clamp the expected first limiter. The exact conduction interval should be read from the Simscape waveform."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "high_pass") || contains(focusId, "recovery")
    message = strjoin([
        "Answer: the high-pass recovery filter removes the 300 mV electrode polarization offset while passing the 1.2 Hz ECG. Its time constant is $tau=R_{HP} C_{HP}=330 kOhm x 1 uF=0.33 s$, giving $f_c approx 1/(2*pi*tau)=0.48 Hz$."
        "That cutoff is below the 1.2 Hz ECG, so the ECG can pass, but a large pacing artifact leaves a transient baseline recovery. You should expect the recovered ECG to become clean only after several recovery-filter time constants unless clamp charge extends the settling."
        "The student-facing evidence is the recovered ECG probe: look for the 1 mVpp waveform reappearing around the settled baseline."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "ecg_visibility") || contains(focusId, "visibility")
    message = strjoin([
        "Answer: the ECG is visible again when the recovered output shows a stable 1.2 Hz sinusoid with about 1 mV peak-to-peak amplitude, rather than a large monotonic recovery tail or clamp-limited plateau."
        "Use the recovered-output plot to mark the first time after the pacing pulse where the baseline error is small enough that the 1 mVpp oscillation is distinguishable. That timestamp is the recovery time; it should be reported from the simulation evidence, not guessed from the prompt alone."
        "The expected qualitative result is: pacing artifact first dominates, clamps/recovery filter settle, then the small ECG waveform becomes visible again."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "cutoff") || contains(focusId, "time_constant")
    message = strjoin([
        "Answer: the cutoff is set by the physical RC time constant. For this model, $R=39.8\,k\Omega$ and $C=100\,nF$, so $\tau=RC=3.98\,ms$."
        "The cutoff frequency is $f_c=\frac{1}{2\pi RC}$, which gives about $39.99\,Hz$. That is why the model passes the 5 Hz sensor signal with little loss but starts attenuating stronger interference above the cutoff."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "interference") || contains(focusId, "attenuation")
    message = strjoin([
        "Answer: after the cutoff is known, compare each frequency with $f_c$. The low-pass magnitude is $|H(jf)|=\frac{1}{\sqrt{1+(f/f_c)^2}}$."
        "At 60 Hz, the model gives about $-5.12\,dB$ of attenuation, so mains ripple is reduced but not eliminated. At the 250 Hz ADC Nyquist edge, the attenuation is about $-16.03\,dB$, so the output is much smaller before sampling."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "nyquist") || contains(focusId, "adc")
    message = strjoin([
        "Answer: a 500 Hz ADC has Nyquist frequency $f_N=\frac{f_s}{2}=250\,Hz$. The Simscape frequency-response check should therefore include the output at 250 Hz, not only the sensor band."
        "Because $250\,Hz$ is well above $f_c\approx39.99\,Hz$, the RC model attenuates that edge by about $-16.03\,dB$."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "wrong_capacitor") || contains(focusId, "mistake")
    message = strjoin([
        "Answer: replacing $100\,nF$ with $100\,\mu F$ makes the capacitor $1000\times$ larger, so $\tau=RC$ becomes $1000\times$ larger and $f_c=\frac{1}{2\pi RC}$ becomes $1000\times$ smaller."
        "That moves the cutoff from about $39.99\,Hz$ down to about $0.040\,Hz$, which would badly suppress the 5 Hz signal. This is the kind of lab error a pure text answer can miss unless it checks the actual model parameters."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif contains(focusId, "output_node") || contains(focusId, "vout")
    message = strjoin([
        "Answer: the output probe belongs at the capacitor node, measured relative to electrical reference. In this low-pass circuit, that node is $V_{out}=V_C$, so it shows the filtered version of the input."
        "If the probe is placed across the resistor instead, the plot answers the complementary high-pass question and the cutoff explanation no longer matches the requested output."
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
elseif strlength(strtrim(concept)) > 0
    message = strjoin([
        "Answer: " + concept
        "Reasoning to compare with: " + string(step.expected_reasoning)
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
else
    message = strjoin([
        "Answer: identify the measured node, its reference node, and the component that sets the dominant time constant or limit."
        "Reasoning to compare with: " + string(step.expected_reasoning)
        "Common mistake to watch: " + string(step.common_mistake)
    ], newline);
end
end

function classification = classifyAnswer(step, studentAnswer, options)
if isfield(options, "UseGemini") && ~logical(options.UseGemini)
    error("CiTT:GeminiRequired", "Socratic teaching requires Gemini in real-run mode.");
end
classification = classifyWithGemini(step, studentAnswer, options);
end

function classification = classifyWithGemini(step, studentAnswer, options)
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
    ""
    "If an image is attached, use it only to understand the student's sketch, equation, or marked circuit region."
], newline);

parts = {struct("text", char(prompt))};
answerImagePath = "";
if isfield(options, "AnswerImagePath")
    answerImagePath = string(options.AnswerImagePath);
end
if strlength(strtrim(answerImagePath)) > 0
    image = feval('citt.util.readImageBytes', answerImagePath);
    parts{end + 1} = struct("inline_data", struct( ...
        "mime_type", char(image.mime_type), ...
        "data", char(image.base64)));
end

content = struct();
content.role = "user";
content.parts = parts;
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
