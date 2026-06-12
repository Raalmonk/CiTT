import pytest

from app.models.circuit_ir import Goal
from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import (
    op_amp_non_inverting_problem,
    rc_low_pass_sweep_problem,
    voltage_divider_problem,
)
from app.services.pipeline import solve_circuit
from app.services.validator import validate_circuit
from app.services.variant_generator import (
    generate_goal_variant,
    generate_value_variant,
    generate_value_variants,
    generate_variants,
)


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


def test_ac_sweep_value_variant_changes_capacitor_source_and_sweep_range():
    original = rc_low_pass_sweep_problem()
    variant = generate_value_variant(original)
    packet = solve_circuit(variant)

    original_components = {component.id: component for component in original.components}
    variant_components = {component.id: component for component in variant.components}

    assert variant_components["C1"].value != original_components["C1"].value
    assert variant_components["V1"].ac_magnitude != original_components["V1"].ac_magnitude
    assert variant.sweep is not None
    assert original.sweep is not None
    assert variant.sweep.start_hz != original.sweep.start_hz
    assert variant.sweep.stop_hz != original.sweep.stop_hz
    assert packet.status == "solved"
    assert packet.verification.passed


def test_bme_value_variants_change_sensor_or_signal_chain_parameters():
    cases = {
        "bme_pressure_sensor_divider": {"RPRESS": 14_000.0},
        "bme_pressure_sensor_bridge": {"R4": 3700.0},
        "bme_strain_gauge_wheatstone": {"RG": 1005.0},
        "bme_thermistor_divider": {"RTH": 8000.0},
        "bme_photodiode_tia": {"IPD": 20e-6},
        "bme_anti_aliasing_low_pass": {"R1": 1590.0},
        "bme_emg_band_pass_chain": {"RHP": 6800.0},
        "bme_instrumentation_amplifier": {"RG": 1000.0},
    }

    for template_id, expected_values in cases.items():
        problem = BME_TEMPLATE_FACTORIES[template_id]().circuit_problem
        variant = generate_value_variant(problem)
        components = {component.id: component for component in variant.components}
        packet = solve_circuit(variant)

        assert variant.bme_metadata is not None
        assert any("biomedical parameter changed" in assumption for assumption in variant.assumptions)
        for component_id, expected_value in expected_values.items():
            assert components[component_id].value == pytest.approx(expected_value)
        assert packet.status == "solved", template_id
        assert packet.verification_badge.label == "PASS", template_id


def test_bme_variants_expose_student_facing_what_if_prompts():
    problem = BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem

    variants = generate_value_variants(problem)
    all_variants = generate_variants(problem)

    prompts = [str(variant["prompt"]) for variant in variants]
    assert "What if cutoff frequency increases?" in prompts
    assert "What if cutoff frequency decreases?" in prompts
    assert len(variants) == 2
    assert len(all_variants) == 3
    assert all(variant["kind"] == "bme_what_if" for variant in variants)


def test_bme_photodiode_variant_doubles_photocurrent():
    problem = BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem
    variants = generate_value_variants(problem)

    doubled = next(
        variant for variant in variants if variant["prompt"] == "What if photocurrent doubles?"
    )
    components = {
        component["id"]: component
        for component in doubled["circuit_ir"]["components"]
    }

    assert components["IPD"]["value"] == pytest.approx(20e-6)


def test_goal_variant_uses_ideal_op_amp_output_reference():
    problem = op_amp_non_inverting_problem()
    problem.goals = [
        Goal(id="vp_voltage", quantity="node_voltage", target="vp"),
        Goal(id="vm_voltage", quantity="node_voltage", target="vm"),
        Goal(id="out_voltage", quantity="node_voltage", target="out"),
        Goal(id="V1_voltage", quantity="component_voltage", target="V1"),
        Goal(id="V1_current", quantity="component_current", target="V1"),
        Goal(id="V1_power", quantity="component_power", target="V1"),
        Goal(id="V1_source_power", quantity="source_power", target="V1"),
        Goal(id="Rg_voltage", quantity="component_voltage", target="Rg"),
        Goal(id="Rg_current", quantity="component_current", target="Rg"),
        Goal(id="Rg_power", quantity="component_power", target="Rg"),
        Goal(id="Rf_voltage", quantity="component_voltage", target="Rf"),
        Goal(id="Rf_current", quantity="component_current", target="Rf"),
        Goal(id="Rf_power", quantity="component_power", target="Rf"),
    ]

    variant = generate_goal_variant(problem)
    packet = solve_circuit(variant)
    goal = variant.goals[0]

    assert goal.id == "U1_output_voltage"
    assert goal.reference == {"positive_node": "out", "negative_node": "0"}
    assert packet.status == "solved"
    assert packet.verification.passed
