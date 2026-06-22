# CiTT SATK Agent Task: Two-Electrode Voltage Clamp Equivalent Circuit

    Build a Simscape/Simulink teaching model for `tevc_equilibrium_feedback` using the structured spec in `citt_spec.json`.

    Required focus points:
    - feedback_loop
- membrane_node
- finite_gain_error
- electrode_resistance_assumption

    Required probes:
    - Vm
- amplifier output
- clamp current

    After model generation, open the model visibly in Simulink and print this exact pause:

    ```text
    PAUSE FOR MANUAL SIMSCAPE ARRANGEMENT

    Please manually drag, reposition, and clean up the Simscape/Simulink blocks now.
    Arrange the model so screenshots clearly show:
    - signal flow,
    - feedback loops,
    - probes,
    - sensors,
    - ADC / digital logic,
    - important Simscape physical components,
    - source, reference, solver configuration, and output paths.

    When done, save the model and press Enter in the MATLAB command window to continue.
    ```

    Then wait with:

    ```matlab
    input("Arrange the Simscape model, save it, then press Enter to continue: ", "s");
    ```

    Capture the model screenshot only after the pause. If MATLAB is headless or SATK/Simscape is unavailable, record `manual_arrangement = "skipped-headless"` in `citt_run_notes.md` and continue with offline plots and report generation.
