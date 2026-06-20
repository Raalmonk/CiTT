from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.demo_parser import bridge_network_problem, voltage_divider_problem
from app.services.pipeline import solve_circuit
from app.services.visual_layout import build_visual_circuit


def _assert_focus_ids_exist(circuit, packet):
    component_ids = {component.id for component in circuit.components}
    node_ids = set(circuit.nodes)
    goal_ids = {goal.id for goal in circuit.goals}

    for step in packet.guided_steps:
        assert set(step.focus.components) <= component_ids
        assert set(step.focus.current_paths) <= component_ids
        assert set(step.focus.nodes) <= node_ids
        assert set(step.focus.goals) <= goal_ids


def _assert_focus_ids_query_visual_layout(circuit, packet):
    layout = build_visual_circuit(circuit)
    component_ids = {component.id for component in layout.components}
    node_ids = {node.id for node in layout.nodes}
    wire_component_ids = {wire.component_id for wire in layout.wires if wire.component_id}

    for step in packet.guided_steps:
        for component_id in step.focus.components:
            assert component_id in component_ids, (step.id, component_id)
        for node_id in step.focus.nodes:
            assert node_id in node_ids, (step.id, node_id)
        for component_id in step.focus.current_paths:
            assert component_id in component_ids or component_id in wire_component_ids, (step.id, component_id)


def test_voltage_divider_packet_includes_guided_steps():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit)

    assert [step.id for step in packet.guided_steps] == [
        "divider_reference",
        "divider_series_path",
        "divider_output",
        "verification_boundary",
    ]
    assert packet.guided_steps[2].focus.components == ["R2"]
    assert packet.guided_steps[2].focus.nodes == ["n2", "0"]
    assert packet.guided_steps[2].look_at
    assert packet.guided_steps[2].why_it_matters
    assert packet.guided_steps[2].common_mistake
    assert any(value.id == "voltage_across_R2" for value in packet.guided_steps[2].verified_values)
    _assert_focus_ids_exist(circuit, packet)


def test_bridge_network_uses_coupled_node_steps_not_divider_shortcut():
    circuit = bridge_network_problem()
    packet = solve_circuit(circuit)

    step_ids = [step.id for step in packet.guided_steps]
    assert step_ids[:3] == [
        "dc_sources_and_ground",
        "dc_coupled_node_map",
        "dc_target_kcl_neighborhood",
    ]
    assert "divider_series_path" not in step_ids

    coupled_step = next(step for step in packet.guided_steps if step.id == "dc_coupled_node_map")
    assert "R5" in coupled_step.focus.components
    assert set(coupled_step.focus.nodes) >= {"n2", "n3"}
    assert coupled_step.look_at
    assert coupled_step.why_it_matters
    assert coupled_step.common_mistake

    answer_step = next(step for step in packet.guided_steps if step.id == "dc_requested_answer")
    assert set(answer_step.focus.goals) == {"n2_voltage", "n3_voltage", "R5_current"}
    assert any(value.id == "R5_current" for value in answer_step.verified_values)
    _assert_focus_ids_exist(circuit, packet)
    _assert_focus_ids_query_visual_layout(circuit, packet)


def test_ecg_template_guided_steps_teach_diff_common_mode_and_output():
    circuit = BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem
    packet = solve_circuit(circuit)

    step_ids = [step.id for step in packet.guided_steps]
    assert "differential_sources" in step_ids
    assert "differential_output" in step_ids
    assert "bme_context_boundary" in step_ids
    diff_step = next(step for step in packet.guided_steps if step.id == "differential_sources")
    output_step = next(step for step in packet.guided_steps if step.id == "differential_output")

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


def test_guided_focus_ids_query_visual_layout_for_polished_demos():
    circuits = [
        voltage_divider_problem(),
        BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem,
        BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem,
        BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem,
    ]

    for circuit in circuits:
        packet = solve_circuit(circuit)

        _assert_focus_ids_query_visual_layout(circuit, packet)


def test_renamed_voltage_divider_uses_structure_not_topology_script():
    circuit = CircuitProblem(
        id="renamed_divider",
        title="Renamed Divider",
        analysis_type="dc_operating_point",
        topology_id=None,
        ground_node="gnd",
        nodes=["gnd", "vin", "sense"],
        components=[
            Component(id="VSUPPLY", type="voltage_source", nodes=["vin", "gnd"], value=12.0, unit="V"),
            Component(id="R_TOP", type="resistor", nodes=["vin", "sense"], value=3000.0, unit="ohm"),
            Component(id="R_BOTTOM", type="resistor", nodes=["sense", "gnd"], value=1000.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="sense_voltage",
                quantity="node_voltage",
                target="sense",
                reference={"positive_node": "sense", "negative_node": "gnd"},
            )
        ],
    )
    packet = solve_circuit(circuit)

    assert [step.id for step in packet.guided_steps][:3] == [
        "divider_reference",
        "divider_series_path",
        "divider_output",
    ]
    output_step = next(step for step in packet.guided_steps if step.id == "divider_output")
    assert output_step.focus.components == ["R_BOTTOM"]
    assert output_step.focus.nodes == ["sense", "gnd"]
    assert output_step.focus.goals == ["sense_voltage"]
    _assert_focus_ids_exist(circuit, packet)


def test_unrelated_divider_motif_does_not_steal_generic_target():
    circuit = CircuitProblem(
        id="mixed_network_loaded_branch",
        title="Mixed Network Loaded Branch",
        analysis_type="dc_operating_point",
        topology_id=None,
        ground_node="0",
        nodes=["0", "rail", "sense", "loaded"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["rail", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["rail", "sense"], value=1000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["sense", "0"], value=2000.0, unit="ohm"),
            Component(id="R3", type="resistor", nodes=["rail", "loaded"], value=1500.0, unit="ohm"),
            Component(id="R4", type="resistor", nodes=["loaded", "0"], value=2500.0, unit="ohm"),
            Component(id="Iload", type="current_source", nodes=["loaded", "0"], value=0.001, unit="A"),
        ],
        goals=[
            Goal(
                id="loaded_voltage",
                quantity="node_voltage",
                target="loaded",
                reference={"positive_node": "loaded", "negative_node": "0"},
            )
        ],
    )
    packet = solve_circuit(circuit)

    step_ids = [step.id for step in packet.guided_steps]
    assert "dc_node_relationships" in step_ids
    assert "divider_series_path" not in step_ids
    target_step = next(step for step in packet.guided_steps if step.id == "dc_target_neighborhood")
    assert "Iload" in target_step.focus.components
    assert target_step.focus.goals == ["loaded_voltage"]
    _assert_focus_ids_exist(circuit, packet)


def test_renamed_rc_low_pass_uses_structure_not_topology_script():
    circuit = CircuitProblem(
        id="custom_antialias_stage",
        title="Custom Sensor Filter",
        analysis_type="ac_steady_state",
        topology_id=None,
        frequency_hz=1000.0,
        ground_node="ref",
        nodes=["ref", "drive", "adc_in"],
        components=[
            Component(
                id="VSIG",
                type="voltage_source",
                nodes=["drive", "ref"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="RSER", type="resistor", nodes=["drive", "adc_in"], value=3180.0, unit="ohm"),
            Component(id="CSHUNT", type="capacitor", nodes=["adc_in", "ref"], value=100e-9, unit="F"),
        ],
        goals=[
            Goal(
                id="adc_input_phasor",
                quantity="node_voltage",
                target="adc_in",
                reference={"positive_node": "adc_in", "negative_node": "ref"},
            )
        ],
    )
    packet = solve_circuit(circuit)

    assert [step.id for step in packet.guided_steps][:3] == [
        "ac_source_frequency",
        "ac_low_pass_pole",
        "ac_output_phasor",
    ]
    pole_step = next(step for step in packet.guided_steps if step.id == "ac_low_pass_pole")
    assert pole_step.focus.components == ["RSER", "CSHUNT"]
    assert pole_step.focus.nodes == ["adc_in", "ref"]
    assert any(value.id == "low_pass_cutoff_frequency" for value in pole_step.verified_values)
    _assert_focus_ids_exist(circuit, packet)
