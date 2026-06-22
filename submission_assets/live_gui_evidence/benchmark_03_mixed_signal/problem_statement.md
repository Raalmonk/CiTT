# Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic

Model a closed-loop neural clamp system with membrane capacitance Cm, membrane leakage resistance Rm, optional simplified nonlinear membrane current, electrode series resistance, finite-gain amplifier, output current limit, rail saturation, command voltage step Vc(t), ADC sampling and quantization of Vm, digital comparator or finite-state control logic, DAC or command update path, and requested outputs Vm(t), clamp current, amplifier output, ADC code sequence, digital control state, saturation flags, settling time, and overshoot.

This problem is intentionally too complex for reliable LLM-only closed-form solving. It requires simulation.

## Educational Scaled Benchmark Parameters

Use the following values to make the benchmark executable and visually inspectable. These are **educational scaled benchmark parameters, not a clinically validated axon model**. They are chosen to produce stable transient behavior, visible ADC/digital effects, and clear saturation/fault evidence.

Nominal analog and membrane parameters:

- `V_rest = -65e-3 V`
- `V_cmd_initial = -65e-3 V`
- `V_cmd_final = -20e-3 V`
- `command_step_time = 5e-3 s`
- `R_m = 20e6 ohm`
- `C_m = 500e-12 F`
- `E_leak = -65e-3 V`
- `R_e = 2e6 ohm`
- `R_series_output = 100e3 ohm`
- `I_membrane_nonlinear_max = 0.5e-9 A`
- `V_nonlinear_threshold = -40e-3 V`
- `V_nonlinear_slope = 6e-3 V`

Amplifier and clamp parameters:

- `A_ol = 2e4 V/V`
- `amplifier_bandwidth_hz = 2000`
- `output_rails = [-1.0, 1.0] V`
- `output_current_limit = 5e-9 A`
- `output_resistance = 50 ohm`
- `input_offset = 0 V`
- `input_noise_rms = 100e-6 V` optional

ADC and digital-control parameters:

- `T_s = 2e-4 s`
- `fs = 5000 Hz`
- `adc_bits = 12`
- `adc_input_range = [-0.2, 0.2] V`
- `adc_lsb = (0.2 - (-0.2)) / 2^12`
- `digital_settled_threshold = 1e-3 V`
- `digital_settled_hold_time = 2e-3 s`
- `saturation_voltage_threshold = 0.95 V`
- `saturation_current_threshold = 4.8e-9 A`

Simulation parameters:

- `t_stop = 60e-3 s`
- `max_step = 1e-5 s`
- Plot `Vm` and command in mV, clamp current in nA, amplifier output in V, ADC code as integer, and digital state as integer.

Parameter sweep:

- `A_ol_values = [1e3, 3e3, 1e4, 3e4, 1e5]`
- `R_e_values = [0.2e6, 0.5e6, 1e6, 2e6, 5e6]`
- Metric: final tracking error in mV and saturation duration in ms.

Fault injection cases:

1. `wrong_Cm_10x`: set `C_m = 5e-9 F`; expected effect is slower settling.
2. `low_adc_rate`: set `T_s = 2e-3 s`, `fs = 500 Hz`; expected effect is coarse digital timing and aliasing risk.
3. `high_electrode_resistance`: set `R_e = 10e6 ohm`; expected effect is larger tracking error and amplifier demand.
4. `low_current_limit`: set `output_current_limit = 1e-9 A`; expected effect is clamp current saturation and slower response.
5. `narrow_rails`: set `output_rails = [-0.05, 0.05] V`; expected effect is amplifier voltage saturation.
6. `unit_mistake_capacitance`: set `C_m = 500e-9 F`; expected effect is an unrealistic time constant and failed settling.

Required generated plots:

- `mixed_signal_full_timeline.png`
- `membrane_voltage_and_clamp_current.png`
- `amplifier_saturation.png`
- `adc_codes_and_digital_logic.png`
- `digital_state_machine_trace.png`
- `parameter_sweep_heatmap.png`
- `fault_injection_summary.png`
