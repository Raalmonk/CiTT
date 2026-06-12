from xml.etree import ElementTree as ET

from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import voltage_divider_problem
from app.services.pipeline import solve_circuit
from app.services.schematic_generator import render_schematic_svg


def _assert_focus_ids_exist(circuit, packet):
    component_ids = {component.id for component in circuit.components}
    node_ids = set(circuit.nodes)
    goal_ids = {goal.id for goal in circuit.goals}

    for step in packet.guided_steps:
        assert set(step.focus.components) <= component_ids
        assert set(step.focus.current_paths) <= component_ids
        assert set(step.focus.nodes) <= node_ids
        assert set(step.focus.goals) <= goal_ids


def _svg_elements(svg: str):
    root = ET.fromstring(svg)
    return list(root.iter())


def _has_component(svg_elements, component_id: str) -> bool:
    return any(element.attrib.get("data-component-id") == component_id for element in svg_elements)


def _has_node(svg_elements, node_id: str) -> bool:
    return any(element.attrib.get("data-node-id") == node_id for element in svg_elements)


def _has_current_path(svg_elements, component_id: str) -> bool:
    return any(
        element.attrib.get("data-component-id") == component_id
        and "current-path" in element.attrib.get("class", "").split()
        for element in svg_elements
    )


def _assert_focus_ids_query_svg(circuit, packet):
    svg_elements = _svg_elements(render_schematic_svg(circuit))
    for step in packet.guided_steps:
        for component_id in step.focus.components:
            assert _has_component(svg_elements, component_id), (step.id, component_id)
        for node_id in step.focus.nodes:
            assert _has_node(svg_elements, node_id), (step.id, node_id)
        for component_id in step.focus.current_paths:
            assert _has_current_path(svg_elements, component_id), (step.id, component_id)


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
    assert packet.guided_steps[2].look_at
    assert packet.guided_steps[2].why_it_matters
    assert packet.guided_steps[2].common_mistake
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
    assert diff_step.look_at
    assert diff_step.why_it_matters
    assert diff_step.common_mistake
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


def test_guided_focus_ids_query_actual_svg_elements_for_polished_demos():
    circuits = [
        voltage_divider_problem(),
        BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem,
        BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem,
        BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem,
    ]

    for circuit in circuits:
        packet = solve_circuit(circuit)

        _assert_focus_ids_query_svg(circuit, packet)
