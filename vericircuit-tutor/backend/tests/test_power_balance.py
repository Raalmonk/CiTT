import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_parser import (
    bridge_network_alt_problem,
    bridge_network_problem,
    current_divider_problem,
    voltage_divider_problem,
)
from app.services.pipeline import solve_circuit


client = TestClient(app)


def test_power_balance_passes_for_solved_circuits():
    for circuit in [
        voltage_divider_problem(),
        current_divider_problem(),
        bridge_network_problem(),
        bridge_network_alt_problem(),
    ]:
        packet = solve_circuit(circuit)

        assert packet.status == "solved"
        assert packet.verification.passed
        assert packet.verification.power_balance_error_w <= 1e-8


def test_second_bridge_network_values_are_stable():
    circuit = bridge_network_alt_problem()
    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["a"] == pytest.approx(5.084264832330181)
    assert packet.node_voltages["b"] == pytest.approx(3.637145313843508)
    assert packet.component_results["R5"].current.value == pytest.approx(
        0.00043852106620808273
    )


def test_incremental_resistor_update_uses_rank_one_solver():
    circuit = voltage_divider_problem()

    response = client.post(
        "/incremental_resistor_update",
        json={
            "circuit_ir": circuit.model_dump(),
            "component_id": "R2",
            "new_value": 4000.0,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["incremental_used"] is True
    packet = payload["solution_packet"]
    assert packet["verification_badge"]["label"] == "PASS"
    assert packet["calculation_trace"]["answer_source"] == "incremental_solver"
    assert packet["requested_answers"]["voltage_across_R2"]["value"] == pytest.approx(
        10.0 * 4000.0 / 6000.0
    )
