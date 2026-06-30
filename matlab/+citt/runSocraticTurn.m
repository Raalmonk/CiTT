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
turn.student_level = "not_evaluated";
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
turn.student_level = classification.student_level;

if classification.is_reasonable
    turn.message = correctFeedback(step, classification);
    turn.next_hint_level = hintLevel;
else
    turn.next_hint_level = hintLevel + 1;
    turn.message = revisionFeedback(step, classification, hintLevel);
end
end

function message = correctFeedback(step, classification)
hint = studentFacingText(strtrim(string(classification.next_hint)));
if strlength(hint) == 0
    hint = "connect the measured node, reference node, and the component law that explains the observed behavior.";
end

switch string(classification.student_level)
    case "novice"
        message = "Level: novice. Good start. Keep the task tiny: " + hint + ...
            " Answer with one sentence about the visible node and ground; no formula needed yet.";
    case "advanced"
        message = "Level: advanced. Good. Now stress-test the assumption behind your answer: " + hint + ...
            " Tie it to probe placement, units, or settling behavior before moving on.";
    otherwise
        message = "Level: developing. Good. " + hint + ...
            " Add one concrete piece of evidence from the model so the explanation is checkable.";
end
end

function message = revisionFeedback(step, classification, hintLevel)
hint = studentFacingText(strtrim(string(classification.next_hint)));
misconception = studentFacingText(strtrim(string(classification.misconception)));
if strlength(hint) == 0
    if hintLevel <= 0
        hint = studentFacingText(string(step.reveal_hint));
    else
        hint = studentFacingText(string(step.common_mistake));
    end
end
if strlength(misconception) == 0
    misconception = studentFacingText(string(step.common_mistake));
end

switch string(classification.student_level)
    case "novice"
        message = "Level: novice. Start with the visible circuit, not the whole math story: " + hint + ...
            " A useful next answer can be only one sentence.";
    case "advanced"
        message = "Level: advanced. Your answer needs a sharper check: " + misconception + ...
            " Reconcile that with the probe location, units, and the limiting component.";
    otherwise
        if hintLevel <= 0
            message = "Level: developing. Check this part: " + hint;
        else
            message = "Level: developing. Try checking this possible trap: " + misconception;
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
classification = classifyWithCli(step, studentAnswer, options);
end

function classification = classifyWithCli(step, studentAnswer, options)
config = feval('citt.loadConfig');
[raw, runner] = callConfiguredCli(step, studentAnswer, options, config);
data = decodeClassification(raw, runner.name);

classification = struct();
classification.label = string(data.label);
classification.is_reasonable = logical(data.is_reasonable);
classification.student_level = normalizeStudentLevel(data.student_level);
classification.misconception = getOptionalString(data, "misconception");
classification.next_hint = getOptionalString(data, "next_hint");
end

function [rawText, runner] = callConfiguredCli(step, studentAnswer, options, config)
runner = selectCliRunner(config);
taskPath = string(fullfile(config.WorkDir, "citt_socratic_cli_task.md"));
stdoutPath = string(fullfile(config.WorkDir, "citt_socratic_cli_stdout.log"));
stderrPath = string(fullfile(config.WorkDir, "citt_socratic_cli_stderr.log"));

answerImagePath = "";
if isfield(options, "AnswerImagePath")
    answerImagePath = string(options.AnswerImagePath);
end
writeText(taskPath, buildClassificationPrompt(step, studentAnswer, answerImagePath, config, runner.name));

command = runner.command;
if runner.uses_template
    command = commandFromTemplate(command, taskPath);
end
if runner.name == "codex" && strlength(strtrim(answerImagePath)) > 0 && exist(answerImagePath, "file") == 2
    command = replace(command, " -", " --image " + shellQuote(answerImagePath) + " -");
end

systemResult = feval('citt.util.safeSystem', command);
writeText(stdoutPath, systemResult.stdout);
writeText(stderrPath, systemResult.stderr);
if systemResult.status ~= 0
    error("CiTT:SocraticCliFailed", ...
        "%s Socratic classifier exited with status %d. See %s and %s.", ...
        runner.name, systemResult.status, stdoutPath, stderrPath);
end
rawText = string(systemResult.stdout);
end

function prompt = buildClassificationPrompt(step, studentAnswer, answerImagePath, config, runnerName)
systemPrompt = string(fileread(fullfile(config.MatlabRoot, "resources", "prompts", "socratic_teaching_system.txt")));
imageLine = "No student answer image attached.";
if strlength(strtrim(string(answerImagePath))) > 0
    imageLine = "Student answer image source path: " + string(answerImagePath) + ...
        ". Use the selected CLI's image capability if available; otherwise state image uncertainty in misconception.";
end
prompt = strjoin([
    "You are CiTT's selected CLI Socratic classifier."
    "Selected CLI: " + string(runnerName)
    string(systemPrompt)
    ""
    "Classify this student answer as exactly one JSON object with fields label, is_reasonable, student_level, misconception, next_hint."
    "Do not wrap the JSON in markdown. Do not include text before or after the JSON object."
    "Use only JSON strings, booleans, and nulls. Escape any quotes or newlines inside strings."
    "Set student_level to exactly novice, developing, or advanced."
    "Use novice for vague, copied, uncertain, or no-node/no-unit answers; developing for partially correct answers with gaps; advanced for concise or complete answers that name the node/reference, relevant component law, units, or model evidence."
    "Do not judge by length alone: a short answer can be advanced if it is precise, and a long answer can be novice if it avoids the model evidence."
    "Keep next_hint as one short line."
    "For low-information answers, assume the student may be confused or avoiding typing; give one tiny visible next action, not a lecture."
    "Do not use internal component IDs such as R_AA, C_AA, VOUT_PROBE, or ADC_500HZ in next_hint or misconception. Say resistor, capacitor, Vout probe, input source, ground, or 500 Hz ADC."
    "Do not solve the circuit or reveal final numerical values."
    ""
    "Teaching step:"
    string(feval('citt.util.jsonEncode', step))
    ""
    "Student answer encoded as JSON:"
    string(feval('citt.util.jsonEncode', struct("answer", string(studentAnswer))))
    ""
    string(imageLine)
], newline);
end

function runner = selectCliRunner(config)
runner = struct("name", "", "command", "", "uses_template", false);
if strlength(strtrim(config.AgentCommand)) > 0
    runner.name = "configured_cli";
    runner.command = string(config.AgentCommand);
    runner.uses_template = true;
    return
end

error("CiTT:SocraticCliMissing", ...
    "No selected CLI command is configured for Socratic classification. Set CITT_AGENT_COMMAND or save a CLI template in Settings; CiTT will not auto-select another CLI.");
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

function data = decodeClassification(raw, runnerName)
cleaned = stripJsonFences(raw);
try
    data = jsondecode(char(cleaned));
    data = normalizeClassification(data);
    return
catch
end

candidates = extractJsonObjectCandidates(cleaned);
for i = numel(candidates):-1:1
    jsonObject = candidates(i);
    try
        data = jsondecode(char(jsonObject));
        data = normalizeClassification(data);
        return
    catch
        continue
    end
end

error("CiTT:SocraticCliNoJson", ...
    "%s did not return a valid Socratic classification JSON object.", runnerName);
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

function data = normalizeClassification(data)
required = ["label", "is_reasonable", "student_level"];
for i = 1:numel(required)
    if ~isfield(data, required(i))
        error("CiTT:SocraticClassificationInvalid", ...
            "Socratic classification JSON is missing field: %s", required(i));
    end
end
if ~isfield(data, "misconception")
    data.misconception = "";
end
if ~isfield(data, "next_hint")
    data.next_hint = "";
end
data.student_level = normalizeStudentLevel(data.student_level);
end

function value = normalizeStudentLevel(value)
value = lower(strtrim(string(value)));
if value == "beginner"
    value = "novice";
elseif value == "intermediate"
    value = "developing";
elseif value == "expert"
    value = "advanced";
end
if ~ismember(value, ["novice", "developing", "advanced"])
    error("CiTT:SocraticClassificationInvalid", ...
        "Socratic classification JSON has invalid student_level: %s", value);
end
end

function text = studentFacingText(text)
text = string(text);
if strlength(text) == 0
    return
end
patterns = [
    "\bC_AA_FAULT\b", "the 100 uF capacitor";
    "\bCERR_C_LP_100uF\b", "the 100 uF capacitor";
    "\bC_LP_ALT\b", "the 100 uF capacitor";
    "\bC_AA\b", "the capacitor";
    "\bC_LP_100nF\b", "the capacitor";
    "\bC_LP\b", "the capacitor";
    "\bR_AA\b", "the resistor";
    "\bR_LP_39p8k\b", "the resistor";
    "\bR_LP\b", "the resistor";
    "\bVOUT_PROBE\b", "the Vout probe";
    "\bADC_500HZ\b", "the 500 Hz ADC";
    "\bV_IN\b", "the input source";
    "\bgnd\b", "ground"
];
for i = 1:size(patterns, 1)
    text = regexprep(text, patterns(i, 1), patterns(i, 2));
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

function value = getOptionalString(data, fieldName)
if isfield(data, fieldName)
    value = string(data.(fieldName));
else
    value = "";
end
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
