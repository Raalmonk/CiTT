from app.models.circuit_ir import Goal
from app.services.demo_parser import voltage_divider_problem
from app.services.validator import validate_circuit


def test_validator_rejects_negative_resistor():
    circuit = voltage_divider_problem()
    circuit.components[1].value = -1000.0

    result = validate_circuit(circuit)

    assert not result.valid
    assert any("positive value" in error for error in result.errors)


def test_validator_rejects_missing_goal_target():
    circuit = voltage_divider_problem()
    circuit.goals.append(
        Goal(id="missing_goal", quantity="component_current", target="R99")
    )

    result = validate_circuit(circuit)

    assert not result.valid
    assert any("missing component" in error for error in result.errors)

