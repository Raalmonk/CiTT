from __future__ import annotations

from collections.abc import Callable

from app.models.circuit_ir import CircuitProblem, Component, Goal


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


BME_TEMPLATE_FACTORIES: dict[str, Callable[[], CircuitProblem]] = {
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


def get_bme_demo_examples() -> list[dict[str, str]]:
    return [
        {
            "id": template_id,
            "title": BME_TEMPLATE_FACTORIES[template_id]().title,
            "problem_text": BME_TEMPLATE_TEXTS[template_id],
        }
        for template_id in BME_TEMPLATE_FACTORIES
    ]


def parse_bme_template(problem_text: str) -> CircuitProblem | None:
    lowered = " ".join(problem_text.lower().split())
    if "ecg" in lowered and ("front-end" in lowered or "front end" in lowered):
        return ecg_front_end_problem()
    if "emg" in lowered and ("band-pass" in lowered or "band pass" in lowered):
        return emg_band_pass_chain_problem()
    if "pressure" in lowered and "divider" in lowered:
        return pressure_sensor_divider_problem()
    if "pressure" in lowered and "bridge" in lowered:
        return pressure_sensor_bridge_problem()
    if "strain" in lowered and ("wheatstone" in lowered or "bridge" in lowered):
        return strain_gauge_wheatstone_bridge_problem()
    if "thermistor" in lowered and "divider" in lowered:
        return thermistor_divider_problem()
    if "photodiode" in lowered and ("transimpedance" in lowered or "tia" in lowered):
        return photodiode_transimpedance_amplifier_problem()
    if "instrumentation amplifier" in lowered:
        return instrumentation_amplifier_problem()
    if "anti-aliasing" in lowered or "anti aliasing" in lowered:
        return anti_aliasing_rc_low_pass_problem()
    return None
