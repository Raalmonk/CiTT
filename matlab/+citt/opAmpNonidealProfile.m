function profiles = opAmpNonidealProfile(inputValue)
%OPAMPNONIDEALPROFILE Return known op-amp nonideal parameter profiles.

if nargin < 1
    inputValue = "";
end

profiles = repmat(baseProfile(), 0, 1);
text = lower(valueToText(inputValue));
text = replace(text, "µ", "u");

if containsAny(text, ["lm741", "ua741", "u741", "741 op", "741 operational"])
    profiles = lm741Profile();
end
end

function profile = baseProfile()
profile = struct();
profile.part_number = "";
profile.aliases = strings(0, 1);
profile.source = "";
profile.source_url = "";
profile.modeling_priority = strings(0, 1);
profile.input_bias_current_typ_A = [];
profile.input_bias_current_max_25c_A = [];
profile.input_bias_current_max_full_temp_A = [];
profile.input_offset_current_typ_A = [];
profile.input_offset_current_max_A = [];
profile.input_offset_voltage_typ_V = [];
profile.input_offset_voltage_max_25c_V = [];
profile.input_offset_voltage_max_full_temp_V = [];
profile.input_resistance_typ_ohm = [];
profile.input_resistance_min_ohm = [];
profile.large_signal_gain_typ_V_per_V = [];
profile.slew_rate_typ_V_per_s = [];
profile.unity_gain_bandwidth_typ_Hz = [];
profile.output_swing_typ_V_at_pm15V_RL10k = [];
profile.notes = strings(0, 1);
end

function profile = lm741Profile()
profile = baseProfile();
profile.part_number = "LM741";
profile.aliases = ["LM741"; "UA741"; "uA741"; "muA741"; "741"];
profile.source = "Texas Instruments LM741 Operational Amplifier datasheet";
profile.source_url = "https://www.ti.com/lit/ds/symlink/lm741.pdf";
profile.modeling_priority = [
    "Do not model LM741 inputs as ideal infinite-impedance nodes when lab error matters."
    "Represent input bias current at both op-amp inputs with DC current sources."
    "Represent input offset voltage as a small differential input voltage source."
    "Represent finite input resistance, finite open-loop gain, output swing limits, and slew-rate/bandwidth if transient behavior is relevant."
];

profile.input_bias_current_typ_A = 80e-9;
profile.input_bias_current_max_25c_A = 500e-9;
profile.input_bias_current_max_full_temp_A = 1.5e-6;
profile.input_offset_current_typ_A = 20e-9;
profile.input_offset_current_max_A = 200e-9;
profile.input_offset_voltage_typ_V = 1e-3;
profile.input_offset_voltage_max_25c_V = 5e-3;
profile.input_offset_voltage_max_full_temp_V = 6e-3;
profile.input_resistance_typ_ohm = 2e6;
profile.input_resistance_min_ohm = 0.3e6;
profile.large_signal_gain_typ_V_per_V = 200e3;
profile.slew_rate_typ_V_per_s = 0.5e6;
profile.unity_gain_bandwidth_typ_Hz = 1e6;
profile.output_swing_typ_V_at_pm15V_RL10k = 14;
profile.notes = [
    "Bias-current voltage error at a high-impedance source is approximately V_error = I_bias * R_source."
    "For a voltage follower, LM741 input bias current can corrupt the measured node even when an ideal op-amp model predicts no loading."
    "The values are typical/default modeling values; use a concrete datasheet grade and temperature range when grading hardware data."
];
end

function tf = containsAny(text, patterns)
tf = any(contains(string(text), string(patterns), "IgnoreCase", true));
end

function text = valueToText(value)
if isempty(value)
    text = "";
elseif ischar(value) || isstring(value)
    text = strjoin(string(value(:))', " ");
elseif isnumeric(value) || islogical(value)
    text = string(mat2str(value));
elseif iscell(value)
    parts = strings(numel(value), 1);
    for i = 1:numel(value)
        parts(i) = valueToText(value{i});
    end
    text = strjoin(parts(:)', " ");
elseif isstruct(value)
    text = string(feval('citt.util.jsonEncode', value));
else
    text = string(value);
end
end
