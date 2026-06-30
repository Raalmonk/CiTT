function messages = ensureStopTimeReady(modelName)
%ENSURESTOPTIMEREADY Make generated timing/gain settings evaluable.

messages = strings(0, 1);
changed = false;
workspace = get_param(char(modelName), "ModelWorkspace");
stopSpec = strtrim(string(get_param(char(modelName), "StopTime")));
defaultStopTime = defaultValueForName(stopSpec, 0.1);
if strlength(stopSpec) == 0
    set_param(char(modelName), string(defaultStopTime));
    messages(end + 1, 1) = "StopTime was empty; set to " + string(defaultStopTime) + " s.";
    changed = true;
    messages = [messages; savePreparedModel(modelName, changed)];
    return
end
if canEvaluateStopTime(modelName, stopSpec)
    [parameterMessages, parameterChanged] = ensureCommonGeneratedParameters(modelName, workspace);
    messages = [messages; parameterMessages];
    messages = [messages; savePreparedModel(modelName, parameterChanged)];
    return
end
if isvarname(char(stopSpec))
    assignin(workspace, char(stopSpec), defaultStopTime);
    messages(end + 1, 1) = "StopTime variable " + stopSpec + " was undefined or non-finite; assigned " + string(defaultStopTime) + " s in the model workspace.";
    changed = true;
else
    set_param(char(modelName), string(defaultStopTime));
    messages(end + 1, 1) = "StopTime expression could not be evaluated; set to " + string(defaultStopTime) + " s.";
    changed = true;
end
[parameterMessages, parameterChanged] = ensureCommonGeneratedParameters(modelName, workspace);
messages = [messages; parameterMessages];
changed = changed || parameterChanged;
messages = [messages; savePreparedModel(modelName, changed)];
end

function [messages, changed] = ensureCommonGeneratedParameters(modelName, workspace)
messages = strings(0, 1);
changed = false;
defaults = {
    "t_step", 0.01, "Step time variable t_step was undefined; assigned 0.01 s in the model workspace."
    "A_clamp_gain", 10, "Clamp gain variable A_clamp_gain was undefined; assigned 10 in the model workspace."
    "citt_stop_time_s", 200, "PK biosensor stop time citt_stop_time_s was undefined or non-finite; assigned 200 s."
    "citt_pk_scale_uM", 10, "PK concentration scale citt_pk_scale_uM was undefined or non-finite; assigned 10 uM."
    "citt_bioavailability", 1, "PK bioavailability citt_bioavailability was undefined or non-finite; assigned 1."
    "citt_ka_per_s", 0.02, "PK absorption rate citt_ka_per_s was undefined or non-finite; assigned 0.02 1/s."
    "citt_ke_per_s", 0.002, "PK elimination rate citt_ke_per_s was undefined or non-finite; assigned 0.002 1/s."
    "citt_adc_vref_hi_V", 3.3, "ADC high reference citt_adc_vref_hi_V was undefined or non-finite; assigned 3.3 V."
    "citt_adc_vref_lo_V", 0, "ADC low reference citt_adc_vref_lo_V was undefined or non-finite; assigned 0 V."
    "citt_vplus_V", 3.3, "Op-amp positive output limit citt_vplus_V was undefined or non-finite; assigned 3.3 V."
    "citt_vminus_V", 0, "Op-amp negative output limit citt_vminus_V was undefined or non-finite; assigned 0 V."
    "citt_opamp_open_loop_gain", 1e5, "Op-amp open-loop gain citt_opamp_open_loop_gain was undefined or non-finite; assigned 1e5."
    "citt_opamp_input_resistance_ohm", 1e9, "Op-amp input resistance citt_opamp_input_resistance_ohm was undefined or non-finite; assigned 1e9 ohm."
    "citt_opamp_output_resistance_ohm", 10, "Op-amp output resistance citt_opamp_output_resistance_ohm was undefined or non-finite; assigned 10 ohm."
    "citt_opamp_pole_frequency_Hz", 1e5, "Op-amp pole frequency citt_opamp_pole_frequency_Hz was undefined or non-finite; assigned 1e5 Hz."
    "citt_opamp_output_offset_V", 0, "Op-amp output offset citt_opamp_output_offset_V was undefined or non-finite; assigned 0 V."
};
for i = 1:size(defaults, 1)
    name = string(defaults{i, 1});
    if ~parameterNeedsDefault(modelName, name)
        continue
    end
    assignin(workspace, char(name), defaults{i, 2});
    messages(end + 1, 1) = defaults{i, 3}; %#ok<AGROW>
    changed = true;
end
end

function value = defaultValueForName(name, defaultValue)
switch string(name)
    case "citt_stop_time_s"
        value = 200;
    otherwise
        value = defaultValue;
end
end

function ok = canEvaluateStopTime(modelName, stopSpec)
ok = false;
try
    value = Simulink.data.evalinGlobal(char(modelName), char(stopSpec));
    ok = isUsableStopValue(value);
    if ok
        return
    end
catch
end
try
    value = evalin("base", char(stopSpec));
    ok = isUsableStopValue(value);
catch
    ok = false;
end
end

function tf = isUsableStopValue(value)
tf = false;
if isnumeric(value)
    tf = ~isempty(value) && all(isfinite(value(:))) && all(value(:) >= 0);
elseif isduration(value)
    tf = all(isfinite(seconds(value(:)))) && all(seconds(value(:)) >= 0);
elseif ischar(value) || isstring(value)
    tf = strlength(strtrim(string(value))) > 0;
end
end

function tf = parameterNeedsDefault(modelName, name)
tf = true;
try
    value = Simulink.data.evalinGlobal(char(modelName), char(name));
catch
    return
end
if isnumeric(value)
    tf = isempty(value) || any(~isfinite(value(:)));
else
    tf = false;
end
end

function messages = savePreparedModel(modelName, changed)
messages = strings(0, 1);
if ~changed
    return
end
try
    save_system(char(modelName));
    messages(end + 1, 1) = "Prepared generated-model parameters saved in the model file.";
catch saveError
    messages(end + 1, 1) = "Prepared generated-model parameters are active in the open model; save failed: " + string(saveError.message);
end
end
