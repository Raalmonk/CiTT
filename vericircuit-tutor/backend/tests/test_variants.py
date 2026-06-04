from app.services.demo_parser import voltage_divider_problem
from app.services.pipeline import solve_circuit
from app.services.validator import validate_circuit
from app.services.variant_generator import generate_goal_variant, generate_value_variant


def test_value_variant_is_valid_and_solves():
    variant = generate_value_variant(voltage_divider_problem())
    validation = validate_circuit(variant)
    packet = solve_circuit(variant)

    assert validation.valid
    assert packet.status == "solved"
    assert packet.verification.passed
    assert variant.components[1].value != 2000.0


def test_goal_variant_is_valid_and_solves():
    variant = generate_goal_variant(voltage_divider_problem())
    validation = validate_circuit(variant)
    packet = solve_circuit(variant)

    assert validation.valid
    assert packet.status == "solved"
    assert packet.verification.passed
    assert len(packet.requested_answers) == 1

