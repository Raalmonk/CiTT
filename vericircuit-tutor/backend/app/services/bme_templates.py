from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

from app.models.circuit_ir import BMETemplateMetadata, CircuitProblem, Component, Goal


class BMETemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_problem: CircuitProblem
    biomedical_context: str
    signal_chain_role: str
    assumptions: list[str]
    what_students_should_learn: list[str]
    common_lab_mistakes: list[str]
    typical_signal_range: str | None = None
    safety_note: str | None = None
    noise_sources: list[str] = Field(default_factory=list)
    real_world_nonidealities: list[str] = Field(default_factory=list)
    recommended_next_block: str | None = None
    nominal_supply_rails_v: dict[str, float] | None = None
    supply_positive_v: float | None = None
    supply_negative_v: float | None = None
    output_swing_margin_v: float = 0.0
    adc_sampling_frequency_hz: float | None = None
    adc_target_cutoff_hz: float | None = None
    adc_resolution_bits: int | None = None
    adc_full_scale_voltage_v: float | None = None
    adc_input_impedance_ohm: float | None = None
    noise_bandwidth_hz: float | None = None
    thermal_noise_temperature_k: float = 300.0
    thermal_noise_resistor_ids: list[str] = Field(default_factory=list)
    photodiode_shot_noise_current_id: str | None = None
    op_amp_input_noise_nv_per_sqrt_hz: float | None = None
    flicker_noise_corner_hz: float | None = None
    flicker_noise_component_ids: list[str] = Field(default_factory=list)
    cmrr_mismatch_percent: float | None = None
    cmrr_mismatch_component_id: str | None = None

    @property
    def metadata(self) -> BMETemplateMetadata:
        return BMETemplateMetadata(
            biomedical_context=self.biomedical_context,
            signal_chain_role=self.signal_chain_role,
            assumptions=self.assumptions,
            what_students_should_learn=self.what_students_should_learn,
            common_lab_mistakes=self.common_lab_mistakes,
            typical_signal_range=self.typical_signal_range,
            safety_note=self.safety_note,
            noise_sources=self.noise_sources,
            real_world_nonidealities=self.real_world_nonidealities,
            recommended_next_block=self.recommended_next_block,
            nominal_supply_rails_v=self.nominal_supply_rails_v,
            supply_positive_v=self.supply_positive_v,
            supply_negative_v=self.supply_negative_v,
            output_swing_margin_v=self.output_swing_margin_v,
            adc_sampling_frequency_hz=self.adc_sampling_frequency_hz,
            adc_target_cutoff_hz=self.adc_target_cutoff_hz,
            adc_resolution_bits=self.adc_resolution_bits,
            adc_full_scale_voltage_v=self.adc_full_scale_voltage_v,
            adc_input_impedance_ohm=self.adc_input_impedance_ohm,
            noise_bandwidth_hz=self.noise_bandwidth_hz,
            thermal_noise_temperature_k=self.thermal_noise_temperature_k,
            thermal_noise_resistor_ids=self.thermal_noise_resistor_ids,
            photodiode_shot_noise_current_id=self.photodiode_shot_noise_current_id,
            op_amp_input_noise_nv_per_sqrt_hz=self.op_amp_input_noise_nv_per_sqrt_hz,
            flicker_noise_corner_hz=self.flicker_noise_corner_hz,
            flicker_noise_component_ids=self.flicker_noise_component_ids,
            cmrr_mismatch_percent=self.cmrr_mismatch_percent,
            cmrr_mismatch_component_id=self.cmrr_mismatch_component_id,
        )


ECG_FRONT_END_TEXT = (
    "BME template: ECG front-end differential amplifier with a 1 mV electrode "
    "difference on a 1 V common-mode level. Find the output voltage."
)

EMG_BAND_PASS_TEXT = (
    "BME template: EMG band-pass chain with an RC high-pass followed by an RC "
    "low-pass at 100 Hz. Find Vout."
)

PRESSURE_SENSOR_DIVIDER_TEXT = (
    "BME template: pressure sensor voltage divider with a 5 V excitation, "
    "10 kOhm bias resistor, and 12 kOhm sensor. Find Vout."
)

PRESSURE_SENSOR_BRIDGE_TEXT = (
    "BME template: pressure sensor Wheatstone bridge with one active arm changed "
    "by pressure. Find the bridge differential voltage."
)

STRAIN_GAUGE_BRIDGE_TEXT = (
    "BME template: strain gauge Wheatstone bridge with one 1002 ohm gauge arm "
    "and three 1000 ohm arms. Find the bridge output."
)

THERMISTOR_DIVIDER_TEXT = (
    "BME template: thermistor divider with a 5 V excitation, 10 kOhm fixed "
    "resistor, and 12 kOhm thermistor. Find the temperature-sense voltage."
)

PHOTODIODE_TIA_TEXT = (
    "BME template: photodiode transimpedance amplifier with 10 uA photocurrent "
    "and a 1 MOhm feedback resistor. Find Vout."
)

INSTRUMENTATION_AMPLIFIER_TEXT = (
    "BME template: instrumentation amplifier for a 1 mV differential sensor "
    "signal using ideal op-amps. Find the output voltage."
)

ANTI_ALIASING_LOW_PASS_TEXT = (
    "BME template: anti-aliasing RC low-pass filter at 1 kHz with R = 3.18 kOhm "
    "and C = 100 nF. Find Vout."
)


BME_TEMPLATE_METADATA: dict[str, BMETemplateMetadata] = {
    "bme_ecg_front_end": BMETemplateMetadata(
        biomedical_context=(
            "ECG electrodes produce a small differential cardiac signal riding on a much larger common-mode body potential."
        ),
        signal_chain_role="Front-end differential amplifier that rejects common-mode voltage and scales the ECG lead signal.",
        assumptions=[
            "The electrode model is simplified to two ideal DC sources with a 1 mV differential signal.",
            "The op-amp is ideal and the matched resistor ratios set a gain of 10.",
        ],
        what_students_should_learn=[
            "Separate differential signal from common-mode voltage.",
            "Relate resistor ratio matching to differential gain.",
            "Read a verified output as a sensor-front-end quantity, not just a node voltage.",
        ],
        common_lab_mistakes=[
            "Measuring each electrode to ground and forgetting the differential input.",
            "Swapping the amplifier inputs and interpreting the sign incorrectly.",
            "Assuming ideal common-mode rejection when resistor ratios are mismatched.",
        ],
        typical_signal_range="ECG differential signals are often around 0.5 mV to 5 mV, while electrode offsets can be much larger.",
        safety_note="Real patient-connected ECG circuits require isolation, leakage-current limits, and approved medical-safety design practices.",
        noise_sources=[
            "Power-line interference",
            "Electrode motion artifacts",
            "Large electrode half-cell offsets",
        ],
        real_world_nonidealities=[
            "CMRR depends on resistor matching and instrumentation-amplifier design.",
            "Input bias current and electrode impedance can create extra offsets.",
            "Protection and isolation components change the real front-end behavior.",
        ],
        recommended_next_block="High-pass baseline-wander removal followed by instrumentation gain and driven-reference/common-mode control.",
        nominal_supply_rails_v={"negative": 0.0, "positive": 3.3},
        supply_negative_v=0.0,
        supply_positive_v=3.3,
        output_swing_margin_v=0.1,
        noise_bandwidth_hz=150.0,
        thermal_noise_resistor_ids=["RINN", "RF", "RINP", "RREF"],
        op_amp_input_noise_nv_per_sqrt_hz=20.0,
        flicker_noise_corner_hz=10.0,
        flicker_noise_component_ids=["RINN", "RF", "RINP", "RREF"],
        cmrr_mismatch_percent=1.0,
        cmrr_mismatch_component_id="RF",
    ),
    "bme_emg_band_pass_chain": BMETemplateMetadata(
        biomedical_context=(
            "Surface EMG measurements need low-frequency motion artifacts and high-frequency noise reduced before feature extraction."
        ),
        signal_chain_role="Passive band-pass conditioning stage between the EMG electrode model and downstream gain or ADC stages.",
        assumptions=[
            "The EMG chain is a passive first-order high-pass followed by a first-order low-pass.",
            "The source AC magnitude is 1 V so Vout is also the transfer magnitude at 100 Hz.",
        ],
        what_students_should_learn=[
            "Connect high-pass and low-pass sections to a practical EMG signal band.",
            "Use phasor magnitude and phase to reason about filter behavior.",
            "Recognize that passive cascaded filters load each other.",
        ],
        common_lab_mistakes=[
            "Treating the two RC stages as independent even though the second stage loads the first.",
            "Using Hz where angular frequency rad/s belongs.",
            "Checking only gain magnitude and ignoring phase shift near the passband edges.",
        ],
        typical_signal_range="Surface EMG is commonly in the microvolt to low millivolt range before amplification.",
        safety_note="Human-connected EMG systems need isolated front ends and current-limited electrodes.",
        noise_sources=[
            "Motion artifact",
            "Power-line pickup",
            "Electrode-skin impedance variation",
            "Cross-talk from nearby muscles",
        ],
        real_world_nonidealities=[
            "Passive stages load each other and the electrode source impedance.",
            "Amplifier input noise can dominate small EMG signals.",
            "Real filters use component tolerances that move the corner frequencies.",
        ],
        recommended_next_block="Low-noise instrumentation gain, notch filtering when appropriate, rectification/envelope extraction, then ADC anti-aliasing.",
    ),
    "bme_pressure_sensor_divider": BMETemplateMetadata(
        biomedical_context="A resistive pressure sensor converts pressure at one operating point into a resistance.",
        signal_chain_role="Excitation and readout divider that turns sensor resistance into a voltage for measurement.",
        assumptions=[
            "The pressure sensor is represented by a resistance of 12 kOhm at this operating point.",
        ],
        what_students_should_learn=[
            "Map a sensor resistance change into a voltage-divider output.",
            "Recognize the tradeoff between bias resistance and output sensitivity.",
            "Keep excitation voltage and measured output reference clear.",
        ],
        common_lab_mistakes=[
            "Putting the sensor in the wrong divider leg and reversing the expected trend.",
            "Loading the divider with the measurement instrument.",
            "Confusing sensor resistance with the output voltage.",
        ],
        typical_signal_range="Resistive pressure sensors vary by device; this template uses a 10 kOhm to 12 kOhm operating region.",
        safety_note="Pressure-sensor excitation should be current- and power-limited when attached to patient-facing hardware.",
        noise_sources=[
            "Excitation-supply noise",
            "Lead resistance",
            "Mechanical vibration",
        ],
        real_world_nonidealities=[
            "Sensor resistance may be nonlinear with pressure.",
            "Self-heating can shift the sensed resistance.",
            "ADC input impedance can load the divider output.",
        ],
        recommended_next_block="Buffer or instrumentation amplifier followed by calibration and ADC input filtering.",
    ),
    "bme_pressure_sensor_bridge": BMETemplateMetadata(
        biomedical_context="A pressure bridge turns a small pressure-driven resistance change into a differential bridge voltage.",
        signal_chain_role="Wheatstone bridge sensor interface before instrumentation amplification.",
        assumptions=[
            "The active pressure-sensor arm is modeled as 3.6 kOhm while the other arms are 3.5 kOhm.",
        ],
        what_students_should_learn=[
            "Compare bridge midpoint voltages rather than either midpoint alone.",
            "Track the sign of a differential bridge output.",
            "Relate balance and imbalance to sensor resistance changes.",
        ],
        common_lab_mistakes=[
            "Measuring only one midpoint to ground and missing the differential output.",
            "Reversing sense_p and sense_n in the reported bridge voltage.",
            "Assuming a bridge output is zero after one arm changes.",
        ],
        typical_signal_range="Bridge outputs are often millivolts or less for small resistance changes before gain.",
        safety_note="Bridge excitation should be limited to avoid sensor heating and unsafe patient-connected power paths.",
        noise_sources=[
            "Excitation drift",
            "Thermal drift",
            "Lead-wire resistance",
        ],
        real_world_nonidealities=[
            "Bridge balance depends on resistor tolerance and temperature.",
            "Sensor response may be nonlinear outside the calibrated range.",
            "Instrumentation-amplifier input offset can be comparable to small bridge outputs.",
        ],
        recommended_next_block="Instrumentation amplifier with differential gain, offset trim, and low-pass filtering before ADC.",
    ),
    "bme_strain_gauge_wheatstone": BMETemplateMetadata(
        biomedical_context="A strain gauge changes resistance slightly when a tissue, beam, or load-cell element deforms.",
        signal_chain_role="Quarter-bridge strain readout that converts a tiny resistance shift into a differential voltage.",
        assumptions=[
            "Only one bridge arm changes with strain; lead resistance and excitation noise are ignored.",
        ],
        what_students_should_learn=[
            "See why bridge circuits are useful for very small resistance changes.",
            "Use differential voltage polarity to infer which arm changed.",
            "Connect resistance mismatch to output sensitivity.",
        ],
        common_lab_mistakes=[
            "Expecting a large output from a tiny gauge resistance change.",
            "Forgetting that lead resistance can matter in real strain-gauge labs.",
            "Reporting the magnitude without the sign of the bridge output.",
        ],
        typical_signal_range="Quarter-bridge strain outputs are commonly in the microvolt to millivolt range before amplification.",
        safety_note="Excitation should be limited to avoid strain-gauge self-heating, especially on tissue-contact fixtures.",
        noise_sources=[
            "Thermal drift",
            "Lead-wire resistance",
            "Mechanical vibration",
        ],
        real_world_nonidealities=[
            "Gauge factor, adhesive strain transfer, and temperature compensation matter in real measurements.",
            "Lead resistance and bridge completion resistors can dominate small resistance changes.",
            "Amplifier offset can hide small bridge imbalance.",
        ],
        recommended_next_block="Instrumentation amplifier, bridge balancing, temperature compensation, and calibrated strain conversion.",
    ),
    "bme_thermistor_divider": BMETemplateMetadata(
        biomedical_context="A thermistor maps temperature to resistance for body-temperature or device-temperature sensing.",
        signal_chain_role="Temperature-sense divider that converts thermistor resistance into an ADC-readable voltage.",
        assumptions=[
            "The thermistor is represented by its resistance at one temperature point.",
        ],
        what_students_should_learn=[
            "Translate a thermistor resistance into a measured divider voltage.",
            "Identify how the fixed resistor sets sensitivity near an operating point.",
            "Separate the electrical readout from the thermistor temperature curve.",
        ],
        common_lab_mistakes=[
            "Assuming voltage is linear with temperature over a wide range.",
            "Using the wrong divider orientation for an NTC thermistor trend.",
            "Ignoring ADC input loading or self-heating in a real lab setup.",
        ],
        typical_signal_range="A 10 kOhm NTC thermistor is often read around a few volts in a 5 V divider near room/body temperature.",
        safety_note="Thermistor excitation should be low enough to avoid self-heating and patient-contact heating.",
        noise_sources=[
            "ADC quantization noise",
            "Reference-voltage drift",
            "Thermal gradients between sensor and target",
        ],
        real_world_nonidealities=[
            "Resistance-temperature behavior is nonlinear and needs a beta or Steinhart-Hart model.",
            "Self-heating shifts the measured temperature.",
            "Thermal time constant can lag fast physiology.",
        ],
        recommended_next_block="ADC buffering/filtering followed by thermistor calibration and temperature conversion.",
    ),
    "bme_photodiode_tia": BMETemplateMetadata(
        biomedical_context="Optical biosensing often begins with a photodiode current proportional to light intensity.",
        signal_chain_role="Transimpedance amplifier that converts photodiode current into voltage.",
        assumptions=[
            "The photodiode is modeled as an ideal 10 uA current source.",
            "The op-amp is ideal and unsaturated.",
        ],
        what_students_should_learn=[
            "Relate photocurrent direction and feedback resistance to output polarity.",
            "Understand current-to-voltage conversion as transimpedance gain.",
            "Check whether an ideal output would saturate a real amplifier.",
        ],
        common_lab_mistakes=[
            "Reversing current source polarity and getting the output sign wrong.",
            "Forgetting that large feedback resistance magnifies offset and bias-current effects.",
            "Treating the summing node as exactly ground in nonideal hardware without checking limits.",
        ],
        typical_signal_range="Photodiode currents can range from nA to uA depending on light level and sensor area; this template uses 10 uA.",
        safety_note="Optical systems should respect illumination exposure limits for tissue, eye, or sample safety.",
        noise_sources=[
            "Shot noise",
            "Ambient light pickup",
            "Op-amp voltage and current noise",
        ],
        real_world_nonidealities=[
            "Feedback capacitance is often needed for stability.",
            "Dark current and op-amp bias current add offsets.",
            "Output swing limits can saturate with high photocurrent or large feedback resistance.",
        ],
        recommended_next_block="Feedback-capacitor stability check, ambient-light rejection, and low-pass filtering before ADC.",
        nominal_supply_rails_v={"negative": 0.0, "positive": 3.3},
        supply_negative_v=0.0,
        supply_positive_v=3.3,
        output_swing_margin_v=0.1,
        noise_bandwidth_hz=1000.0,
        thermal_noise_resistor_ids=["RF"],
        photodiode_shot_noise_current_id="IPD",
        op_amp_input_noise_nv_per_sqrt_hz=15.0,
        flicker_noise_corner_hz=20.0,
        flicker_noise_component_ids=["RF"],
    ),
    "bme_instrumentation_amplifier": BMETemplateMetadata(
        biomedical_context="Many biomedical sensors produce millivolt differential signals on top of a common-mode voltage.",
        signal_chain_role="Instrumentation amplifier stage that boosts the differential sensor signal before digitization.",
        assumptions=[
            "The three-op-amp instrumentation amplifier is ideal.",
            "The first-stage gain is 1 + 2R/RG with R = 10 kOhm and RG = 2 kOhm.",
        ],
        what_students_should_learn=[
            "Trace a small differential input through an instrumentation amplifier.",
            "Connect RG to differential gain.",
            "Distinguish common-mode level from differential output.",
        ],
        common_lab_mistakes=[
            "Using single-ended gain formulas for a differential amplifier.",
            "Forgetting the gain contribution of the first stage.",
            "Ignoring output swing limits in a real op-amp implementation.",
        ],
        typical_signal_range="Biomedical differential sensor inputs are often microvolts to millivolts before instrumentation gain.",
        safety_note="Patient-connected instrumentation amplifiers require isolation, input protection, and leakage-current controls.",
        noise_sources=[
            "Common-mode interference",
            "Input-referred amplifier noise",
            "Electrode or sensor impedance mismatch",
        ],
        real_world_nonidealities=[
            "CMRR is finite and falls with frequency.",
            "Input offset and bias currents can be amplified.",
            "Output swing and supply rails limit usable gain.",
        ],
        recommended_next_block="Band-limiting, level shifting, anti-aliasing, and ADC driver stage.",
        nominal_supply_rails_v={"negative": 0.0, "positive": 3.3},
        supply_negative_v=0.0,
        supply_positive_v=3.3,
        output_swing_margin_v=0.1,
        noise_bandwidth_hz=500.0,
        thermal_noise_resistor_ids=["R1", "R2", "RG", "R3", "R4", "R5", "R6"],
        op_amp_input_noise_nv_per_sqrt_hz=20.0,
        flicker_noise_corner_hz=10.0,
        flicker_noise_component_ids=["RG"],
        cmrr_mismatch_percent=1.0,
        cmrr_mismatch_component_id="R4",
    ),
    "bme_anti_aliasing_low_pass": BMETemplateMetadata(
        biomedical_context="Before ADC sampling, biomedical signals need high-frequency content attenuated to reduce aliasing.",
        signal_chain_role="RC anti-aliasing low-pass stage placed before the ADC input.",
        assumptions=[
            "The 1 V AC source makes Vout equal to the low-pass transfer value at 1 kHz.",
        ],
        what_students_should_learn=[
            "Connect an RC corner frequency to ADC anti-aliasing behavior.",
            "Use magnitude and phase to describe low-pass filtering.",
            "Explain why the capacitor diverts high-frequency current away from the output node.",
        ],
        common_lab_mistakes=[
            "Choosing a cutoff without considering sampling frequency.",
            "Forgetting that ADC input impedance and sampling capacitance can load the RC node.",
            "Using 1/(RC) instead of 1/(2*pi*RC) for the cutoff frequency in Hz.",
        ],
        typical_signal_range="The template uses a normalized 1 V AC source so Vout is the transfer magnitude at the analysis frequency.",
        safety_note="Anti-aliasing filters in patient-connected systems still sit behind the isolated, protected front end.",
        noise_sources=[
            "Wideband amplifier noise",
            "ADC sampling kickback",
            "External RF interference",
        ],
        real_world_nonidealities=[
            "ADC input impedance and sampling capacitance can move the effective pole.",
            "Component tolerances shift the cutoff frequency.",
            "A single RC pole may not provide enough stop-band attenuation near Nyquist.",
        ],
        recommended_next_block="ADC driver or higher-order active anti-aliasing filter matched to the sampling rate.",
        adc_sampling_frequency_hz=4000.0,
        adc_target_cutoff_hz=500.0,
        adc_resolution_bits=12,
        adc_full_scale_voltage_v=3.3,
        adc_input_impedance_ohm=1_000_000.0,
        noise_bandwidth_hz=500.0,
        thermal_noise_resistor_ids=["R1"],
        flicker_noise_corner_hz=5.0,
        flicker_noise_component_ids=["R1"],
    ),
}


def ecg_front_end_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_ecg_front_end",
        title="BME ECG Front-End Differential Amplifier",
        analysis_type="dc_operating_point",
        topology_id="bme_ecg_front_end",
        ground_node="0",
        nodes=["0", "ecg_p", "ecg_n", "amp_plus", "amp_minus", "ecg_out"],
        components=[
            Component(id="VECGP", type="voltage_source", nodes=["ecg_p", "0"], value=1.001, unit="V"),
            Component(id="VECGN", type="voltage_source", nodes=["ecg_n", "0"], value=1.0, unit="V"),
            Component(id="RINN", type="resistor", nodes=["ecg_n", "amp_minus"], value=10_000.0, unit="ohm"),
            Component(id="RF", type="resistor", nodes=["ecg_out", "amp_minus"], value=100_000.0, unit="ohm"),
            Component(id="RINP", type="resistor", nodes=["ecg_p", "amp_plus"], value=10_000.0, unit="ohm"),
            Component(id="RREF", type="resistor", nodes=["amp_plus", "0"], value=100_000.0, unit="ohm"),
            Component(
                id="U1",
                type="ideal_op_amp",
                nodes=["amp_plus", "amp_minus", "ecg_out", "0"],
                value=0.0,
                unit="ideal",
            ),
        ],
        goals=[
            Goal(
                id="ecg_front_end_output",
                quantity="node_voltage",
                target="ecg_out",
                reference={"positive_node": "ecg_out", "negative_node": "0"},
            )
        ],
        assumptions=[
            "The electrode model is simplified to two ideal DC sources with a 1 mV differential signal.",
            "The op-amp is ideal and the matched resistor ratios set a gain of 10.",
        ],
    )


def emg_band_pass_chain_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_emg_band_pass_chain",
        title="BME EMG RC Band-Pass Chain",
        analysis_type="ac_steady_state",
        topology_id="bme_emg_band_pass_chain",
        frequency_hz=100.0,
        ground_node="0",
        nodes=["0", "in", "hp", "out"],
        components=[
            Component(
                id="VEMG",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="CHP", type="capacitor", nodes=["in", "hp"], value=1e-6, unit="F"),
            Component(id="RHP", type="resistor", nodes=["hp", "0"], value=10_000.0, unit="ohm"),
            Component(id="RLP", type="resistor", nodes=["hp", "out"], value=3180.0, unit="ohm"),
            Component(id="CLP", type="capacitor", nodes=["out", "0"], value=100e-9, unit="F"),
        ],
        goals=[
            Goal(
                id="emg_band_pass_output",
                quantity="node_voltage",
                target="out",
                reference={"positive_node": "out", "negative_node": "0"},
            )
        ],
        assumptions=[
            "The EMG chain is a passive first-order high-pass followed by a first-order low-pass.",
            "The source AC magnitude is 1 V so Vout is also the transfer magnitude at 100 Hz.",
        ],
    )


def pressure_sensor_divider_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_pressure_sensor_divider",
        title="BME Pressure Sensor Voltage Divider",
        analysis_type="dc_operating_point",
        topology_id="bme_pressure_sensor_divider",
        ground_node="0",
        nodes=["0", "vexc", "vout"],
        components=[
            Component(id="VEXC", type="voltage_source", nodes=["vexc", "0"], value=5.0, unit="V"),
            Component(id="RBIAS", type="resistor", nodes=["vexc", "vout"], value=10_000.0, unit="ohm"),
            Component(id="RPRESS", type="resistor", nodes=["vout", "0"], value=12_000.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="pressure_divider_output",
                quantity="node_voltage",
                target="vout",
                reference={"positive_node": "vout", "negative_node": "0"},
            )
        ],
        assumptions=["The pressure sensor is represented by a resistance of 12 kOhm at this operating point."],
    )


def pressure_sensor_bridge_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_pressure_sensor_bridge",
        title="BME Pressure Sensor Bridge",
        analysis_type="dc_operating_point",
        topology_id="bme_pressure_sensor_bridge",
        ground_node="0",
        nodes=["0", "vexc", "sense_p", "sense_n"],
        components=[
            Component(id="VEXC", type="voltage_source", nodes=["vexc", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["vexc", "sense_p"], value=3500.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["sense_p", "0"], value=3500.0, unit="ohm"),
            Component(id="R3", type="resistor", nodes=["vexc", "sense_n"], value=3500.0, unit="ohm"),
            Component(id="R4", type="resistor", nodes=["sense_n", "0"], value=3600.0, unit="ohm"),
        ],
        goals=[
            Goal(id="pressure_bridge_p", quantity="node_voltage", target="sense_p"),
            Goal(id="pressure_bridge_n", quantity="node_voltage", target="sense_n"),
            Goal(
                id="pressure_bridge_differential",
                quantity="component_voltage",
                target="R4",
                reference={"positive_node": "sense_n", "negative_node": "sense_p"},
            ),
        ],
        assumptions=["The active pressure-sensor arm is modeled as 3.6 kOhm while the other arms are 3.5 kOhm."],
    )


def strain_gauge_wheatstone_bridge_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_strain_gauge_wheatstone",
        title="BME Strain Gauge Wheatstone Bridge",
        analysis_type="dc_operating_point",
        topology_id="bme_strain_gauge_wheatstone",
        ground_node="0",
        nodes=["0", "vexc", "sense_p", "sense_n"],
        components=[
            Component(id="VEXC", type="voltage_source", nodes=["vexc", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["vexc", "sense_p"], value=1000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["sense_p", "0"], value=1000.0, unit="ohm"),
            Component(id="R3", type="resistor", nodes=["vexc", "sense_n"], value=1000.0, unit="ohm"),
            Component(id="RG", type="resistor", nodes=["sense_n", "0"], value=1002.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="strain_bridge_output",
                quantity="component_voltage",
                target="RG",
                reference={"positive_node": "sense_n", "negative_node": "sense_p"},
            )
        ],
        assumptions=["Only one bridge arm changes with strain; lead resistance and excitation noise are ignored."],
    )


def thermistor_divider_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_thermistor_divider",
        title="BME Thermistor Divider",
        analysis_type="dc_operating_point",
        topology_id="bme_thermistor_divider",
        ground_node="0",
        nodes=["0", "vexc", "vtemp"],
        components=[
            Component(id="VEXC", type="voltage_source", nodes=["vexc", "0"], value=5.0, unit="V"),
            Component(id="RFIXED", type="resistor", nodes=["vexc", "vtemp"], value=10_000.0, unit="ohm"),
            Component(id="RTH", type="resistor", nodes=["vtemp", "0"], value=12_000.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="thermistor_voltage",
                quantity="node_voltage",
                target="vtemp",
                reference={"positive_node": "vtemp", "negative_node": "0"},
            )
        ],
        assumptions=["The thermistor is represented by its resistance at one temperature point."],
    )


def photodiode_transimpedance_amplifier_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_photodiode_tia",
        title="BME Photodiode Transimpedance Amplifier",
        analysis_type="dc_operating_point",
        topology_id="bme_photodiode_tia",
        ground_node="0",
        nodes=["0", "sum", "out"],
        components=[
            Component(id="IPD", type="current_source", nodes=["sum", "0"], value=10e-6, unit="A"),
            Component(id="RF", type="resistor", nodes=["out", "sum"], value=1_000_000.0, unit="ohm"),
            Component(
                id="U1",
                type="ideal_op_amp",
                nodes=["0", "sum", "out", "0"],
                value=0.0,
                unit="ideal",
            ),
        ],
        goals=[
            Goal(id="tia_output", quantity="node_voltage", target="out"),
            Goal(id="photodiode_current", quantity="component_current", target="IPD"),
        ],
        assumptions=[
            "The photodiode is modeled as an ideal 10 uA current source.",
            "The op-amp is ideal and unsaturated.",
        ],
    )


def instrumentation_amplifier_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_instrumentation_amplifier",
        title="BME Instrumentation Amplifier",
        analysis_type="dc_operating_point",
        topology_id="bme_instrumentation_amplifier",
        ground_node="0",
        nodes=[
            "0",
            "sensor_p",
            "sensor_n",
            "inv_p",
            "inv_n",
            "stage_p",
            "stage_n",
            "diff_plus",
            "diff_minus",
            "inst_out",
        ],
        components=[
            Component(id="VSENP", type="voltage_source", nodes=["sensor_p", "0"], value=1.001, unit="V"),
            Component(id="VSENN", type="voltage_source", nodes=["sensor_n", "0"], value=1.0, unit="V"),
            Component(id="U1", type="ideal_op_amp", nodes=["sensor_p", "inv_p", "stage_p", "0"], value=0.0, unit="ideal"),
            Component(id="U2", type="ideal_op_amp", nodes=["sensor_n", "inv_n", "stage_n", "0"], value=0.0, unit="ideal"),
            Component(id="R1", type="resistor", nodes=["stage_p", "inv_p"], value=10_000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["stage_n", "inv_n"], value=10_000.0, unit="ohm"),
            Component(id="RG", type="resistor", nodes=["inv_p", "inv_n"], value=2000.0, unit="ohm"),
            Component(id="R3", type="resistor", nodes=["stage_n", "diff_minus"], value=10_000.0, unit="ohm"),
            Component(id="R4", type="resistor", nodes=["inst_out", "diff_minus"], value=10_000.0, unit="ohm"),
            Component(id="R5", type="resistor", nodes=["stage_p", "diff_plus"], value=10_000.0, unit="ohm"),
            Component(id="R6", type="resistor", nodes=["diff_plus", "0"], value=10_000.0, unit="ohm"),
            Component(id="U3", type="ideal_op_amp", nodes=["diff_plus", "diff_minus", "inst_out", "0"], value=0.0, unit="ideal"),
        ],
        goals=[
            Goal(
                id="instrumentation_amp_output",
                quantity="node_voltage",
                target="inst_out",
                reference={"positive_node": "inst_out", "negative_node": "0"},
            )
        ],
        assumptions=[
            "The three-op-amp instrumentation amplifier is ideal.",
            "The first-stage gain is 1 + 2R/RG with R = 10 kOhm and RG = 2 kOhm.",
        ],
    )


def anti_aliasing_rc_low_pass_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bme_anti_aliasing_low_pass",
        title="BME Anti-Aliasing RC Low-Pass",
        analysis_type="ac_steady_state",
        topology_id="bme_anti_aliasing_low_pass",
        frequency_hz=1000.0,
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="VADC",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=3180.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["out", "0"], value=100e-9, unit="F"),
        ],
        goals=[
            Goal(
                id="anti_aliasing_output",
                quantity="node_voltage",
                target="out",
                reference={"positive_node": "out", "negative_node": "0"},
            )
        ],
        assumptions=["The 1 V AC source makes Vout equal to the low-pass transfer value at 1 kHz."],
    )


BME_PROBLEM_FACTORIES: dict[str, Callable[[], CircuitProblem]] = {
    "bme_ecg_front_end": ecg_front_end_problem,
    "bme_emg_band_pass_chain": emg_band_pass_chain_problem,
    "bme_pressure_sensor_divider": pressure_sensor_divider_problem,
    "bme_pressure_sensor_bridge": pressure_sensor_bridge_problem,
    "bme_strain_gauge_wheatstone": strain_gauge_wheatstone_bridge_problem,
    "bme_thermistor_divider": thermistor_divider_problem,
    "bme_photodiode_tia": photodiode_transimpedance_amplifier_problem,
    "bme_instrumentation_amplifier": instrumentation_amplifier_problem,
    "bme_anti_aliasing_low_pass": anti_aliasing_rc_low_pass_problem,
}


def _with_bme_metadata(circuit: CircuitProblem) -> CircuitProblem:
    metadata = BME_TEMPLATE_METADATA[circuit.id]
    return circuit.model_copy(
        deep=True,
        update={
            "assumptions": list(metadata.assumptions),
            "bme_metadata": metadata,
        },
    )


def build_bme_template(template_id: str) -> BMETemplate:
    metadata = BME_TEMPLATE_METADATA[template_id]
    circuit = _with_bme_metadata(BME_PROBLEM_FACTORIES[template_id]())
    return BMETemplate(
        circuit_problem=circuit,
        biomedical_context=metadata.biomedical_context,
        signal_chain_role=metadata.signal_chain_role,
        assumptions=list(metadata.assumptions),
        what_students_should_learn=list(metadata.what_students_should_learn),
        common_lab_mistakes=list(metadata.common_lab_mistakes),
        typical_signal_range=metadata.typical_signal_range,
        safety_note=metadata.safety_note,
        noise_sources=list(metadata.noise_sources),
        real_world_nonidealities=list(metadata.real_world_nonidealities),
        recommended_next_block=metadata.recommended_next_block,
        nominal_supply_rails_v=dict(metadata.nominal_supply_rails_v)
        if metadata.nominal_supply_rails_v is not None
        else None,
        supply_positive_v=metadata.supply_positive_v,
        supply_negative_v=metadata.supply_negative_v,
        output_swing_margin_v=metadata.output_swing_margin_v,
        adc_sampling_frequency_hz=metadata.adc_sampling_frequency_hz,
        adc_target_cutoff_hz=metadata.adc_target_cutoff_hz,
        adc_resolution_bits=metadata.adc_resolution_bits,
        adc_full_scale_voltage_v=metadata.adc_full_scale_voltage_v,
        adc_input_impedance_ohm=metadata.adc_input_impedance_ohm,
        noise_bandwidth_hz=metadata.noise_bandwidth_hz,
        thermal_noise_temperature_k=metadata.thermal_noise_temperature_k,
        thermal_noise_resistor_ids=list(metadata.thermal_noise_resistor_ids),
        photodiode_shot_noise_current_id=metadata.photodiode_shot_noise_current_id,
        op_amp_input_noise_nv_per_sqrt_hz=metadata.op_amp_input_noise_nv_per_sqrt_hz,
        flicker_noise_corner_hz=metadata.flicker_noise_corner_hz,
        flicker_noise_component_ids=list(metadata.flicker_noise_component_ids),
        cmrr_mismatch_percent=metadata.cmrr_mismatch_percent,
        cmrr_mismatch_component_id=metadata.cmrr_mismatch_component_id,
    )


def _bme_template_factory(template_id: str) -> Callable[[], BMETemplate]:
    return lambda: build_bme_template(template_id)


BME_TEMPLATE_FACTORIES: dict[str, Callable[[], BMETemplate]] = {
    template_id: _bme_template_factory(template_id)
    for template_id in BME_PROBLEM_FACTORIES
}


BME_TEMPLATE_TEXTS: dict[str, str] = {
    "bme_ecg_front_end": ECG_FRONT_END_TEXT,
    "bme_emg_band_pass_chain": EMG_BAND_PASS_TEXT,
    "bme_pressure_sensor_divider": PRESSURE_SENSOR_DIVIDER_TEXT,
    "bme_pressure_sensor_bridge": PRESSURE_SENSOR_BRIDGE_TEXT,
    "bme_strain_gauge_wheatstone": STRAIN_GAUGE_BRIDGE_TEXT,
    "bme_thermistor_divider": THERMISTOR_DIVIDER_TEXT,
    "bme_photodiode_tia": PHOTODIODE_TIA_TEXT,
    "bme_instrumentation_amplifier": INSTRUMENTATION_AMPLIFIER_TEXT,
    "bme_anti_aliasing_low_pass": ANTI_ALIASING_LOW_PASS_TEXT,
}


def get_bme_demo_examples() -> list[dict[str, object]]:
    return [
        template.model_dump(exclude={"circuit_problem"})
        | {
            "id": template_id,
            "title": template.circuit_problem.title,
            "problem_text": BME_TEMPLATE_TEXTS[template_id],
        }
        for template_id in BME_TEMPLATE_FACTORIES
        for template in [BME_TEMPLATE_FACTORIES[template_id]()]
    ]
