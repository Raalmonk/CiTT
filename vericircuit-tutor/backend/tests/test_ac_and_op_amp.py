import math

import pytest

from app.models.circuit_ir import ACSweep, CircuitProblem, Component, Goal, RCTransient
from app.services.demo_parser import RC_LOW_PASS_SWEEP_TEXT, RC_TRANSIENT_TEXT, parse_demo_problem
from app.services.pipeline import solve_circuit


def test_dc_capacitor_is_open_circuit():
    circuit = CircuitProblem(
        id="dc_capacitor_open",
        title="DC Capacitor Open Circuit",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=10.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["n2", "0"], value=1e-6, unit="F"),
        ],
        goals=[
            Goal(id="n2_voltage", quantity="node_voltage", target="n2"),
            Goal(id="R1_current", quantity="component_current", target="R1"),
            Goal(id="C1_current", quantity="component_current", target="C1"),
        ],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["n2"] == pytest.approx(10.0)
    assert packet.component_results["R1"].current.value == pytest.approx(0.0)
    assert packet.component_results["C1"].current.value == pytest.approx(0.0)


def test_rc_low_pass_ac_single_frequency():
    circuit = CircuitProblem(
        id="rc_low_pass_ac",
        title="RC Low-Pass AC",
        analysis_type="ac_single_frequency",
        frequency_hz=159.154943,
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["out", "0"], value=1e-6, unit="F"),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    answer = packet.ac_requested_answers["vout"]
    assert answer.magnitude == pytest.approx(0.7071, rel=1e-3)
    assert answer.phase_deg == pytest.approx(-45.0, abs=1e-2)


def test_rc_low_pass_ac_steady_state():
    circuit = CircuitProblem(
        id="rc_low_pass_ac_steady_state",
        title="RC Low-Pass AC Steady-State",
        analysis_type="ac_steady_state",
        frequency_hz=159.154943,
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["out", "0"], value=1e-6, unit="F"),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    answer = packet.ac_requested_answers["vout"]
    assert answer.magnitude == pytest.approx(0.7071, rel=1e-3)
    assert answer.phase_deg == pytest.approx(-45.0, abs=1e-2)


def test_rc_high_pass_ac_single_frequency():
    circuit = CircuitProblem(
        id="rc_high_pass_ac",
        title="RC High-Pass AC",
        analysis_type="ac_single_frequency",
        frequency_hz=159.154943,
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="C1", type="capacitor", nodes=["in", "out"], value=1e-6, unit="F"),
            Component(id="R1", type="resistor", nodes=["out", "0"], value=1000.0, unit="ohm"),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    answer = packet.ac_requested_answers["vout"]
    assert answer.magnitude == pytest.approx(0.7071, rel=1e-3)
    assert answer.phase_deg == pytest.approx(45.0, abs=1e-2)


def test_rl_high_pass_ac_steady_state_inductor_impedance():
    circuit = CircuitProblem(
        id="rl_high_pass_ac_steady_state",
        title="RL High-Pass AC Steady-State",
        analysis_type="ac_steady_state",
        frequency_hz=159.154943,
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=1000.0, unit="ohm"),
            Component(id="L1", type="inductor", nodes=["out", "0"], value=1.0, unit="H"),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    answer = packet.ac_requested_answers["vout"]
    assert answer.magnitude == pytest.approx(0.7071, rel=1e-3)
    assert answer.phase_deg == pytest.approx(45.0, abs=1e-2)


def test_series_rlc_band_pass_ac_steady_state_at_resonance():
    circuit = CircuitProblem(
        id="series_rlc_band_pass",
        title="Series RLC Band-Pass",
        analysis_type="ac_steady_state",
        frequency_hz=159.154943,
        ground_node="0",
        nodes=["0", "in", "n1", "n2"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="C1", type="capacitor", nodes=["in", "n1"], value=1e-6, unit="F"),
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=100.0, unit="ohm"),
            Component(id="L1", type="inductor", nodes=["n2", "0"], value=1.0, unit="H"),
        ],
        goals=[
            Goal(
                id="vout",
                quantity="component_voltage",
                target="R1",
                reference={"positive_node": "n1", "negative_node": "n2"},
            )
        ],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    answer = packet.ac_requested_answers["vout"]
    assert answer.magnitude == pytest.approx(1.0, rel=1e-3)
    assert answer.phase_deg == pytest.approx(0.0, abs=1e-2)


def test_ac_sweep_low_pass_magnitude_decreases():
    circuit = CircuitProblem(
        id="rc_low_pass_sweep",
        title="RC Low-Pass Sweep",
        analysis_type="ac_sweep",
        sweep=ACSweep(start_hz=10.0, stop_hz=100_000.0, points_per_decade=10),
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["out", "0"], value=1e-6, unit="F"),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.ac_sweep
    first_mag = packet.ac_sweep[0].requested_answers["vout"].magnitude
    last_mag = packet.ac_sweep[-1].requested_answers["vout"].magnitude
    assert first_mag > last_mag


def test_ac_sweep_exposes_plot_ready_series():
    circuit = CircuitProblem(
        id="rc_low_pass_sweep_plots",
        title="RC Low-Pass Sweep Plots",
        analysis_type="ac_sweep",
        sweep=ACSweep(start_hz=10.0, stop_hz=100_000.0, points_per_decade=10),
        ground_node="0",
        nodes=["0", "in", "out"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["out", "0"], value=1e-6, unit="F"),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    answer_series = next(series for series in packet.ac_sweep_plots if series.id == "answer:vout")
    assert answer_series.source == "requested_answer"
    assert answer_series.unit == "V"
    assert len(answer_series.points) == len(packet.ac_sweep)
    assert answer_series.points[0].magnitude == pytest.approx(
        packet.ac_sweep[0].requested_answers["vout"].magnitude
    )
    assert answer_series.points[0].magnitude_db == pytest.approx(
        20.0 * math.log10(packet.ac_sweep[0].requested_answers["vout"].magnitude)
    )
    assert any(series.id == "node:out" for series in packet.ac_sweep_plots)
    assert any(series.id == "component:C1:current" for series in packet.ac_sweep_plots)


def test_demo_parser_recognizes_rc_low_pass_sweep_template():
    circuit = parse_demo_problem(RC_LOW_PASS_SWEEP_TEXT)
    packet = solve_circuit(circuit)

    assert circuit.analysis_type == "ac_sweep"
    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.ac_sweep


def test_first_order_rc_transient_template_charging():
    circuit = CircuitProblem(
        id="rc_transient_charging",
        title="First-Order RC Charging",
        analysis_type="rc_transient",
        ground_node="0",
        nodes=["0", "vin", "vc"],
        transient=RCTransient(
            capacitor_id="C1",
            initial_voltage_v=0.0,
            time_points_s=[0.001],
        ),
        components=[
            Component(id="V1", type="voltage_source", nodes=["vin", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["vin", "vc"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["vc", "0"], value=1e-6, unit="F"),
        ],
        goals=[Goal(id="capacitor_voltage", quantity="component_voltage", target="C1")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.transient_response is not None
    assert packet.transient_response.initial_voltage_v == pytest.approx(0.0)
    assert packet.transient_response.final_voltage_v == pytest.approx(5.0)
    assert packet.transient_response.resistance_ohm == pytest.approx(1000.0)
    assert packet.transient_response.time_constant_s == pytest.approx(0.001)
    assert "exp(-t/0.001)" in packet.transient_response.formula
    assert packet.requested_answers["time_constant"].value == pytest.approx(0.001)
    sample_at_tau = next(
        point for point in packet.transient_response.sample_points if abs(point.time_s - 0.001) < 1e-12
    )
    assert sample_at_tau.voltage_v == pytest.approx(5.0 * (1.0 - math.exp(-1.0)))


def test_demo_parser_recognizes_first_order_rc_transient_template():
    circuit = parse_demo_problem(RC_TRANSIENT_TEXT)
    packet = solve_circuit(circuit)

    assert circuit.analysis_type == "rc_transient"
    assert packet.status == "solved"
    assert packet.transient_response is not None
    assert packet.transient_response.time_constant_s == pytest.approx(0.001)


def test_ideal_op_amp_non_inverting_amplifier_dc():
    circuit = CircuitProblem(
        id="op_amp_non_inverting",
        title="Ideal Non-Inverting Amplifier",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0", "vp", "vm", "out"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["vp", "0"], value=1.0, unit="V"),
            Component(id="Rg", type="resistor", nodes=["vm", "0"], value=1000.0, unit="ohm"),
            Component(id="Rf", type="resistor", nodes=["out", "vm"], value=9000.0, unit="ohm"),
            Component(
                id="U1",
                type="op_amp_ideal",
                nodes=["vp", "vm", "out", "0"],
                value=0.0,
                unit="ideal",
            ),
        ],
        goals=[
            Goal(id="vout", quantity="node_voltage", target="out"),
            Goal(id="vminus", quantity="node_voltage", target="vm"),
        ],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["out"] == pytest.approx(10.0)
    assert packet.node_voltages["vm"] == pytest.approx(1.0)


def test_ideal_op_amp_type_alias_non_inverting_amplifier_dc():
    circuit = CircuitProblem(
        id="ideal_op_amp_alias",
        title="Ideal Op-Amp Type Alias",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0", "vp", "vm", "out"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["vp", "0"], value=0.5, unit="V"),
            Component(id="Rg", type="resistor", nodes=["vm", "0"], value=1000.0, unit="ohm"),
            Component(id="Rf", type="resistor", nodes=["out", "vm"], value=3000.0, unit="ohm"),
            Component(
                id="U1",
                type="ideal_op_amp",
                nodes=["vp", "vm", "out", "0"],
                value=0.0,
                unit="ideal",
            ),
        ],
        goals=[
            Goal(id="vout", quantity="node_voltage", target="out"),
            Goal(id="u1_current", quantity="component_current", target="U1"),
        ],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["out"] == pytest.approx(2.0)
    assert packet.node_voltages["vm"] == pytest.approx(0.5)
    assert packet.component_results["U1"].current.reference == {
        "from_node": "out",
        "to_node": "0",
    }


def test_nonideal_op_amp_dc_clamps_to_output_rail_window():
    circuit = parse_demo_problem(
        "Analyze an op-amp with rail saturation, slew rate, bias current, clipping recovery, "
        "output current limit, and frequency response."
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["out"] == pytest.approx(4.8)
    assert abs(packet.component_results["U1"].current.value) == pytest.approx(0.00048, rel=1e-3)
    assert any("nonideal op-amp saturated" in warning for warning in packet.warnings)
    assert any(observation.id == "U1_slew_rate" for observation in packet.tutor_observations)


def test_nonideal_op_amp_ac_gain_bandwidth_reduces_high_frequency_gain():
    def circuit_at(frequency_hz: float) -> CircuitProblem:
        return CircuitProblem(
            id=f"nonideal_op_amp_ac_{frequency_hz:g}",
            title="Nonideal Op-Amp AC",
            analysis_type="ac_steady_state",
            frequency_hz=frequency_hz,
            ground_node="0",
            nodes=["0", "vp", "vm", "out"],
            components=[
                Component(
                    id="V1",
                    type="voltage_source",
                    nodes=["vp", "0"],
                    value=0.0,
                    unit="V",
                    ac_magnitude=1.0,
                    ac_phase_deg=0.0,
                ),
                Component(id="Rg", type="resistor", nodes=["vm", "0"], value=1000.0, unit="ohm"),
                Component(id="Rf", type="resistor", nodes=["out", "vm"], value=9000.0, unit="ohm"),
                Component(
                    id="U1",
                    type="nonideal_op_amp",
                    nodes=["vp", "vm", "out", "0"],
                    value=0.0,
                    unit="model",
                    open_loop_gain=100_000.0,
                    gain_bandwidth_hz=100_000.0,
                ),
            ],
            goals=[Goal(id="vout", quantity="node_voltage", target="out")],
        )

    low_packet = solve_circuit(circuit_at(1.0))
    high_packet = solve_circuit(circuit_at(100_000.0))

    assert low_packet.verification_badge.label == "PASS"
    assert high_packet.verification_badge.label == "PASS"
    assert low_packet.ac_requested_answers["vout"].magnitude == pytest.approx(10.0, rel=1e-2)
    assert high_packet.ac_requested_answers["vout"].magnitude < 2.0


def test_unsupported_transient_request_has_no_numerical_answers():
    circuit = CircuitProblem(
        id="unsupported_transient",
        title="Unsupported Transient",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0"],
        components=[],
        goals=[],
        unsupported_features=["transient analysis"],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "unsupported"
    assert packet.verification_badge.label == "UNSUPPORTED"
    assert packet.requested_answers == {}
    assert packet.ac_requested_answers == {}


def test_open_loop_ideal_op_amp_returns_singular_feedback_message():
    circuit = CircuitProblem(
        id="op_amp_open_loop",
        title="Open-Loop Ideal Op-Amp",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0", "vp", "vm", "out"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["vp", "0"], value=1.0, unit="V"),
            Component(
                id="U1",
                type="op_amp_ideal",
                nodes=["vp", "vm", "out", "0"],
                value=0.0,
                unit="ideal",
            ),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "invalid"
    assert packet.verification_badge.label == "FAIL"
    assert "closed-loop feedback path or additional constraints" in packet.verification_badge.message
    assert packet.requested_answers == {}
