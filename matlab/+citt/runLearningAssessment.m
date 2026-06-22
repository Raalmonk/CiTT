function report = runLearningAssessment(request, options)
%RUNLEARNINGASSESSMENT Score before/after concept answers for tutor evidence.

config = feval('citt.loadConfig');
if nargin < 1 || isempty(request)
    request = struct();
end
if nargin < 2 || isempty(options)
    options = struct();
end

jsonPath = optionString(options, "OutputPath", config.AssessmentReportPath);
markdownPath = optionString(options, "MarkdownPath", config.AssessmentMarkdownPath);

concept = fieldText(request, "concept", "circuit behavior");
beforeAnswer = fieldText(request, "before_answer", "");
afterAnswer = fieldText(request, "after_answer", "");
hintLevelsUsed = fieldNumber(request, "hint_levels_used", 0);
expectedKeywords = keywordsFromRequest(request, concept);

before = scoreAnswer(beforeAnswer, expectedKeywords);
after = scoreAnswer(afterAnswer, expectedKeywords);
gain = after.score - before.score;
finalCorrect = after.score >= 0.55 || (after.score >= 0.4 && gain > 0.15);

report = struct();
report.success = true;
report.created_at = string(datetime("now"));
report.concept = concept;
report.expected_keywords = expectedKeywords;
report.before = before;
report.after = after;
report.learning_gain = gain;
report.hint_levels_used = hintLevelsUsed;
report.final_correctness = finalCorrect;
report.misconception_detected = misconception(beforeAnswer, afterAnswer, expectedKeywords);
report.time_to_correction = fieldText(request, "time_to_correction", "not recorded");
report.report_path = string(jsonPath);
report.markdown_path = string(markdownPath);

writeJson(jsonPath, report);
writeText(markdownPath, renderMarkdown(report));
end

function keywords = keywordsFromRequest(request, concept)
if isstruct(request) && isfield(request, "expected_keywords")
    keywords = string(request.expected_keywords);
    keywords = keywords(strlength(strtrim(keywords)) > 0);
    if ~isempty(keywords)
        return
    end
end
base = lower(string(concept));
tokens = regexp(char(base), '[A-Za-z][A-Za-z0-9_+-]*', 'match');
keywords = unique(string(tokens), "stable");
stop = ["the", "and", "for", "with", "this", "that", "circuit", "behavior", "explain", "why"];
keywords = keywords(~ismember(keywords, stop));
if isempty(keywords)
    keywords = ["node", "component", "signal"];
end
end

function scored = scoreAnswer(answer, keywords)
answer = lower(string(answer));
hits = strings(0, 1);
for i = 1:numel(keywords)
    if contains(answer, lower(keywords(i)))
        hits(end + 1) = keywords(i); %#ok<AGROW>
    end
end
score = 0;
if ~isempty(keywords)
    score = numel(hits) / numel(keywords);
end
if strlength(strtrim(answer)) > 20
    score = min(1, score + 0.15);
end
scored = struct();
scored.answer = string(answer);
scored.keyword_hits = hits;
scored.score = score;
end

function text = misconception(beforeAnswer, afterAnswer, keywords)
beforeText = lower(string(beforeAnswer));
afterText = lower(string(afterAnswer));
if strlength(strtrim(beforeText)) == 0
    text = "missing pre-assessment answer";
elseif contains(beforeText, "guess") || contains(beforeText, "not sure") || contains(beforeText, "don't know")
    text = "low confidence or missing model-grounded reasoning";
else
    beforeScore = scoreAnswer(beforeAnswer, keywords);
    afterScore = scoreAnswer(afterAnswer, keywords);
    if isempty(beforeScore.keyword_hits) && ~isempty(afterScore.keyword_hits)
        text = "initial answer lacked target concept keywords";
    elseif contains(beforeText, "voltage") && contains(afterText, "current")
        text = "possible voltage/current role confusion improved after tutoring";
    else
        text = "not clearly detected";
    end
    return
end
end

function value = fieldText(container, fieldName, defaultValue)
if nargin < 3
    defaultValue = "";
end
if isstruct(container) && isfield(container, fieldName)
    value = string(container.(fieldName));
else
    value = string(defaultValue);
end
end

function value = fieldNumber(container, fieldName, defaultValue)
value = defaultValue;
if isstruct(container) && isfield(container, fieldName)
    raw = container.(fieldName);
    if isnumeric(raw) && isscalar(raw)
        value = double(raw);
    elseif isstring(raw) || ischar(raw)
        candidate = str2double(raw);
        if ~isnan(candidate)
            value = candidate;
        end
    end
end
end

function value = optionString(options, fieldName, defaultValue)
if isstruct(options) && isfield(options, fieldName)
    value = string(options.(fieldName));
else
    value = string(defaultValue);
end
end

function text = renderMarkdown(report)
lines = [
    "# CiTT Learning Gain / Student Assessment"
    ""
    "Created: " + report.created_at
    ""
    "- Concept: " + report.concept
    "- Before score: " + sprintf("%.2f", report.before.score)
    "- After score: " + sprintf("%.2f", report.after.score)
    "- Learning gain: " + sprintf("%.2f", report.learning_gain)
    "- Hint levels used: " + string(report.hint_levels_used)
    "- Final correctness: " + string(report.final_correctness)
    "- Misconception detected: " + report.misconception_detected
    "- Time to correction: " + report.time_to_correction
    ""
    "Expected keywords: " + strjoin(report.expected_keywords, ", ")
];
text = strjoin(lines, newline);
end

function writeJson(path, value)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", feval('citt.util.jsonEncode', value));
end

function writeText(path, text)
[folder, ~, ~] = fileparts(path);
if exist(folder, "dir") ~= 7
    mkdir(folder);
end
fid = fopen(path, "w");
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(text));
end
