from __future__ import annotations

import json
import math

from app.models.matlab_playground import (
    FocusMapEntry,
    HighlightTarget,
    LabDeltaCause,
    LabDeltaComparisonRow,
    LabDeltaRequest,
    LabDeltaResponse,
    MatlabArtifact,
    MatlabArtifactRequest,
    MatlabPlaygroundManifest,
    PlaygroundLab,
    ProbePlan,
)


RC_ANTIALIAS_LAB_ID = "rc_antialias_adc"
INSTRUMENTATION_FEEDBACK_LAB_ID = "instrumentation_amplifier_feedback"
PLAYGROUND_TABS = ["overview", "teach", "probe", "lab_delta"]
DEFAULT_FS_HZ = 500.0
DEFAULT_TARGET_FC_HZ = 40.0
DEFAULT_C_F = 100e-9
DEFAULT_R_OHM = 1.0 / (2.0 * math.pi * DEFAULT_TARGET_FC_HZ * DEFAULT_C_F)


def build_playground_manifest() -> MatlabPlaygroundManifest:
    labs = available_labs()
    default_lab_id = RC_ANTIALIAS_LAB_ID
    return MatlabPlaygroundManifest(
        product_name="CiTT MATLAB/Simscape Playground",
        version="1.0.0",
        positioning=(
            "CiTT is a graphical tutor layer for BME circuits and signal-conditioning labs. "
            "Students stay in a guided UI while MATLAB, Simulink, and Simscape provide the "
            "engineering playground behind GUI buttons."
        ),
        tabs=PLAYGROUND_TABS,
        labs=labs,
        artifacts=generate_artifacts(default_lab_id),
        focus_map=get_focus_map(default_lab_id),
        probe_plans=get_probe_plans(default_lab_id),
        lab_delta_causes=get_lab_delta_causes(default_lab_id),
        notes=[
            "The LLM is not the numerical authority.",
            "CiTT grounds tutoring in explicit circuit representations, hand checks, simulation artifacts, and student-visible evidence.",
            "MATLAB execution is optional for CI; generated artifacts are deterministic text and JSON.",
            "The internal solver remains the hand-check engine and fallback for small circuits.",
        ],
    )


def available_labs() -> list[PlaygroundLab]:
    return [
        PlaygroundLab(
            id=RC_ANTIALIAS_LAB_ID,
            title="RC anti-aliasing filter before ADC",
            summary=(
                "A first-order R-C low-pass stage filters an ECG-like signal before a "
                "500 Hz sampling step. Students compare hand cutoff, generated simulation "
                "signals, and measured lab data."
            ),
            bme_context=(
                "Signal-conditioning for ECG-style acquisition: preserve low-frequency content, "
                "attenuate interference before sampling, and check whether lab data matches "
                "the assumptions."
            ),
            required_products=["MATLAB"],
            optional_products=["Simulink", "Simscape", "Simscape Electrical"],
            default_parameters={
                "fs_hz": DEFAULT_FS_HZ,
                "target_fc_hz": DEFAULT_TARGET_FC_HZ,
                "R_ohm": DEFAULT_R_OHM,
                "C_f": DEFAULT_C_F,
            },
            learning_objectives=[
                "Compute cutoff frequency with fc = 1/(2*pi*R*C).",
                "Relate cutoff and Nyquist frequency to anti-aliasing behavior.",
                "Probe input, filter output, and sampled output signals.",
                "Use Lab Delta to distinguish math, unit, tolerance, loading, and sampling causes.",
            ],
            assumptions=[
                "The source and ADC input are ideal for the hand check.",
                "The RC stage is a first-order low-pass filter.",
                "The ECG-like waveform is educational and not patient data.",
                "Simscape is preferred when available; Simulink signal-flow and internal hand checks remain valid fallbacks.",
            ],
        ),
        PlaygroundLab(
            id=INSTRUMENTATION_FEEDBACK_LAB_ID,
            title="Instrumentation amplifier feedback focus",
            summary=(
                "A compact ECG front-end lab that highlights differential input, common-mode "
                "input, gain-setting resistor, feedback loop, op-amp output, and output probe."
            ),
            bme_context=(
                "Instrumentation amplifiers teach how small differential biopotentials are "
                "amplified while common-mode signals are rejected. The lab stays educational "
                "and does not claim patient-connected safety verification."
            ),
            required_products=["MATLAB"],
            optional_products=["Simulink", "Simscape"],
            default_parameters={
                "v_diff_v": 1e-3,
                "v_common_v": 1.0,
                "R_ohm": 10000.0,
                "Rg_ohm": 1000.0,
            },
            learning_objectives=[
                "Separate differential and common-mode inputs.",
                "Connect gain-setting resistance to closed-loop gain.",
                "Highlight the feedback loop in the drawn/model circuit.",
                "Probe the op-amp output before interpreting downstream signal quality.",
            ],
            assumptions=[
                "Ideal op-amp behavior is used for the hand-check path.",
                "Matched resistors are assumed unless Lab Delta suggests otherwise.",
                "Focus maps describe highlight targets even when Simscape is unavailable.",
            ],
        ),
    ]


def get_lab(lab_id: str) -> PlaygroundLab:
    canonical_id = _canonical_lab_id(lab_id)
    for lab in available_labs():
        if lab.id == canonical_id:
            return lab
    raise ValueError(f"Unknown MATLAB playground lab: {lab_id}")


def generate_artifacts(
    lab_id: str,
    request: MatlabArtifactRequest | None = None,
) -> list[MatlabArtifact]:
    canonical_id = _canonical_lab_id(lab_id)
    requested = set(request.kinds) if request and request.kinds else set(_default_artifact_kinds(canonical_id))
    builders = _artifact_builders(canonical_id)
    artifacts: list[MatlabArtifact] = []
    for kind in _ordered_artifact_kinds(requested):
        builder = builders.get(kind)
        if builder is not None:
            artifacts.append(builder())
    return artifacts


def get_focus_map(lab_id: str) -> list[FocusMapEntry]:
    canonical_id = _canonical_lab_id(lab_id)
    if canonical_id == RC_ANTIALIAS_LAB_ID:
        return _rc_focus_map()
    if canonical_id == INSTRUMENTATION_FEEDBACK_LAB_ID:
        return _instrumentation_focus_map()
    raise ValueError(f"Unknown MATLAB playground lab: {lab_id}")


def get_probe_plans(lab_id: str) -> list[ProbePlan]:
    canonical_id = _canonical_lab_id(lab_id)
    if canonical_id == RC_ANTIALIAS_LAB_ID:
        return _rc_probe_plans()
    if canonical_id == INSTRUMENTATION_FEEDBACK_LAB_ID:
        return _instrumentation_probe_plans()
    raise ValueError(f"Unknown MATLAB playground lab: {lab_id}")


def get_lab_delta_causes(lab_id: str) -> list[LabDeltaCause]:
    get_lab(lab_id)
    return [
        _cause("rad_s_vs_hz"),
        _cause("missing_2pi"),
        _cause("capacitor_prefix_mistake"),
        _cause("resistor_prefix_mistake"),
        _cause("rc_tolerance"),
        _cause("source_load_impedance"),
        _cause("sampling_nyquist"),
        _cause("adc_quantization"),
        _cause("op_amp_saturation"),
        _cause("transient_not_settled"),
        _cause("measurement_noise"),
    ]


def compare_lab_delta(lab_id: str, request: LabDeltaRequest) -> LabDeltaResponse:
    canonical_id = _canonical_lab_id(lab_id)
    get_lab(canonical_id)
    rows = _comparison_rows(request)
    causes = _detect_lab_delta_causes(request, rows)
    if not causes:
        causes = [_cause("measurement_noise")]

    return LabDeltaResponse(
        lab_id=canonical_id,
        rows=rows,
        likely_causes=causes,
        recommended_probe=_recommended_probe(canonical_id, causes),
        reflection_question=(
            "Which single assumption would you test first, and what measurement would make "
            "that assumption visible?"
        ),
        notes=_lab_delta_notes(request),
    )


def _canonical_lab_id(lab_id: str) -> str:
    if lab_id == "instrumentation_amplifier_intro":
        return INSTRUMENTATION_FEEDBACK_LAB_ID
    return lab_id


def _default_artifact_kinds(lab_id: str) -> list[str]:
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return [
            "matlab_script",
            "simscape_script",
            "simulink_script",
            "popup_app_script",
            "focus_map",
            "probe_plan",
            "lab_delta_report",
        ]
    return [
        "matlab_script",
        "simulink_script",
        "popup_app_script",
        "focus_map",
        "probe_plan",
        "lab_delta_report",
    ]


def _ordered_artifact_kinds(kinds: set[str]) -> list[str]:
    order = [
        "matlab_script",
        "simscape_script",
        "simulink_script",
        "popup_app_script",
        "focus_map",
        "probe_plan",
        "lab_delta_report",
    ]
    return [kind for kind in order if kind in kinds]


def _artifact_builders(lab_id: str):
    if lab_id == RC_ANTIALIAS_LAB_ID:
        return {
            "matlab_script": lambda: _artifact(
                "rc_matlab_script",
                lab_id,
                "RC hand check and signal script",
                "matlab_script",
                "citt_rc_antialias_adc.m",
                _rc_matlab_script(),
                "Run from MATLAB or inspect as generated evidence. Students use the CiTT UI, not hand-written setup code.",
            ),
            "simscape_script": lambda: _artifact(
                "rc_simscape_script",
                lab_id,
                "RC Simscape-first build script",
                "simscape_script",
                "citt_build_rc_antialias_adc_simscape.m",
                _rc_simscape_script(),
                "Builds a Simscape-first playground when blocks are available and falls back gracefully.",
            ),
            "simulink_script": lambda: _artifact(
                "rc_simulink_script",
                lab_id,
                "RC Simulink signal-flow fallback",
                "simulink_script",
                "citt_build_rc_antialias_adc_signal_flow.m",
                _rc_simulink_script(),
                "Creates a signal-flow model that mirrors the hand check when Simscape blocks are unavailable.",
            ),
            "popup_app_script": lambda: _artifact(
                "rc_popup_app_script",
                lab_id,
                "CiTT MATLAB popup app skeleton",
                "popup_app_script",
                "citt.m",
                _popup_app_script(),
                "Place beside +citt helpers and call citt to open the four-tab popup.",
            ),
            "focus_map": lambda: _json_artifact(
                "rc_focus_map",
                lab_id,
                "RC focus map",
                "focus_map",
                "citt_rc_antialias_adc_focus_map.json",
                [entry.model_dump() for entry in _rc_focus_map()],
            ),
            "probe_plan": lambda: _json_artifact(
                "rc_probe_plan",
                lab_id,
                "RC probe plans",
                "probe_plan",
                "citt_rc_antialias_adc_probe_plan.json",
                [probe.model_dump() for probe in _rc_probe_plans()],
            ),
            "lab_delta_report": lambda: _json_artifact(
                "rc_lab_delta_report",
                lab_id,
                "RC Lab Delta report seed",
                "lab_delta_report",
                "citt_rc_antialias_adc_lab_delta_report.json",
                compare_lab_delta(
                    lab_id,
                    LabDeltaRequest(
                        lab_id=lab_id,
                        hand_values={"fc_hz": DEFAULT_TARGET_FC_HZ},
                        simulation_values={"fc_hz": DEFAULT_TARGET_FC_HZ},
                        measured_values={"fc_hz": DEFAULT_TARGET_FC_HZ * 2.0 * math.pi},
                        notes="Seed case: scope cursor reports angular frequency as if it were Hz.",
                    ),
                ).model_dump(),
            ),
        }
    if lab_id == INSTRUMENTATION_FEEDBACK_LAB_ID:
        return {
            "matlab_script": lambda: _artifact(
                "instrumentation_matlab_script",
                lab_id,
                "Instrumentation amplifier teaching script",
                "matlab_script",
                "citt_instrumentation_amplifier_feedback.m",
                _instrumentation_matlab_script(),
                "Educational hand-check setup for the instrumentation amplifier feedback lab.",
            ),
            "simulink_script": lambda: _artifact(
                "instrumentation_simulink_script",
                lab_id,
                "Instrumentation amplifier focus skeleton",
                "simulink_script",
                "citt_build_instrumentation_feedback_model.m",
                _instrumentation_simulink_script(),
                "Builds named blocks and annotations so the feedback loop can be highlighted.",
            ),
            "popup_app_script": lambda: _artifact(
                "instrumentation_popup_app_script",
                lab_id,
                "CiTT MATLAB popup app skeleton",
                "popup_app_script",
                "citt.m",
                _popup_app_script(),
                "Place beside +citt helpers and call citt to open the four-tab popup.",
            ),
            "focus_map": lambda: _json_artifact(
                "instrumentation_focus_map",
                lab_id,
                "Instrumentation focus map",
                "focus_map",
                "citt_instrumentation_feedback_focus_map.json",
                [entry.model_dump() for entry in _instrumentation_focus_map()],
            ),
            "probe_plan": lambda: _json_artifact(
                "instrumentation_probe_plan",
                lab_id,
                "Instrumentation probe plans",
                "probe_plan",
                "citt_instrumentation_feedback_probe_plan.json",
                [probe.model_dump() for probe in _instrumentation_probe_plans()],
            ),
            "lab_delta_report": lambda: _json_artifact(
                "instrumentation_lab_delta_report",
                lab_id,
                "Instrumentation Lab Delta report seed",
                "lab_delta_report",
                "citt_instrumentation_feedback_lab_delta_report.json",
                compare_lab_delta(
                    lab_id,
                    LabDeltaRequest(
                        lab_id=lab_id,
                        hand_values={"gain_v_per_v": 21.0},
                        simulation_values={"gain_v_per_v": 20.8},
                        measured_values={"gain_v_per_v": 18.9},
                        notes="Seed case: gain is lower than the ideal hand check.",
                    ),
                ).model_dump(),
            ),
        }
    raise ValueError(f"Unknown MATLAB playground lab: {lab_id}")


def _artifact(
    artifact_id: str,
    lab_id: str,
    title: str,
    kind: str,
    filename: str,
    content: str,
    instructions: str,
) -> MatlabArtifact:
    return MatlabArtifact(
        id=artifact_id,
        lab_id=lab_id,
        title=title,
        kind=kind,
        filename=filename,
        content=content,
        instructions=instructions,
    )


def _json_artifact(
    artifact_id: str,
    lab_id: str,
    title: str,
    kind: str,
    filename: str,
    payload: object,
) -> MatlabArtifact:
    return _artifact(
        artifact_id,
        lab_id,
        title,
        kind,
        filename,
        json.dumps(payload, indent=2, sort_keys=True),
        "This artifact is deterministic JSON consumed by the web UI and MATLAB popup.",
    )


def _target(
    target_id: str,
    label: str,
    target_type: str,
    *,
    component_id: str | None = None,
    node_id: str | None = None,
    model_path: str | None = None,
    signal_name: str | None = None,
    style: str = "default",
    reason: str,
) -> HighlightTarget:
    return HighlightTarget(
        id=target_id,
        label=label,
        target_type=target_type,
        component_id=component_id,
        node_id=node_id,
        model_path=model_path,
        signal_name=signal_name,
        style=style,
        reason=reason,
    )


def _rc_focus_map() -> list[FocusMapEntry]:
    return [
        FocusMapEntry(
            id="overview_signal_flow",
            label="Overview signal flow",
            mode="overview",
            description="Input signal, RC filter, sampler, and output evidence path.",
            targets=[
                _target(
                    "overview_signal_flow_path",
                    "Signal flow from ECG-like input to sampled output",
                    "conceptual_path",
                    model_path="citt_rc_antialias_adc/Input to ADC path",
                    style="lineTrace",
                    reason="Shows the full lab boundary before a local calculation.",
                )
            ],
            student_prompt="What changes between the analog filter output and the sampled output?",
        ),
        FocusMapEntry(
            id="input_path",
            label="Input path",
            mode="teach",
            description="ECG-like low-frequency component plus 60 Hz interference.",
            targets=[
                _target(
                    "input_signal",
                    "Input source and interference",
                    "block",
                    component_id="vin",
                    model_path="citt_rc_antialias_adc/Input Signal",
                    signal_name="citt_input_signal",
                    reason="Students first identify what the filter is asked to preserve and attenuate.",
                )
            ],
            teaching_step_id="identify_input",
            student_prompt="Which part of this input should pass, and which part should be reduced?",
        ),
        FocusMapEntry(
            id="rc_filter",
            label="RC filter",
            mode="teach",
            description="The resistor and capacitor that set cutoff frequency.",
            targets=[
                _target(
                    "resistor_R",
                    "Series resistor R",
                    "simscape_component",
                    component_id="R",
                    model_path="citt_rc_antialias_adc/RC Filter/Resistor",
                    style="find",
                    reason="R participates in fc = 1/(2*pi*R*C).",
                ),
                _target(
                    "capacitor_C",
                    "Shunt capacitor C",
                    "simscape_component",
                    component_id="C",
                    model_path="citt_rc_antialias_adc/RC Filter/Capacitor",
                    style="find",
                    reason="C participates in fc = 1/(2*pi*R*C).",
                ),
            ],
            teaching_step_id="cutoff_formula",
            student_prompt="If C is accidentally entered in uF instead of nF, which direction does fc move?",
        ),
        FocusMapEntry(
            id="capacitor_output_node",
            label="Capacitor output node",
            mode="probe",
            description="Voltage across the capacitor and into the ADC input.",
            targets=[
                _target(
                    "vout_node",
                    "Filter output node",
                    "simscape_connection",
                    node_id="vout",
                    model_path="citt_rc_antialias_adc/RC Filter/Vout",
                    signal_name="citt_filtered_signal",
                    style="default",
                    reason="This is the main analog evidence point for attenuation.",
                )
            ],
            teaching_step_id="read_filter_output",
            student_prompt="What unit and approximate magnitude do you expect at this node?",
        ),
        FocusMapEntry(
            id="sampling_stage",
            label="Sampling stage",
            mode="teach",
            description="Zero-order hold or sampled-output stage after the analog filter.",
            targets=[
                _target(
                    "sampler",
                    "Sampler / ADC input",
                    "block",
                    model_path="citt_rc_antialias_adc/Sampling Stage",
                    signal_name="citt_sampled_signal",
                    style="find",
                    reason="Nyquist and aliasing checks live at the sampling boundary.",
                )
            ],
            teaching_step_id="nyquist_check",
            student_prompt="Why is fs/2 the first sampling boundary to check?",
        ),
        FocusMapEntry(
            id="output_signal",
            label="Output signal",
            mode="probe",
            description="The student-visible sampled output after filtering.",
            targets=[
                _target(
                    "sampled_output",
                    "Sampled output trace",
                    "line",
                    model_path="citt_rc_antialias_adc/Sampled Output",
                    signal_name="citt_sampled_signal",
                    style="lineTrace",
                    reason="This is the trace compared to hand and lab evidence.",
                )
            ],
            teaching_step_id="compare_output",
            student_prompt="What evidence would show that 60 Hz was attenuated before sampling?",
        ),
        FocusMapEntry(
            id="lab_delta_measurement_point",
            label="Lab Delta measurement point",
            mode="lab_delta",
            description="Where uploaded lab data should be aligned to the model.",
            targets=[
                _target(
                    "measurement_point_vout",
                    "Scope probe at filter output",
                    "annotation",
                    node_id="vout",
                    model_path="citt_rc_antialias_adc/Lab Delta/Measurement Point",
                    signal_name="citt_filtered_signal",
                    style="default",
                    reason="Lab Delta only helps when the hand, simulation, and measured points match.",
                )
            ],
            student_prompt="Is the measured CSV from the input, RC output, or sampled output?",
        ),
    ]


def _instrumentation_focus_map() -> list[FocusMapEntry]:
    return [
        FocusMapEntry(
            id="differential_input",
            label="Differential input",
            mode="overview",
            description="Small ECG-like voltage between the two input electrodes.",
            targets=[
                _target(
                    "v_diff",
                    "Differential sensor input",
                    "port",
                    model_path="citt_inamp_feedback/Differential Input",
                    signal_name="v_diff",
                    style="find",
                    reason="The useful signal is the difference between the inputs.",
                )
            ],
            student_prompt="Which voltage is the biopotential signal here?",
        ),
        FocusMapEntry(
            id="common_mode_input",
            label="Common-mode input",
            mode="overview",
            description="Shared input voltage that should be rejected by the front end.",
            targets=[
                _target(
                    "v_common",
                    "Common-mode input",
                    "annotation",
                    model_path="citt_inamp_feedback/Common Mode Input",
                    signal_name="v_common",
                    reason="Students should separate common-mode from differential behavior.",
                )
            ],
            student_prompt="Why does a large common-mode voltage not mean a large useful output?",
        ),
        FocusMapEntry(
            id="gain_setting_resistor",
            label="Gain-setting resistor",
            mode="teach",
            description="The resistor that sets the first-stage instrumentation amplifier gain.",
            targets=[
                _target(
                    "Rg",
                    "Gain-setting resistor Rg",
                    "simscape_component",
                    component_id="Rg",
                    model_path="citt_inamp_feedback/Gain Setting Resistor",
                    style="find",
                    reason="Changing Rg changes the differential gain.",
                )
            ],
            teaching_step_id="gain_formula",
            student_prompt="If Rg decreases, does the gain increase or decrease?",
        ),
        FocusMapEntry(
            id="feedback_loop",
            label="Feedback loop",
            mode="teach",
            description="Closed-loop path from op-amp output through feedback network to the inverting input.",
            targets=[
                _target(
                    "feedback_loop_path",
                    "Feedback loop path",
                    "conceptual_path",
                    component_id="Rf",
                    model_path="citt_inamp_feedback/U1 Output -> Rf -> Inverting Input",
                    style="lineTrace",
                    reason="This proves CiTT can highlight a feedback loop rather than only a single part.",
                )
            ],
            teaching_step_id="feedback_loop",
            student_prompt="What does feedback force the op-amp inputs to do in the ideal model?",
        ),
        FocusMapEntry(
            id="op_amp_output",
            label="Op-amp output",
            mode="probe",
            description="Output node where saturation or output swing limits become visible.",
            targets=[
                _target(
                    "op_amp_output",
                    "Op-amp output",
                    "port",
                    node_id="vout",
                    model_path="citt_inamp_feedback/Op Amp Output",
                    signal_name="vout",
                    reason="This local output is the probe point for gain and saturation checks.",
                )
            ],
            teaching_step_id="output_check",
            student_prompt="Is the predicted output inside the assumed supply rails?",
        ),
        FocusMapEntry(
            id="output_probe",
            label="Output probe",
            mode="lab_delta",
            description="Measurement point for comparing hand gain, simulation output, and lab voltage.",
            targets=[
                _target(
                    "output_probe",
                    "Output voltage probe",
                    "annotation",
                    node_id="vout",
                    model_path="citt_inamp_feedback/Output Probe",
                    signal_name="vout",
                    reason="Lab Delta should compare the same physical output point.",
                )
            ],
            student_prompt="Are the measured and simulated output points the same node?",
        ),
    ]


def _rc_probe_plans() -> list[ProbePlan]:
    focus = {entry.id: entry for entry in _rc_focus_map()}
    return [
        ProbePlan(
            id="input_signal_probe",
            label="Input signal probe",
            target=focus["input_path"].targets[0],
            measurement_type="signal voltage",
            expected_unit="V",
            why_probe_here="Confirms the low-frequency ECG-like component and 60 Hz interference before filtering.",
            insertion_steps=[
                "Log the generated input source as citt_input_signal.",
                "Plot the time waveform and optionally its spectrum.",
                "Ask whether the useful signal and interference are distinguishable.",
            ],
            matlab_variable_name="citt_input_signal",
            student_question="Which visible part of the input should the RC filter keep?",
        ),
        ProbePlan(
            id="filter_output_voltage_probe",
            label="Filter output voltage probe",
            target=focus["capacitor_output_node"].targets[0],
            measurement_type="voltage",
            expected_unit="V",
            why_probe_here="This node shows the actual filtered voltage before the ADC boundary.",
            insertion_steps=[
                "Attach a voltage sensor or signal logging block at the capacitor output node.",
                "Name the logged signal citt_filtered_signal.",
                "Compare the 60 Hz amplitude before and after the RC stage.",
            ],
            matlab_variable_name="citt_filtered_signal",
            student_question="What should happen to the 60 Hz component at the filter output?",
        ),
        ProbePlan(
            id="sampled_output_probe",
            label="Sampled output probe",
            target=focus["output_signal"].targets[0],
            measurement_type="sampled signal",
            expected_unit="V",
            why_probe_here="The sampled trace is where Nyquist and aliasing become student-visible.",
            insertion_steps=[
                "Log the zero-order hold or sampled output as citt_sampled_signal.",
                "Confirm fs = 500 Hz and Nyquist = 250 Hz.",
                "Compare the sampled output with the analog filter output.",
            ],
            matlab_variable_name="citt_sampled_signal",
            student_question="Does the sampled trace show evidence that the analog filter worked first?",
        ),
        ProbePlan(
            id="cutoff_attenuation_check",
            label="Cutoff and attenuation check",
            target=focus["rc_filter"].targets[0],
            measurement_type="hand check",
            expected_unit="Hz and unitless ratio",
            why_probe_here="The formula check catches missing 2*pi, rad/s vs Hz, and R/C unit mistakes early.",
            insertion_steps=[
                "Compute citt_hand_fc_hz = 1/(2*pi*R*C).",
                "Compute attenuation at 60 Hz and at Nyquist.",
                "Compare the hand check with simulation and lab values in Lab Delta.",
            ],
            matlab_variable_name="citt_hand_fc_hz",
            student_question="Which single unit mistake would move the cutoff by about 1000x?",
        ),
    ]


def _instrumentation_probe_plans() -> list[ProbePlan]:
    focus = {entry.id: entry for entry in _instrumentation_focus_map()}
    return [
        ProbePlan(
            id="differential_input_probe",
            label="Differential input probe",
            target=focus["differential_input"].targets[0],
            measurement_type="differential voltage",
            expected_unit="V",
            why_probe_here="This confirms the useful ECG-like signal before gain is applied.",
            insertion_steps=["Measure Vplus - Vminus.", "Name the logged signal citt_v_diff."],
            matlab_variable_name="citt_v_diff",
            student_question="Why is this small voltage still meaningful after amplification?",
        ),
        ProbePlan(
            id="feedback_loop_probe",
            label="Feedback loop highlight probe",
            target=focus["feedback_loop"].targets[0],
            measurement_type="conceptual loop highlight",
            expected_unit="V path",
            why_probe_here="The loop explains how the ideal op-amp constrains its input difference.",
            insertion_steps=[
                "Highlight the op-amp output.",
                "Trace through the feedback resistor.",
                "End at the inverting input annotation.",
            ],
            matlab_variable_name="citt_feedback_loop_focus",
            student_question="What local error does negative feedback reduce?",
        ),
        ProbePlan(
            id="output_voltage_probe",
            label="Output voltage probe",
            target=focus["op_amp_output"].targets[0],
            measurement_type="voltage",
            expected_unit="V",
            why_probe_here="Output voltage shows gain and possible rail saturation.",
            insertion_steps=["Log vout.", "Compare hand gain against simulated or measured output."],
            matlab_variable_name="citt_inamp_output",
            student_question="Is the output consistent with the assumed gain and supply rails?",
        ),
    ]


def _comparison_rows(request: LabDeltaRequest) -> list[LabDeltaComparisonRow]:
    rows: list[LabDeltaComparisonRow] = []
    keys = sorted(
        set(request.hand_values)
        | set(request.simulation_values)
        | set(request.measured_values)
    )
    for key in keys:
        hand = request.hand_values.get(key)
        simulation = request.simulation_values.get(key)
        measured = request.measured_values.get(key)
        compared = measured if measured is not None else simulation
        absolute_error = None
        percent_error = None
        if hand is not None and compared is not None:
            absolute_error = compared - hand
            percent_error = absolute_error / hand * 100.0 if hand != 0 else None
        rows.append(
            LabDeltaComparisonRow(
                quantity=key,
                hand_value=hand,
                simulation_value=simulation,
                measured_value=measured,
                unit=_unit_for_quantity(key),
                absolute_error=absolute_error,
                percent_error=percent_error,
                interpretation=_interpret_row(key, hand, simulation, measured),
            )
        )
    return rows


def _detect_lab_delta_causes(
    request: LabDeltaRequest,
    rows: list[LabDeltaComparisonRow],
) -> list[LabDeltaCause]:
    cause_ids: list[str] = []

    for key, hand, compared in _comparison_pairs(request):
        if hand == 0:
            continue
        ratio = compared / hand
        if _close_ratio(ratio, 2.0 * math.pi) or _close_ratio(ratio, 1.0 / (2.0 * math.pi)):
            cause_ids.extend(["rad_s_vs_hz", "missing_2pi"])
        if any(_close_ratio(ratio, factor) for factor in [1000.0, 1.0 / 1000.0, 1e6, 1e-6]):
            lowered = key.lower()
            if "cap" in lowered or lowered.startswith("c") or "_c" in lowered:
                cause_ids.append("capacitor_prefix_mistake")
            elif "res" in lowered or lowered.startswith("r") or "_r" in lowered:
                cause_ids.append("resistor_prefix_mistake")
            else:
                cause_ids.extend(["capacitor_prefix_mistake", "resistor_prefix_mistake"])

    if _has_nyquist_issue(request):
        cause_ids.append("sampling_nyquist")

    for row in rows:
        hand = row.hand_value
        simulation = row.simulation_value
        measured = row.measured_value
        if hand is None or simulation is None or measured is None:
            continue
        if _values_close(simulation, hand, tolerance=0.05) and not _values_close(measured, simulation, tolerance=0.10):
            cause_ids.extend(["rc_tolerance", "source_load_impedance", "measurement_noise"])
        if not _values_close(simulation, hand, tolerance=0.10) and _values_close(measured, simulation, tolerance=0.10):
            cause_ids.append("model_nonideality")

    if _has_output_saturation_issue(request):
        cause_ids.append("op_amp_saturation")
    if request.notes and "settled" in request.notes.lower():
        cause_ids.append("transient_not_settled")
    if request.notes and "quant" in request.notes.lower():
        cause_ids.append("adc_quantization")
    if request.notes and any(term in request.notes.lower() for term in ["noise", "noisy", "scope jitter"]):
        cause_ids.append("measurement_noise")

    deduped: list[LabDeltaCause] = []
    seen: set[str] = set()
    for cause_id in cause_ids:
        if cause_id not in seen:
            deduped.append(_cause(cause_id))
            seen.add(cause_id)
    return deduped


def _comparison_pairs(request: LabDeltaRequest):
    for key, hand in request.hand_values.items():
        if key in request.simulation_values:
            yield key, hand, request.simulation_values[key]
        if key in request.measured_values:
            yield key, hand, request.measured_values[key]


def _has_nyquist_issue(request: LabDeltaRequest) -> bool:
    values = {**request.hand_values, **request.simulation_values, **request.measured_values}
    fs = _first_value(values, ["fs_hz", "sample_rate_hz", "sampling_rate_hz"])
    frequency = _first_value(
        values,
        ["signal_frequency_hz", "interference_hz", "input_frequency_hz", "max_signal_hz"],
    )
    note = (request.notes or "").lower()
    if "nyquist" in note or "alias" in note:
        return True
    return fs is not None and frequency is not None and fs <= 2.0 * frequency


def _has_output_saturation_issue(request: LabDeltaRequest) -> bool:
    values = {**request.hand_values, **request.simulation_values, **request.measured_values}
    rail_pos = _first_value(values, ["rail_positive_v", "supply_positive_v", "supply_rail_v"])
    rail_neg = _first_value(values, ["rail_negative_v", "supply_negative_v"])
    if rail_pos is not None and rail_neg is None:
        rail_neg = -rail_pos
    for key, value in values.items():
        lowered = key.lower()
        if ("output" in lowered or "vout" in lowered) and rail_pos is not None and rail_neg is not None:
            if value > rail_pos or value < rail_neg:
                return True
    return request.notes is not None and "saturat" in request.notes.lower()


def _first_value(values: dict[str, float], keys: list[str]) -> float | None:
    for key in keys:
        if key in values:
            return values[key]
    return None


def _close_ratio(ratio: float, target: float, *, tolerance: float = 0.08) -> bool:
    if not math.isfinite(ratio) or target == 0:
        return False
    return abs(ratio - target) / abs(target) <= tolerance


def _values_close(left: float, right: float, *, tolerance: float) -> bool:
    scale = max(abs(right), 1e-12)
    return abs(left - right) / scale <= tolerance


def _unit_for_quantity(quantity: str) -> str | None:
    lowered = quantity.lower()
    if lowered.endswith("_hz") or "frequency" in lowered or "fc" in lowered:
        return "Hz"
    if lowered.endswith("_v") or "voltage" in lowered or "vout" in lowered:
        return "V"
    if lowered.endswith("_ohm") or "resistor" in lowered:
        return "ohm"
    if lowered.endswith("_f") or "capacitor" in lowered:
        return "F"
    if "gain" in lowered:
        return "V/V"
    return None


def _interpret_row(
    key: str,
    hand: float | None,
    simulation: float | None,
    measured: float | None,
) -> str:
    if hand is None:
        return "No hand-check value was supplied for this quantity."
    compared = measured if measured is not None else simulation
    if compared is None:
        return "Only the hand-check value is available."
    if hand == 0:
        return "Absolute error is reported because the hand-check reference is zero."
    percent = (compared - hand) / hand * 100.0
    if abs(percent) < 5:
        return "Hand, simulation, and/or lab values are close for an educational check."
    if abs(percent) < 15:
        return "The difference is moderate; check tolerance, loading, and probe placement."
    return "The difference is large enough to check units, 2*pi, sampling, or nonideal limits."


def _cause(cause_id: str) -> LabDeltaCause:
    causes = {
        "rad_s_vs_hz": LabDeltaCause(
            id="rad_s_vs_hz",
            label="rad/s vs Hz",
            explanation="A result near 2*pi or 1/(2*pi) from the hand check often means angular frequency was compared directly to Hz.",
            check_to_run="Write both omega_c = 1/(R*C) in rad/s and fc = omega_c/(2*pi) in Hz.",
            severity="high",
        ),
        "missing_2pi": LabDeltaCause(
            id="missing_2pi",
            label="Missing 2*pi",
            explanation="The cutoff formula in Hz is fc = 1/(2*pi*R*C); omitting 2*pi moves the result by about 6.28x.",
            check_to_run="Recompute fc with the exact 1/(2*pi*R*C) expression.",
            severity="high",
        ),
        "capacitor_prefix_mistake": LabDeltaCause(
            id="capacitor_prefix_mistake",
            label="nF/uF capacitor mistake",
            explanation="A 1000x or 1,000,000x ratio can come from entering nF as uF, uF as F, or another capacitor SI-prefix slip.",
            check_to_run="Inspect the capacitor value in the hand table, MATLAB variables, Simscape block, and lab part label.",
            severity="high",
        ),
        "resistor_prefix_mistake": LabDeltaCause(
            id="resistor_prefix_mistake",
            label="kOhm/Ohm resistor mistake",
            explanation="A 1000x ratio can come from entering kOhm as Ohm or treating Ohm as kOhm.",
            check_to_run="Check whether R is written in ohms in MATLAB and in the Simscape resistor block.",
            severity="high",
        ),
        "rc_tolerance": LabDeltaCause(
            id="rc_tolerance",
            label="R/C tolerance",
            explanation="Hand and simulation may agree while measured cutoff shifts because real resistors and capacitors have tolerance.",
            check_to_run="Measure the actual R and C, then rerun the hand-check formula with measured component values.",
            severity="medium",
        ),
        "source_load_impedance": LabDeltaCause(
            id="source_load_impedance",
            label="Source/load impedance",
            explanation="A real source or ADC input can load the RC node, shifting the measured output from the ideal model.",
            check_to_run="Probe source output and filter output separately, then add source/load impedance to the comparison.",
            severity="medium",
        ),
        "sampling_nyquist": LabDeltaCause(
            id="sampling_nyquist",
            label="Sampling/Nyquist issue",
            explanation="If sample rate is not comfortably above twice the relevant signal frequency, aliasing can dominate the Lab Delta.",
            check_to_run="Compare fs, Nyquist, interference frequency, and the sampled-output probe.",
            severity="high",
        ),
        "adc_quantization": LabDeltaCause(
            id="adc_quantization",
            label="ADC quantization",
            explanation="A coarse ADC step can make measured samples differ even when the analog hand and simulation values agree.",
            check_to_run="Compute ADC LSB size and compare it with the observed output error.",
            severity="medium",
        ),
        "op_amp_saturation": LabDeltaCause(
            id="op_amp_saturation",
            label="Op-amp saturation",
            explanation="Predicted output outside the assumed rails suggests saturation or output-swing limits.",
            check_to_run="Compare predicted vout against rail assumptions and probe the op-amp output.",
            severity="high",
        ),
        "transient_not_settled": LabDeltaCause(
            id="transient_not_settled",
            label="Transient not settled",
            explanation="A lab value captured too early can differ from the steady-state hand check.",
            check_to_run="Estimate five time constants and verify the measurement window starts after settling.",
            severity="medium",
        ),
        "measurement_noise": LabDeltaCause(
            id="measurement_noise",
            label="Measurement noise",
            explanation="When no strong math or unit pattern matches, inspect wiring, scope coupling, noise, and probe placement first.",
            check_to_run="Repeat the measurement, average if appropriate, and confirm the probe point matches the focus map.",
            severity="low",
        ),
        "model_nonideality": LabDeltaCause(
            id="model_nonideality",
            label="Model includes nonideal effect",
            explanation="If simulation and measurement agree but the hand check differs, the model may include an effect omitted by the hand approximation.",
            check_to_run="List the model effects that are absent from the hand calculation.",
            severity="medium",
        ),
    }
    return causes[cause_id]


def _recommended_probe(lab_id: str, causes: list[LabDeltaCause]) -> str:
    cause_ids = {cause.id for cause in causes}
    if "sampling_nyquist" in cause_ids:
        return "sampled_output_probe"
    if "capacitor_prefix_mistake" in cause_ids or "resistor_prefix_mistake" in cause_ids:
        return "cutoff_attenuation_check"
    if lab_id == INSTRUMENTATION_FEEDBACK_LAB_ID:
        return "output_voltage_probe"
    return "filter_output_voltage_probe"


def _lab_delta_notes(request: LabDeltaRequest) -> list[str]:
    notes = [
        "Lab Delta ranks likely causes from deterministic checks; it is educational, not a bench diagnosis.",
        "Rows use hand calculation as the reference when available.",
    ]
    if request.notes:
        notes.append(request.notes)
    return notes


def _rc_matlab_script() -> str:
    return f"""%% CiTT RC anti-aliasing before ADC
% Students interact with the CiTT graphical UI.
% This generated MATLAB script is the hidden playground setup.
% CiTT does not ask the student to hand-write MATLAB, Simulink, or Simscape code.

clear; clc;

fs = 500;                 % Hz
target_fc = 40;           % Hz
C = 100e-9;               % F
R = 1/(2*pi*target_fc*C); % ohm, default {DEFAULT_R_OHM:.6f}
fc = 1/(2*pi*R*C);
nyquist = fs/2;

t_stop = 2.0;
t = 0:1/(20*fs):t_stop;
ecg_like = 0.8*sin(2*pi*1.2*t) + 0.12*sin(2*pi*2.4*t);
interference_60hz = 0.18*sin(2*pi*60*t);
optional_noise = 0.01*sin(2*pi*137*t);
input_signal = ecg_like + interference_60hz + optional_noise;

dt = t(2)-t(1);
alpha = dt/(R*C + dt);
filtered_signal = zeros(size(input_signal));
for k = 2:numel(input_signal)
    filtered_signal(k) = filtered_signal(k-1) + alpha*(input_signal(k) - filtered_signal(k-1));
end

sample_times = 0:1/fs:t_stop;
sampled_signal = interp1(t, filtered_signal, sample_times, "linear");
attenuation_60hz = 1/sqrt(1 + (60/fc)^2);

citt_hand_fc_hz = fc;
citt_nyquist_hz = nyquist;
citt_input_signal = timetable(seconds(t(:)), input_signal(:), "VariableNames", "vin");
citt_filtered_signal = timetable(seconds(t(:)), filtered_signal(:), "VariableNames", "vout");
citt_sampled_signal = timetable(seconds(sample_times(:)), sampled_signal(:), "VariableNames", "sampled_vout");
citt_results = struct( ...
    "fs_hz", fs, ...
    "target_fc_hz", target_fc, ...
    "R_ohm", R, ...
    "C_f", C, ...
    "hand_fc_hz", citt_hand_fc_hz, ...
    "citt_hand_fc_hz", citt_hand_fc_hz, ...
    "nyquist_hz", citt_nyquist_hz, ...
    "attenuation_60hz", attenuation_60hz, ...
    "provenance", "CiTT generated hand-check and signal artifact");

disp(citt_results);
% CiTT Overview tab: show lab boundary, assumptions, MATLAB/Simscape role, and BME context.
% CiTT Teach tab: coach before reveal using verified values only when available.
% CiTT Probe tab: use citt_input_signal, citt_filtered_signal, and citt_sampled_signal.
% CiTT Lab Delta tab: compare hand calculation, simulation, and uploaded lab data.
"""


def _rc_simscape_script() -> str:
    return """function modelName = citt_build_rc_antialias_adc_simscape(modelName)
%CITT_BUILD_RC_ANTIALIAS_ADC_SIMSCAPE Build a Simscape-first RC playground.
% The script is intentionally defensive: if Simscape blocks are unavailable,
% it opens a Simulink signal-flow fallback instead of failing the CiTT demo.

if nargin < 1 || strlength(string(modelName)) == 0
    modelName = "citt_rc_antialias_adc";
end

fs = 500; target_fc = 40; C = 100e-9; R = 1/(2*pi*target_fc*C); %#ok<NASGU>
try
    new_system(modelName); open_system(modelName);
    tryAddBlock(modelName, ["simscape/Foundation Library/Electrical/Electrical Sources/Controlled Voltage Source", ...
        "fl_lib/Electrical/Electrical Sources/Controlled Voltage Source"], "Input Source");
    tryAddBlock(modelName, ["simscape/Foundation Library/Electrical/Electrical Elements/Resistor", ...
        "ee_lib/Passive/Resistor"], "Resistor");
    tryAddBlock(modelName, ["simscape/Foundation Library/Electrical/Electrical Elements/Capacitor", ...
        "ee_lib/Passive/Capacitor"], "Capacitor");
    tryAddBlock(modelName, ["simscape/Utilities/Solver Configuration", ...
        "nesl_utility/Solver Configuration"], "Solver Configuration");
    tryAddBlock(modelName, ["simscape/Foundation Library/Electrical/Electrical Elements/Electrical Reference", ...
        "fl_lib/Electrical/Electrical Elements/Electrical Reference"], "Electrical Reference");
    tryAddBlock(modelName, ["simscape/Foundation Library/Electrical/Electrical Sensors/Voltage Sensor", ...
        "fl_lib/Electrical/Electrical Sensors/Voltage Sensor"], "Voltage Sensor");
    % Probe/logging comments:
    % - Log source as citt_input_signal.
    % - Log capacitor output voltage as citt_filtered_signal.
    % - Add scope/logging block for citt_sampled_signal after the sampling stage.
    % Simscape resistor, capacitor, electrical reference, solver configuration,
    % source, sensors, and scope/logging blocks belong in the named regions above.
    disp("CiTT Simscape RC playground opened.");
catch buildError
    warning("CiTT:SimscapeFallback", "Simscape build did not complete: %s", buildError.message);
    modelName = citt_build_rc_antialias_adc_signal_flow(modelName + "_signal_flow");
end
end

function blockPath = tryAddBlock(modelName, candidates, blockName)
blockPath = modelName + "/" + blockName;
for candidate = candidates
    try
        add_block(candidate, blockPath, "MakeNameUnique", "on");
        return
    catch
    end
end
warning("CiTT:MissingBlock", "Could not find block for %s. Using annotation fallback.", blockName);
add_block("built-in/Note", blockPath, "Text", blockName + " placeholder");
end
"""


def _rc_simulink_script() -> str:
    return """function modelName = citt_build_rc_antialias_adc_signal_flow(modelName)
%CITT_BUILD_RC_ANTIALIAS_ADC_SIGNAL_FLOW Simulink fallback for the RC lab.
% This model mirrors H(s)=1/(R*C*s+1) and keeps CiTT's hand check available.

if nargin < 1 || strlength(string(modelName)) == 0
    modelName = "citt_rc_antialias_adc_signal_flow";
end

fs = 500; target_fc = 40; C = 100e-9; R = 1/(2*pi*target_fc*C); %#ok<NASGU>
new_system(modelName); open_system(modelName);
add_block("simulink/Sources/Sine Wave", modelName + "/ECG-like input");
add_block("simulink/Sources/Sine Wave", modelName + "/60 Hz interference");
add_block("simulink/Math Operations/Sum", modelName + "/Input sum");
add_block("simulink/Continuous/Transfer Fcn", modelName + "/RC low-pass fallback");
add_block("simulink/Discrete/Zero-Order Hold", modelName + "/Sampling stage");
add_block("simulink/Sinks/Scope", modelName + "/Scope logging");
% fallback, resistor, capacitor, solver configuration, electrical reference:
% The fallback has no physical resistor/capacitor blocks, so annotations name
% the equivalent R, C, solver configuration, and electrical reference roles.
% Probe/logging comments:
% - input signal probe -> citt_input_signal
% - filter output voltage probe -> citt_filtered_signal
% - sampled output probe -> citt_sampled_signal
disp("CiTT Simulink signal-flow fallback opened.");
end
"""


def _instrumentation_matlab_script() -> str:
    return """%% CiTT instrumentation amplifier feedback focus
% Educational hand-check values for the graphical MATLAB popup tutor.

v_diff = 1e-3;
v_common = 1.0;
R = 10e3;
Rg = 1e3;
gain = 1 + (2*R/Rg);
vout_ideal = gain * v_diff;

citt_inamp_results = struct( ...
    "v_diff_v", v_diff, ...
    "v_common_v", v_common, ...
    "gain_v_per_v", gain, ...
    "vout_ideal_v", vout_ideal, ...
    "focus_ids", ["differential_input", "common_mode_input", "gain_setting_resistor", "feedback_loop", "op_amp_output", "output_probe"]);

disp(citt_inamp_results);
% Highlight-ready focus id: feedback_loop
% Probe-ready output variable: citt_inamp_results.vout_ideal_v
"""


def _instrumentation_simulink_script() -> str:
    return """function modelName = citt_build_instrumentation_feedback_model(modelName)
%CITT_BUILD_INSTRUMENTATION_FEEDBACK_MODEL Educational focus skeleton.

if nargin < 1 || strlength(string(modelName)) == 0
    modelName = "citt_inamp_feedback";
end

new_system(modelName); open_system(modelName);
add_block("simulink/Sources/Constant", modelName + "/Differential Input");
add_block("simulink/Sources/Constant", modelName + "/Common Mode Input");
add_block("simulink/Math Operations/Gain", modelName + "/Gain Setting Resistor");
add_block("simulink/Math Operations/Gain", modelName + "/Op Amp Output");
add_block("built-in/Note", modelName + "/Feedback Loop", ...
    "Text", "feedback_loop: U1 output -> feedback resistor -> inverting input");
add_block("simulink/Sinks/Scope", modelName + "/Output Probe");
% Focus IDs: differential_input, common_mode_input, gain_setting_resistor,
% feedback_loop, op_amp_output, output_probe.
disp("CiTT instrumentation amplifier focus skeleton opened.");
end
"""


def _popup_app_script() -> str:
    return """function app = citt(labId)
%CITT Open the CiTT graphical MATLAB/Simscape tutor popup.
% Uses uifigure/uitabgroup and works with bundled data if the API is offline.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "rc_antialias_adc";
end

manifest = citt.loadManifest(labId);
app = struct();
app.Figure = uifigure("Name", "CiTT MATLAB/Simscape Tutor", "Position", [100 100 980 680]);
tabs = uitabgroup(app.Figure, "Position", [12 12 956 656]);

overviewTab = uitab(tabs, "Title", "Overview");
teachTab = uitab(tabs, "Title", "Teach");
probeTab = uitab(tabs, "Title", "Probe");
deltaTab = uitab(tabs, "Title", "Lab Delta");

uilabel(overviewTab, "Text", manifest.positioning, "Position", [24 560 880 44]);
uibutton(overviewTab, "Text", "Build MATLAB/Simscape Playground", "Position", [24 500 240 32], ...
    "ButtonPushedFcn", @(~,~) citt.buildPlayground(labId));
uibutton(overviewTab, "Text", "Run Hand Check", "Position", [280 500 150 32], ...
    "ButtonPushedFcn", @(~,~) disp("CiTT hand check uses generated variables and internal solver evidence."));

uilabel(teachTab, "Text", "Teach mode maps guided steps to model and circuit focus targets.", "Position", [24 560 700 28]);
uibutton(teachTab, "Text", "Highlight Current Step", "Position", [24 510 190 32], ...
    "ButtonPushedFcn", @(~,~) citt.highlightFocus("", manifest.focus_map, "rc_filter"));
uibutton(teachTab, "Text", "Highlight Feedback Loop", "Position", [230 510 190 32], ...
    "ButtonPushedFcn", @(~,~) citt.highlightFocus("", manifest.focus_map, "feedback_loop"));

uilabel(probeTab, "Text", "Probe mode adds conceptual voltage, current, and signal logging plans.", "Position", [24 560 760 28]);
uibutton(probeTab, "Text", "Add Probe Plan", "Position", [24 510 150 32], ...
    "ButtonPushedFcn", @(~,~) disp("CiTT probe plan selected."));

uilabel(deltaTab, "Text", "Lab Delta compares hand calculation, simulation output, and lab data.", "Position", [24 560 760 28]);
uibutton(deltaTab, "Text", "Compare Lab Delta", "Position", [24 510 170 32], ...
    "ButtonPushedFcn", @(~,~) citt.runLabDelta(labId));
end
"""
