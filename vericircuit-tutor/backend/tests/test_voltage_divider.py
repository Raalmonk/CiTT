import pytest

from app.services.demo_parser import VOLTAGE_DIVIDER_TEXT
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


def test_voltage_divider_solution():
    circuit = parse_problem(VOLTAGE_DIVIDER_TEXT).circuit
    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.verification.passed
    assert packet.node_voltages["n1"] == pytest.approx(10.0)
    assert packet.node_voltages["n2"] == pytest.approx(6.0)
    assert packet.component_results["R1"].current.value == pytest.approx(0.002)
    assert packet.component_results["R2"].current.value == pytest.approx(0.002)
    assert packet.requested_answers["voltage_across_R2"].value == pytest.approx(6.0)
    assert packet.requested_answers["circuit_current"].value == pytest.approx(0.002)


def test_voltage_divider_kcl_residual_is_near_zero():
    circuit = parse_problem(VOLTAGE_DIVIDER_TEXT).circuit
    packet = solve_circuit(circuit)

    assert packet.verification.max_kcl_residual_a <= 1e-8
