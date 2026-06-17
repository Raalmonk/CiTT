from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.demo_parser import parse_demo_problem
from app.services.pipeline import solve_circuit


def test_singular_current_source_open_node_returns_human_message():
    circuit = CircuitProblem(
        id="singular_open_current_source",
        title="Open Current Source",
        ground_node="0",
        nodes=["0", "n1"],
        components=[
            Component(
                id="I1",
                type="current_source",
                nodes=["0", "n1"],
                value=0.001,
                unit="A",
            )
        ],
        goals=[Goal(id="n1_voltage", quantity="node_voltage", target="n1")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "invalid"
    assert packet.verification_badge.label == "FAIL"
    assert "singular" in packet.verification_badge.message.lower()
    assert packet.warnings


def test_floating_component_subgraph_fails_validation_with_message():
    circuit = CircuitProblem(
        id="floating_resistor",
        title="Floating Resistor",
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=1000.0, unit="ohm")
        ],
        goals=[Goal(id="R1_current", quantity="component_current", target="R1")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "invalid"
    assert packet.verification_badge.label == "FAIL"
    assert "not connected to ground" in packet.verification_badge.message


def test_duplicate_component_ids_fail_validation_with_message():
    circuit = CircuitProblem(
        id="duplicate_ids",
        title="Duplicate IDs",
        ground_node="0",
        nodes=["0", "n1"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["n1", "0"], value=1000.0, unit="ohm"),
            Component(id="R1", type="resistor", nodes=["n1", "0"], value=2000.0, unit="ohm"),
        ],
        goals=[Goal(id="n1_voltage", quantity="node_voltage", target="n1")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "invalid"
    assert packet.verification_badge.label == "FAIL"
    assert "Component IDs must be unique" in packet.verification_badge.message


def test_unsupported_component_type_returns_unsupported_badge():
    circuit = CircuitProblem(
        id="unsupported_inductor",
        title="Unsupported Inductor",
        ground_node="0",
        nodes=["0", "n1"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=5.0, unit="V"),
            Component(id="L1", type="inductor", nodes=["n1", "0"], value=1e-3, unit="H"),
        ],
        goals=[Goal(id="L1_current", quantity="component_current", target="L1")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "unsupported"
    assert packet.verification_badge.label == "UNSUPPORTED"
    assert "Unsupported component type" in packet.verification_badge.message


def test_unsupported_natural_language_request_returns_unsupported_badge():
    circuit = parse_demo_problem("Find the transient response of an RC circuit.")
    packet = solve_circuit(circuit)

    assert packet.status == "unsupported"
    assert packet.verification_badge.label == "UNSUPPORTED"
    assert "transient analysis" in packet.verification_badge.message


def test_nonideal_op_amp_request_uses_supported_model():
    circuit = parse_demo_problem("Analyze an op-amp with rail saturation and clipping recovery.")
    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert circuit.components[-1].type == "nonideal_op_amp"
    assert packet.requested_answers["vout"].value == 4.8
    assert any("saturated" in warning for warning in packet.warnings)


def test_text_only_image_request_without_image_is_ambiguous():
    circuit = parse_demo_problem("Find Vout from this image of a schematic.")
    packet = solve_circuit(circuit)

    assert packet.status == "ambiguous"
    assert packet.verification_badge.label == "AMBIGUOUS"
    assert "parse_image" in packet.verification_badge.message


def test_ambiguous_natural_language_request_returns_ambiguous_badge():
    circuit = parse_demo_problem("Find the voltage in this circuit.")
    packet = solve_circuit(circuit)

    assert packet.status == "ambiguous"
    assert packet.verification_badge.label == "AMBIGUOUS"
    assert "Ambiguities must be resolved" in packet.verification_badge.message
