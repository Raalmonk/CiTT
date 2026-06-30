# CiTT SATK Agent Report

## Model
- Saved model: `matlab/work/citt_generated_model.slx`
- Construction path: MATLAB MCP/SATK `model_edit` structural edits.
- Local CiTT model-construction helpers were not called.

## Structural Check
- `model_check` status: healthy.
- Checks run: unconnected ports, unconnected lines, Stateflow lint.

## Simulation Readiness
- MATLAB update/compile did not complete because numeric values for symbolic parameters are not yet defined.
- First update diagnostic follows:

```text
Error due to multiple causes.
Caused by:
    Error evaluating parameter 'gain' in 'citt_generated_model/AMP1_Open_Loop_Gain_A_ol'
        Unrecognized function or variable 'A_ol'.
            Variable 'A_ol' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error evaluating parameter 'iLim' in 'citt_generated_model/AMP1_Output_Current_Limit_I_limit'
        Unrecognized function or variable 'I_limit'.
            Variable 'I_limit' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error due to multiple causes.
        Error evaluating parameter 'upper_limit' in 'citt_generated_model/AMP1_Rail_Saturation'
            Unrecognized function or variable 'V_rail_plus'.
                Variable 'V_rail_plus' does not exist.
                Suggested Actions:
                    • Load data from a file into the base workspace. - Fix
                    • Create a new variable. - Fix
        Error evaluating parameter 'lower_limit' in 'citt_generated_model/AMP1_Rail_Saturation'
            Unrecognized function or variable 'V_rail_minus'.
                Variable 'V_rail_minus' does not exist.
                Suggested Actions:
                    • Load data from a file into the base workspace. - Fix
                    • Create a new variable. - Fix
    Error evaluating parameter 'const' in 'citt_generated_model/DIGCTRL_Saturation_High_Flag'
        Unrecognized function or variable 'V_rail_plus'.
            Variable 'V_rail_plus' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error evaluating parameter 'const' in 'citt_generated_model/DIGCTRL_Saturation_Low_Flag'
        Unrecognized function or variable 'V_rail_minus'.
            Variable 'V_rail_minus' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error evaluating parameter 'c' in 'citt_generated_model/MEMBRANE_C_m'
        Unrecognized function or variable 'C_m'.
            Variable 'C_m' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error evaluating parameter 'constant' in 'citt_generated_model/MEMBRANE_I_leak_Command'
        Unrecognized function or variable 'I_leak'.
            Variable 'I_leak' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error evaluating parameter 'R' in 'citt_generated_model/MEMBRANE_R_m_Leak'
        Unrecognized function or variable 'R_m'.
            Variable 'R_m' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
    Error evaluating parameter 'R' in 'citt_generated_model/RELECT_R_e'
        Unrecognized function or variable 'R_e'.
            Variable 'R_e' does not exist.
            Suggested Actions:
                • Load data from a file into the base workspace. - Fix
                • Create a new variable. - Fix
```

- Numeric simulation is intentionally pending because the circuit spec supplied symbolic parameters.
- Preserved symbolic parameters: `t_stop`, `t_step`, `V_c_initial`, `V_c`, `A_ol`, `V_rail_plus`, `V_rail_minus`, `I_limit`, `R_e`, `R_m`, `C_m`, `I_leak`, `I_nl`, `T_s`, `N_bits`, `V_adc_ref`, `K_ctrl`.
## Implemented Components
- VC_STEP: Simulink step plus Simscape controlled voltage source at `n_cmd`.
- AMP1: physical command/feedback sensing, finite open-loop gain `A_ol`, rail saturation, controlled output source, and current limiter `I_limit`.
- RELECT: Simscape resistor `R_e` in the drive path.
- MEMBRANE: Simscape `R_m`, `C_m`, leak current source `I_leak`, and optional nonlinear current hook `I_nl`.
- VM_SENSOR and ICLAMP_SENSOR: physical voltage/current sensors with workspace logs.
- ADC1, DIGCTRL, DAC1: sample/quantize path, symbolic behavioral digital update, flags/state logs, and DAC feedback source at `n_feedback`.

## Output Artifacts
- Focus map: `matlab/work/citt_focus_map.json`
- Probe map: `matlab/work/citt_probe_map.json`

## Notes
- Settling time and overshoot are mapped as derived probes from `citt_vm` and `citt_command_voltage`; they must not be reported until the model runs with numeric parameters.
- Current sign convention follows `ICLAMP_SENSOR_Clamp_Current` orientation from amplifier/current limiter toward `R_e`.
