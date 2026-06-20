import pytest

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.bme_templates import anti_aliasing_rc_low_pass_problem
from app.services.demo_parser import diode_limiter_problem
from app.services.pipeline import solve_circuit


def test_dc_diode_uses_newton_raphson_operating_point():
    circuit = CircuitProblem(
        id="diode_limiter_dc",
        title="Diode limiter DC operating point",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0", "vin", "vout"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["vin", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["vin", "vout"], value=1000.0, unit="ohm"),
            Component(
                id="D1",
                type="diode",
                nodes=["vout", "0"],
                value=0.0,
                unit="model",
                saturation_current_a=1e-12,
                emission_coefficient=1.0,
                thermal_voltage_v=0.025852,
            ),
        ],
        goals=[
            Goal(id="vout", quantity="node_voltage", target="vout"),
            Goal(id="diode_current", quantity="component_current", target="D1"),
        ],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.calculation_trace.answer_source == "nonlinear_solver"
    assert packet.calculation_trace.solver_method.startswith("Newton-Raphson")
    assert packet.node_voltages["vout"] == pytest.approx(0.574, rel=2e-2)
    assert packet.component_results["D1"].current.value == pytest.approx(
        packet.component_results["R1"].current.value,
        rel=1e-6,
    )


def test_diode_limiter_fixture_solves():
    circuit = diode_limiter_problem()

    packet = solve_circuit(circuit)

    assert circuit.id == "diode_limiter_dc"
    assert packet.verification_badge.label == "PASS"
    assert packet.calculation_trace.answer_source == "nonlinear_solver"


def test_nonideal_op_amp_output_resistance_macromodel_loads_output():
    circuit = CircuitProblem(
        id="op_amp_output_resistance",
        title="Nonideal op-amp output resistance macromodel",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0", "inp", "out"],
        components=[
            Component(id="VIN", type="voltage_source", nodes=["inp", "0"], value=1.0, unit="V"),
            Component(id="RL", type="resistor", nodes=["out", "0"], value=100.0, unit="ohm"),
            Component(
                id="U1",
                type="nonideal_op_amp",
                nodes=["inp", "0", "out", "0"],
                value=10.0,
                unit="model",
                output_resistance_ohm=100.0,
            ),
        ],
        goals=[Goal(id="vout", quantity="node_voltage", target="out")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["out"] == pytest.approx(5.0)
    assert packet.component_results["U1"].current.value == pytest.approx(-0.05)
    assert any(
        observation.id == "U1_output_resistance"
        for observation in packet.tutor_observations
    )


def test_bme_noise_budget_propagates_sources_to_output_rms():
    circuit = anti_aliasing_rc_low_pass_problem()

    packet = solve_circuit(circuit)

    assert packet.verification_badge.label == "PASS"
    output_noise = next(
        observation
        for observation in packet.tutor_observations
        if observation.id == "output_integrated_noise_rms"
    )
    resistor_noise = next(
        observation
        for observation in packet.tutor_observations
        if observation.id == "output_noise_from_R1"
    )
    assert output_noise.value is not None and output_noise.value > 0
    assert resistor_noise.value is not None and resistor_noise.value > 0
    assert "complex MNA" in output_noise.note
