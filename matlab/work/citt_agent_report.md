# CiTT Simscape Model Agent Report

## Outputs
- Model: `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_generated_model.slx`
- Focus map: `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_focus_map.json`
- Probe map: `/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_probe_map.json`

## Build Summary
- Built a Simscape-first biosensor/TIA front-end model using SATK `model_edit` structural operations.
- Physical electrical network includes a controlled faradaic current source, current sensor, band-limited op amp, RF/CF feedback network, DC reference source, electrical reference, solver configuration, and TIA output voltage sensor.
- Simulink-side stimulus/probe chain includes the one-compartment oral PK source expression, first-order membrane lag, concentration-to-current gain, ADC range saturation/scaling/quantization, and workspace probes for all requested outputs.
- No recognized real op-amp part number was present in the spec. The TIA uses the Simscape Electrical Band-Limited Op-Amp block with named parameters for gain, input/output resistance, pole frequency, output offset, and output voltage limits.
- The selected op-amp block does not expose physical supply pins. The VSUP ambiguity is preserved through named output-limit parameters `citt_vplus_V` and `citt_vminus_V` instead of silently inventing rail values.

## Checks
- Final SATK `model_check` on root scope: `status: healthy`.
- Checks run: `unconnected_ports`, `unconnected_lines`, `stateflow_lint`.
- JSON artifact validation: focus map contains 10 items and probe map contains 6 items with the required contract fields.
- `model_resolve_params` was attempted for key named parameters, but it requested model compilation and failed because omitted spec values are intentionally retained as `NaN` named parameters. This is recorded as an unresolved input issue, not replaced with invented numeric values.

## Specified Named Parameters
- `citt_tau_m_s = 4`
- `citt_sensor_sensitivity_A_per_uM = 25e-9`
- `citt_Rf_ohm = 1e6`
- `citt_Cf_F = 1e-8`
- `citt_Vref_V = 0`
- `citt_adc_bits = 12`
- `citt_stop_time_s = 200` simulation-control default

## Unresolved Named Inputs Preserved From Spec Ambiguities
- PK source parameters: `citt_pk_scale_uM`, `citt_bioavailability`, `citt_ka_per_s`, `citt_ke_per_s`
- ADC range parameters: `citt_adc_vref_hi_V`, `citt_adc_vref_lo_V`
- Op-amp/supply parameters: `citt_vplus_V`, `citt_vminus_V`, `citt_opamp_open_loop_gain`, `citt_opamp_input_resistance_ohm`, `citt_opamp_output_resistance_ohm`, `citt_opamp_pole_frequency_Hz`, `citt_opamp_output_offset_V`

## Probe Coverage
- Concentration `C(t)` via `probe_concentration_C_uM`.
- Lagged concentration via `probe_lagged_concentration_uM`.
- Sensor current via Simscape Current Sensor and `probe_sensor_current_A`.
- TIA output voltage via Simscape Voltage Sensor and `probe_tia_output_V`.
- ADC code via `probe_adc_code`.
- Settling error via `probe_settling_error_V`.

## Remaining Issues
- A numerical transient simulation requires user-supplied values for the unresolved PK, ADC reference, op-amp, and supply parameters listed above.
- The current-source polarity follows the structured spec: `I_SENSOR.p/head` injects through the current sensor into the TIA summing node and `I_SENSOR.n/tail` returns to the reference node.
