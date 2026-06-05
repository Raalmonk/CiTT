import pytest

from app.models.circuit_ir import ACSweep, CircuitProblem, Component, Goal
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
