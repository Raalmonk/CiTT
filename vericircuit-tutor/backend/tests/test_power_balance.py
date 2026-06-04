import pytest

from app.services.demo_parser import (
    BRIDGE_NETWORK_ALT_TEXT,
    BRIDGE_NETWORK_TEXT,
    CURRENT_DIVIDER_TEXT,
    VOLTAGE_DIVIDER_TEXT,
)
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


def test_power_balance_passes_for_solved_circuits():
    for text in [
        VOLTAGE_DIVIDER_TEXT,
        CURRENT_DIVIDER_TEXT,
        BRIDGE_NETWORK_TEXT,
        BRIDGE_NETWORK_ALT_TEXT,
    ]:
        circuit = parse_problem(text).circuit
        packet = solve_circuit(circuit)

        assert packet.status == "solved"
        assert packet.verification.passed
        assert packet.verification.power_balance_error_w <= 1e-8


def test_second_bridge_network_values_are_stable():
    circuit = parse_problem(BRIDGE_NETWORK_ALT_TEXT).circuit
    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["a"] == pytest.approx(5.084264832330181)
    assert packet.node_voltages["b"] == pytest.approx(3.637145313843508)
    assert packet.component_results["R5"].current.value == pytest.approx(
        0.00043852106620808273
    )
