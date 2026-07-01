function model = defaultStudentModel(existing)
%DEFAULTSTUDENTMODEL Build or normalize CiTT's persistent student model.

if nargin < 1
    existing = [];
end

model = struct( ...
    "reference_node", "unknown", ...
    "polarity", "unknown", ...
    "units", "unknown", ...
    "component_law", "unknown", ...
    "probe_placement", "unknown", ...
    "settling_transient", "unknown", ...
    "sampling_aliasing", "unknown", ...
    "confidence", "unknown", ...
    "turns", emptyTurns());

if ~isstruct(existing) || isempty(existing)
    return
end

names = string(fieldnames(model));
for i = 1:numel(names)
    name = names(i);
    if ~isfield(existing, name)
        continue
    end
    if name == "turns"
        model.turns = normalizeTurns(existing.turns);
    else
        model.(name) = scalarString(existing.(name), model.(name));
    end
end
end

function turns = normalizeTurns(rawTurns)
turns = emptyTurns();
if ~isstruct(rawTurns) || isempty(rawTurns)
    return
end

template = emptyTurn();
names = string(fieldnames(template));
for i = 1:numel(rawTurns)
    item = template;
    for j = 1:numel(names)
        name = names(j);
        if isfield(rawTurns(i), name)
            item.(name) = scalarString(rawTurns(i).(name), item.(name));
        end
    end
    turns(end + 1, 1) = item; %#ok<AGROW>
end
end

function turns = emptyTurns()
turns = repmat(emptyTurn(), 0, 1);
end

function turn = emptyTurn()
turn = struct( ...
    "time", "", ...
    "step_id", "", ...
    "focus_id", "", ...
    "student_text", "", ...
    "intent", "", ...
    "student_level", "", ...
    "misconception", "", ...
    "pedagogical_move", "", ...
    "tool_action", "", ...
    "tool_target", "", ...
    "message", "", ...
    "evidence_used", "");
end

function text = scalarString(value, fallback)
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
