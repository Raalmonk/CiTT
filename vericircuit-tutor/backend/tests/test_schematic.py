from fastapi.testclient import TestClient

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.main import app
from app.services.demo_parser import (
    bridge_network_alt_problem,
    bridge_network_problem,
    current_divider_problem,
    voltage_divider_problem,
)
from app.services import schematic_generator
from app.services.variant_generator import generate_goal_variant, generate_value_variant


def _schematic(circuit: CircuitProblem):
    client = TestClient(app)
    return client.post("/schematic", json={"circuit_ir": circuit.model_dump()})


def test_schematic_endpoint_returns_svg_for_original_examples():
    examples = [
        (voltage_divider_problem(), "schemdraw_voltage_divider"),
        (current_divider_problem(), "schemdraw_current_divider"),
        (bridge_network_problem(), "manual_svg_bridge_network"),
        (bridge_network_alt_problem(), "manual_svg_bridge_network"),
    ]

    for circuit, renderer in examples:
        response = _schematic(circuit)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/svg+xml")
        assert response.text.lstrip().startswith("<svg")
        assert renderer in response.text
        assert "fallback_graph" not in response.text


def test_schematic_contains_component_ids_and_values():
    response = _schematic(voltage_divider_problem())

    assert response.status_code == 200
    assert "R1" in response.text
    assert "2 kΩ" in response.text
    assert "R2" in response.text
    assert "3 kΩ" in response.text
    assert "V1" in response.text
    assert "10 V" in response.text


def test_known_schematics_include_probe_metadata_and_current_paths():
    examples = [voltage_divider_problem(), current_divider_problem(), bridge_network_problem()]

    for circuit in examples:
        response = _schematic(circuit)

        assert response.status_code == 200
        for component in circuit.components:
            assert f'data-component-id="{component.id}"' in response.text
            assert f'class="current-path" data-component-id="{component.id}"' in response.text
        for node in circuit.nodes:
            assert f'data-node-id="{node}"' in response.text


def test_bridge_schematic_contains_clear_component_and_node_labels():
    response = _schematic(bridge_network_problem())

    assert response.status_code == 200
    for label in ["R1", "R2", "R3", "R4", "R5", "V1"]:
        assert label in response.text
    for node_label in ["n1", "n2", "n3", "0"]:
        assert node_label in response.text
    assert "1 kΩ" in response.text
    assert "1.5 kΩ" in response.text
    assert "2.2 kΩ" in response.text
    assert "manual_svg_bridge_network" in response.text
    for component_id in ["R1", "R2", "R3", "R4", "R5", "V1"]:
        assert response.text.count(component_id) >= 1


def test_second_bridge_schematic_contains_clear_component_and_node_labels():
    response = _schematic(bridge_network_alt_problem())

    assert response.status_code == 200
    for label in ["R1", "R2", "R3", "R4", "R5", "V1"]:
        assert label in response.text
    for node_label in ["src", "a", "b", "0"]:
        assert node_label in response.text
    assert "1.2 kΩ" in response.text
    assert "3.3 kΩ" in response.text
    assert "manual_svg_bridge_network" in response.text


def test_schematic_uses_template_for_goal_variant():
    variant = generate_goal_variant(bridge_network_problem())
    response = _schematic(variant)

    assert response.status_code == 200
    assert "manual_svg_bridge_network" in response.text
    assert "fallback_graph" not in response.text
    assert variant.topology_id == "bridge_network"


def test_schematic_uses_template_for_second_bridge_goal_variant():
    variant = generate_goal_variant(bridge_network_alt_problem())
    response = _schematic(variant)

    assert response.status_code == 200
    assert "manual_svg_bridge_network" in response.text
    assert "fallback_graph" not in response.text
    assert "src" in response.text
    assert "a" in response.text
    assert "b" in response.text


def test_schematic_uses_template_for_value_variant():
    variant = generate_value_variant(bridge_network_alt_problem())
    response = _schematic(variant)

    assert response.status_code == 200
    assert "manual_svg_bridge_network" in response.text
    assert "fallback_graph" not in response.text
    assert "R5" in response.text
    assert variant.topology_id == "bridge_network"


def test_schematic_normalizes_variant_id_when_topology_id_missing():
    variant = generate_value_variant(voltage_divider_problem())
    variant.topology_id = None
    response = _schematic(variant)

    assert response.status_code == 200
    assert "schemdraw_voltage_divider" in response.text
    assert "fallback_graph" not in response.text


def test_schematic_fallback_still_works_for_unknown_topology():
    circuit = CircuitProblem(
        id="custom_supported_network",
        title="Custom Supported Network",
        topology_id=None,
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=1000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["n2", "0"], value=2000.0, unit="ohm"),
        ],
        goals=[Goal(id="n2_voltage", quantity="node_voltage", target="n2")],
    )
    response = _schematic(circuit)

    assert response.status_code == 200
    assert response.text.lstrip().startswith("<svg")
    assert "fallback_graph" in response.text
    assert "R1" in response.text
    assert "1 kΩ" in response.text


def test_schematic_template_error_returns_fallback_svg(monkeypatch):
    def broken_renderer(circuit):
        raise RuntimeError("schemdraw failed")

    monkeypatch.setattr(schematic_generator, "_render_bridge_manual_svg", broken_renderer)
    response = _schematic(bridge_network_problem())

    assert response.status_code == 200
    assert response.text.lstrip().startswith("<svg")
    assert "fallback_graph_after_schemdraw_error" in response.text
