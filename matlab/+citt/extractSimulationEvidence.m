function evidence = extractSimulationEvidence(simOut, scenario, context)
%EXTRACTSIMULATIONEVIDENCE Summarize SimulationOutput evidence for CiTT.

if nargin < 3 || isempty(context)
    context = struct();
end

evidence = struct();
evidence.scenario_id = fieldText(scenario, "id");
evidence.output_variables = strings(0, 1);
evidence.logsout_present = false;
evidence.simscape_log_present = false;
evidence.messages = strings(0, 1);
evidence.context_model_path = fieldText(context, "ModelPath");

try
    evidence.output_variables = string(simOut.who);
catch
    evidence.messages(end + 1) = "SimulationOutput variable list was not available.";
end

if any(evidence.output_variables == "logsout")
    evidence.logsout_present = true;
end
if any(startsWith(evidence.output_variables, "simlog"))
    evidence.simscape_log_present = true;
end
end

function text = fieldText(value, name)
text = "";
if isstruct(value) && isfield(value, char(name))
    raw = value.(char(name));
    if isempty(raw)
        text = "";
    elseif isstring(raw)
        text = strjoin(raw(:)', ", ");
    elseif ischar(raw)
        text = string(raw);
    elseif isnumeric(raw) || islogical(raw)
        text = string(raw);
    else
        text = string(feval('citt.util.jsonEncode', raw));
    end
end
end
