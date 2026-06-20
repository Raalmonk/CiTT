from fastapi.testclient import TestClient

from app.main import app
from app.models.lab import LabScenario, LabSimulationRequest
from app.services.demo_parser import (
    nonideal_op_amp_problem,
    op_amp_non_inverting_problem,
    voltage_divider_problem,
)
from app.services.lab_simulator import simulate_lab
from app.services.pipeline import solve_circuit


client = TestClient(app)


def test_lab_component_error_changes_verified_answer_and_measured_readout():
    circuit = voltage_divider_problem()
    baseline = solve_circuit(circuit)

    response = simulate_lab(
        LabSimulationRequest(
            circuit_ir=circuit,
            baseline_packet=baseline,
            scenario=LabScenario(
                component_value_error_percent={"R2": 10.0},
                readout_gain_error_percent=1.0,
                readout_offset_v=0.005,
            ),
        )
    )

    answer = next(item for item in response.comparisons if item.id == "voltage_across_R2")
    assert answer.lab_value != answer.baseline_value
    assert answer.measured_value != answer.lab_value
    assert any(item.kind == "component_value" and item.target == "R2" for item in response.applied_modifications)
    assert any(item.kind == "measurement_readout" for item in response.applied_modifications)
    assert response.lab_packet.verification_badge.label == "PASS"
    assert response.sensitivity_sweeps
    assert len(response.sensitivity_sweeps[0].points) >= 5


def test_lab_op_amp_rail_limit_converts_ideal_amp_and_reports_saturation():
    circuit = op_amp_non_inverting_problem()

    response = simulate_lab(
        LabSimulationRequest(
            circuit_ir=circuit,
            scenario=LabScenario(
                op_amp_open_loop_gain=100_000.0,
                supply_positive_v=5.0,
                supply_negative_v=-5.0,
                output_swing_margin_v=0.2,
            ),
        )
    )

    op_amp = next(component for component in response.lab_circuit.components if component.id == "U1")
    assert op_amp.type == "nonideal_op_amp"
    assert response.lab_packet.node_voltages["out"] == 4.8
    assert any("saturated" in warning.lower() for warning in response.lab_packet.warnings)
    assert any(observation.id == "op_amp_saturation" for observation in response.observations)


def test_lab_bias_compensation_adds_balance_resistor_and_teaching_observation():
    circuit = nonideal_op_amp_problem()

    response = simulate_lab(
        LabSimulationRequest(
            circuit_ir=circuit,
            scenario=LabScenario(
                op_amp_input_bias_current_a=50e-9,
                enable_bias_compensation=True,
            ),
        )
    )

    balance = next(
        component
        for component in response.lab_circuit.components
        if component.id.startswith("RB_U1_bias")
    )
    assert balance.type == "resistor"
    assert balance.value == 900.0
    assert any(item.kind == "bias_compensation" for item in response.applied_modifications)
    assert any(observation.id == "bias_compensation" for observation in response.observations)
    assert response.counterfactuals
    assert response.counterfactuals[0].id == "without_bias_compensation"


def test_lab_breadboard_leakage_adds_node_loads():
    circuit = voltage_divider_problem()

    response = simulate_lab(
        LabSimulationRequest(
            circuit_ir=circuit,
            scenario=LabScenario(breadboard_leakage_ohm=100_000.0),
        )
    )

    leakage_components = [
        component for component in response.lab_circuit.components if component.id.startswith("RBB_")
    ]
    assert len(leakage_components) == 2
    assert any(item.id == "breadboard_leakage" for item in response.applied_modifications)
    assert any(observation.id == "breadboard_leakage" for observation in response.observations)


def test_lab_simulate_endpoint_returns_comparison_payload():
    circuit = voltage_divider_problem()

    response = client.post(
        "/lab/simulate",
        json={
            "circuit_ir": circuit.model_dump(),
            "scenario": {
                "component_value_error_percent": {"R2": 5.0},
                "readout_offset_v": 0.01,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["lab_packet"]["verification_badge"]["label"] == "PASS"
    assert payload["comparisons"]
    assert any(item["target"] == "R2" for item in payload["applied_modifications"])
