from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import voltage_divider_problem
from app.services.pipeline import solve_circuit


def _assert_focus_ids_exist(circuit, packet):
    component_ids = {component.id for component in circuit.components}
    node_ids = set(circuit.nodes)
    goal_ids = {goal.id for goal in circuit.goals}

    for step in packet.guided_steps:
        assert set(step.focus.components) <= component_ids
        assert set(step.focus.current_paths) <= component_ids
        assert set(step.focus.nodes) <= node_ids
        assert set(step.focus.goals) <= goal_ids


def test_voltage_divider_packet_includes_guided_steps():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit)

    assert [step.id for step in packet.guided_steps] == [
        "voltage_divider_reference",
        "voltage_divider_series_current",
        "voltage_divider_output",
        "voltage_divider_verification_boundary",
    ]
    assert packet.guided_steps[2].focus.components == ["R2"]
    assert packet.guided_steps[2].focus.nodes == ["n2", "0"]
    assert any(value.id == "voltage_across_R2" for value in packet.guided_steps[2].verified_values)
    _assert_focus_ids_exist(circuit, packet)


def test_ecg_template_guided_steps_teach_diff_common_mode_and_output():
    circuit = BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem
    packet = solve_circuit(circuit)

    step_ids = [step.id for step in packet.guided_steps]
    assert "ecg_diff_common_mode" in step_ids
    assert "ecg_output" in step_ids
    diff_step = next(step for step in packet.guided_steps if step.id == "ecg_diff_common_mode")
    output_step = next(step for step in packet.guided_steps if step.id == "ecg_output")

    assert diff_step.focus.components == ["VECGP", "VECGN"]
    assert {value.id for value in diff_step.verified_values} >= {
        "differential_input_voltage",
        "common_mode_input_voltage",
    }
    assert output_step.focus.nodes == ["ecg_out"]
    assert any(value.id == "ecg_front_end_output" for value in output_step.verified_values)
    _assert_focus_ids_exist(circuit, packet)


def test_first_bme_guided_templates_have_deterministic_steps():
    for template_id in ["bme_anti_aliasing_low_pass", "bme_photodiode_tia"]:
        circuit = BME_TEMPLATE_FACTORIES[template_id]().circuit_problem
        packet = solve_circuit(circuit)

        assert packet.guided_steps, template_id
        assert all(step.title and step.body for step in packet.guided_steps)
        _assert_focus_ids_exist(circuit, packet)
