from fastapi.testclient import TestClient

from app.main import app
from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services import optcpv_bridge
from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import (
    bridge_network_alt_problem,
    bridge_network_problem,
    current_divider_problem,
    voltage_divider_problem,
)
from app.services.variant_generator import generate_goal_variant, generate_value_variant


def _schematic(circuit: CircuitProblem, renderer: str | None = None):
    client = TestClient(app)
    payload = {"circuit_ir": circuit.model_dump()}
    if renderer:
        payload["renderer"] = renderer
    return client.post("/schematic", json=payload)


def _assert_optcpv_svg(response, circuit: CircuitProblem) -> None:
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.text.lstrip().startswith("<svg")
    assert 'data-renderer="optcpv.' in response.text
    assert f'data-optcpv-circuit-id="{circuit.id}"' in response.text
    assert "fallback_graph" not in response.text
    assert "schemdraw_voltage_divider" not in response.text
    assert "manual_svg_bridge_network" not in response.text


def test_schematic_endpoint_returns_optcpv_svg_for_original_examples():
    for circuit in [
        voltage_divider_problem(),
        current_divider_problem(),
        bridge_network_problem(),
        bridge_network_alt_problem(),
    ]:
        _assert_optcpv_svg(_schematic(circuit), circuit)


def test_schematic_preserves_component_metadata_and_resistor_labels():
    circuit = voltage_divider_problem()
    response = _schematic(circuit)

    _assert_optcpv_svg(response, circuit)
    for component in circuit.components:
        assert f'data-component-id="{component.id}"' in response.text
    assert "R1" in response.text
    assert "2 kΩ" in response.text
    assert "R2" in response.text
    assert "3 kΩ" in response.text
    assert "V1" in response.text


def test_bridge_schematic_keeps_all_bridge_components():
    circuit = bridge_network_problem()
    response = _schematic(circuit)

    _assert_optcpv_svg(response, circuit)
    for component_id in ["V1", "R1", "R2", "R3", "R4", "R5"]:
        assert f'data-component-id="{component_id}"' in response.text
    assert "R5" in response.text


def test_bme_schematic_keeps_component_metadata_without_citt_fallback():
    circuit = BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem
    response = _schematic(circuit)

    _assert_optcpv_svg(response, circuit)
    for component in circuit.components:
        assert f'data-component-id="{component.id}"' in response.text


def test_schematic_renders_variants_through_optcpv():
    variants = [
        generate_goal_variant(bridge_network_problem()),
        generate_goal_variant(bridge_network_alt_problem()),
        generate_value_variant(bridge_network_alt_problem()),
        generate_value_variant(voltage_divider_problem()),
    ]

    for variant in variants:
        _assert_optcpv_svg(_schematic(variant), variant)


def test_schematic_unknown_topology_still_uses_optcpv_not_citt_fallback():
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

    _assert_optcpv_svg(response, circuit)
    for component in circuit.components:
        assert f'data-component-id="{component.id}"' in response.text


def test_voltage_clamp_schematic_canonicalizes_lowercase_nets_for_optcpv_routes():
    circuit = CircuitProblem(
        id="tevc_lowercase",
        title="Lowercase TEVC",
        topology_id="two_electrode_voltage_clamp",
        ground_node="gnd",
        nodes=["gnd", "vc", "vm", "vo"],
        components=[
            Component(
                id="DiffAmp",
                type="op_amp_nonideal",
                nodes=["vc", "vm", "vo", "gnd"],
                value=100.0,
                unit="gain",
                open_loop_gain=100.0,
            ),
            Component(id="R_m", type="resistor", nodes=["vm", "gnd"], value=10.0, unit="ohm", label="R_m = 10 ohm"),
            Component(id="R_o", type="resistor", nodes=["vo", "vm"], value=10.0, unit="ohm", label="R_o = 10 ohm"),
        ],
        goals=[Goal(id="vm_equilibrium", quantity="node_voltage", target="vm")],
    )
    response = _schematic(circuit)

    _assert_optcpv_svg(response, circuit)
    assert 'data-component-id="VC"' in response.text
    assert 'data-component-id="VM"' in response.text
    assert 'data-component-id="VO"' in response.text
    assert 'data-component-id="GND"' in response.text
    assert 'data-net-name="Vm"' in response.text
    assert 'data-net-name="vm"' not in response.text


def test_schematic_rejects_removed_citt_renderer_option():
    response = _schematic(voltage_divider_problem(), renderer="citt")

    assert response.status_code == 422


def test_schematic_endpoint_can_render_through_optcpv(monkeypatch):
    def fake_from_citt_payload(payload):
        assert payload["id"] == "voltage_divider"
        assert payload["motif"] == "voltage_divider"
        assert payload["output_node"] == "n2"
        assert payload["components"][0]["label"].startswith("V1 = ")
        return payload

    def fake_draw_svg(payload):
        assert payload["ground_node"] == "0"
        return '<svg data-renderer="optcpv.raw"><g data-component-id="R1"></g></svg>'

    def fake_draw_optimized_svg(*args, **kwargs):
        raise AssertionError("raw OptCPV rendering should be the default")

    monkeypatch.setattr(
        optcpv_bridge,
        "_load_bindings",
        lambda: optcpv_bridge.OptCPVBindings(
            from_citt_payload=fake_from_citt_payload,
            draw_svg=fake_draw_svg,
            draw_optimized_svg=fake_draw_optimized_svg,
        ),
    )

    response = _schematic(voltage_divider_problem(), renderer="optcpv")

    assert response.status_code == 200
    assert 'data-renderer="optcpv.raw"' in response.text
    assert 'data-component-id="R1"' in response.text


def test_optcpv_schematic_error_is_returned_without_citt_fallback(monkeypatch, caplog):
    def fake_from_citt_payload(payload):
        return payload

    def fake_draw_svg(payload):
        raise RuntimeError("optcpv render exploded")

    monkeypatch.setattr(
        optcpv_bridge,
        "_load_bindings",
        lambda: optcpv_bridge.OptCPVBindings(
            from_citt_payload=fake_from_citt_payload,
            draw_svg=fake_draw_svg,
            draw_optimized_svg=fake_draw_svg,
        ),
    )
    caplog.set_level("ERROR", logger="app.main")

    response = _schematic(voltage_divider_problem(), renderer="optcpv")

    assert response.status_code == 502
    assert response.json()["detail"].startswith("OptCPV schematic rendering failed")
    assert "fallback_graph" not in response.text
    assert "OptCPV schematic rendering failed." in caplog.text
