function p = benchmark03_educational_params(overrides)
%BENCHMARK03_EDUCATIONAL_PARAMS Educational scaled parameters for benchmark 3.
%
% These values are for CiTT benchmark evidence only. They are not a
% clinically validated axon model or validated neural membrane dataset.

if nargin < 1 || isempty(overrides)
    overrides = struct();
end

p = struct();
p.parameter_set_label = "educational scaled benchmark parameters";
p.parameter_set_warning = "Not a clinically validated axon model.";

p.V_rest = -65e-3;
p.V_cmd_initial = -65e-3;
p.V_cmd_final = -20e-3;
p.command_step_time = 5e-3;
p.R_m = 20e6;
p.C_m = 500e-12;
p.E_leak = -65e-3;
p.R_e = 2e6;
p.R_series_output = 100e3;
p.I_membrane_nonlinear_max = 0.5e-9;
p.V_nonlinear_threshold = -40e-3;
p.V_nonlinear_slope = 6e-3;

p.A_ol = 2e4;
p.amplifier_bandwidth_hz = 2000;
p.output_rails = [-1.0, 1.0];
p.output_current_limit = 5e-9;
p.output_resistance = 50;
p.input_offset = 0;
p.input_noise_rms = 100e-6;

p.T_s = 2e-4;
p.fs = 5000;
p.adc_bits = 12;
p.adc_input_range = [-0.2, 0.2];
p.digital_settled_threshold = 1e-3;
p.digital_settled_hold_time = 2e-3;
p.saturation_voltage_threshold = 0.95;
p.saturation_current_threshold = 4.8e-9;

p.t_stop = 60e-3;
p.max_step = 1e-5;
p.K_ctrl = 1.0;

p.A_ol_values = [1e3, 3e3, 1e4, 3e4, 1e5];
p.R_e_values = [0.2e6, 0.5e6, 1e6, 2e6, 5e6];

p.fault_cases = [
    faultCase("wrong_Cm_10x", "C_m", 5e-9, "slower settling")
    faultCase("low_adc_rate", "T_s", 2e-3, "coarse digital timing / aliasing risk")
    faultCase("high_electrode_resistance", "R_e", 10e6, "larger tracking error / amplifier demand")
    faultCase("low_current_limit", "output_current_limit", 1e-9, "clamp current saturation and slower response")
    faultCase("narrow_rails", "output_rails", [-0.05, 0.05], "amplifier voltage saturation")
    faultCase("unit_mistake_capacitance", "C_m", 500e-9, "unrealistic time constant and failed settling")
];

names = fieldnames(overrides);
for i = 1:numel(names)
    p.(names{i}) = overrides.(names{i});
end

p.adc_lsb = (p.adc_input_range(2) - p.adc_input_range(1)) / 2^p.adc_bits;

% Aliases used by the generated Simulink/Simscape model.
p.V_c_initial = p.V_cmd_initial;
p.V_c = p.V_cmd_final;
p.t_step = p.command_step_time;
p.V_rail_minus = p.output_rails(1);
p.V_rail_plus = p.output_rails(2);
p.I_limit = p.output_current_limit;
p.N_bits = p.adc_bits;
p.V_adc_ref = p.adc_input_range(2) - p.adc_input_range(1);
p.I_leak = -p.E_leak / p.R_m;
p.I_nl = 0;
end

function item = faultCase(id, parameter, value, expectedEffect)
item = struct();
item.id = string(id);
item.parameter = string(parameter);
item.value = value;
item.expected_effect = string(expectedEffect);
end
