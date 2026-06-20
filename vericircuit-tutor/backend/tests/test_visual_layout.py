from fastapi.testclient import TestClient

from app.main import app
from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.demo_parser import (
    bridge_network_problem,
    current_divider_problem,
    op_amp_non_inverting_problem,
    voltage_divider_problem,
)
from app.services.visual_layout import build_visual_circuit


def test_visual_layout_endpoint_returns_semantic_layout():
    client = TestClient(app)
    circuit = voltage_divider_problem()

    response = client.post("/visual_layout", json={"circuit_ir": circuit.model_dump()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["circuit_id"] == "voltage_divider"
    assert payload["renderer"] == "optcpv"
    assert any(node["id"] == "0" and node["role"] == "ground" for node in payload["nodes"])
    assert any(component["id"] == "R2" for component in payload["components"])
    assert any(overlay["kind"] == "goal_reference" for overlay in payload["overlays"])


def test_common_templates_include_semantic_nodes_components_and_symbols():
    for circuit in [voltage_divider_problem(), current_divider_problem(), bridge_network_problem()]:
        layout = build_visual_circuit(circuit)

        assert {node.id for node in layout.nodes} >= set(circuit.nodes)
        assert {component.id for component in layout.components} == {component.id for component in circuit.components}
        assert any(annotation.kind == "ground" for annotation in layout.annotations)
        assert layout.focus_regions


def test_op_amp_visual_layout_has_pin_semantics():
    circuit = op_amp_non_inverting_problem()
    layout = build_visual_circuit(circuit)

    op_amp = next(component for component in layout.components if component.id == "U1")
    assert op_amp.orientation == "triangle"
    assert op_amp.nodes == ["vp", "vm", "out", "0"]


def test_visual_layout_fallback_does_not_crash():
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

    layout = build_visual_circuit(circuit)

    assert layout.layout_strategy == "fallback_left_to_right"
    assert layout.warnings


def test_visual_layout_fallback_layers_nodes_from_ground():
    circuit = CircuitProblem(
        id="custom_chain_network",
        title="Custom Chain Network",
        topology_id=None,
        ground_node="0",
        nodes=["0", "a", "b", "c"],
        components=[
            Component(id="R0", type="resistor", nodes=["0", "a"], value=1000.0, unit="ohm"),
            Component(id="R1", type="resistor", nodes=["a", "b"], value=1000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["b", "c"], value=1000.0, unit="ohm"),
        ],
        goals=[Goal(id="vc", quantity="node_voltage", target="c")],
    )

    layout = build_visual_circuit(circuit)
    positions = {node.id: node.position.x for node in layout.nodes}

    assert positions["0"] < positions["a"] < positions["b"] < positions["c"]
