import pytest

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.demo_parser import nonideal_op_amp_problem, voltage_divider_problem
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


def test_dc_inductor_is_supported_as_steady_state_short():
    circuit = CircuitProblem(
        id="dc_inductor_short",
        title="DC Inductor Short",
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=1000.0, unit="ohm"),
            Component(id="L1", type="inductor", nodes=["n2", "0"], value=1e-3, unit="H"),
        ],
        goals=[
            Goal(id="n2_voltage", quantity="node_voltage", target="n2"),
            Goal(id="L1_current", quantity="component_current", target="L1"),
        ],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.node_voltages["n2"] == pytest.approx(0.0)
    assert packet.component_results["L1"].voltage.value == pytest.approx(0.0)
    assert packet.component_results["L1"].current.value == pytest.approx(0.005)
    assert packet.requested_answers["L1_current"].value == pytest.approx(0.005)


def test_conflicting_dc_inductor_short_returns_invalid_badge():
    circuit = CircuitProblem(
        id="conflicting_dc_inductor_short",
        title="Conflicting DC Inductor Short",
        ground_node="0",
        nodes=["0", "n1"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=5.0, unit="V"),
            Component(id="L1", type="inductor", nodes=["n1", "0"], value=1e-3, unit="H"),
        ],
        goals=[Goal(id="L1_current", quantity="component_current", target="L1")],
    )

    packet = solve_circuit(circuit)

    assert packet.status == "invalid"
    assert packet.verification_badge.label == "FAIL"
    assert "singular" in packet.verification_badge.message.lower()


def test_unsupported_natural_language_request_returns_unsupported_badge():
    circuit = CircuitProblem(
        id="unsupported_transient_request",
        title="Unsupported Transient Request",
        ground_node="0",
        nodes=["0"],
        unsupported_features=["transient analysis"],
    )
    packet = solve_circuit(circuit)

    assert packet.status == "unsupported"
    assert packet.verification_badge.label == "UNSUPPORTED"
    assert "transient analysis" in packet.verification_badge.message


def test_nonideal_op_amp_request_uses_supported_model():
    circuit = nonideal_op_amp_problem()
    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert circuit.components[-1].type == "nonideal_op_amp"
    assert packet.requested_answers["vout"].value == 4.8
    assert any("saturated" in warning for warning in packet.warnings)


def test_text_only_image_request_without_image_is_ambiguous():
    circuit = CircuitProblem(
        id="text_only_image_request",
        title="Text-only Image Request",
        ground_node="0",
        nodes=["0"],
        ambiguities=["Use /parse_image with image_base64 for schematic/image recognition."],
    )
    packet = solve_circuit(circuit)

    assert packet.status == "ambiguous"
    assert packet.verification_badge.label == "AMBIGUOUS"
    assert "parse_image" in packet.verification_badge.message


def test_ambiguous_natural_language_request_returns_ambiguous_badge():
    circuit = CircuitProblem(
        id="ambiguous_request",
        title="Ambiguous Circuit Request",
        ground_node="0",
        nodes=["0"],
        ambiguities=["Topology and component values are not specified."],
    )
    packet = solve_circuit(circuit)

    assert packet.status == "ambiguous"
    assert packet.verification_badge.label == "AMBIGUOUS"
    assert "Ambiguities must be resolved" in packet.verification_badge.message


def test_nonblocking_ambiguities_do_not_stop_solvable_circuit():
    circuit = voltage_divider_problem().model_copy(deep=True)
    circuit.nonblocking_ambiguities = [
        "A secondary switched branch was outside the requested output-voltage calculation and omitted."
    ]

    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.requested_answers["voltage_across_R2"].value == pytest.approx(6.0)
    assert any("Non-blocking parse note" in warning for warning in packet.warnings)


def test_null_goal_reference_entries_are_ignored_before_solving():
    circuit = CircuitProblem(
        id="null_goal_reference",
        title="Null Goal Reference",
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["n1", "0"], value=5.0, unit="V"),
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=1000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["n2", "0"], value=4000.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="voltage_across_R2",
                quantity="component_voltage",
                target="R2",
                reference={
                    "positive_node": "n2",
                    "negative_node": "0",
                    "from_node": None,
                    "to_node": None,
                    "component": None,
                },
            )
        ],
    )

    packet = solve_circuit(circuit)

    assert circuit.goals[0].reference == {"positive_node": "n2", "negative_node": "0"}
    assert packet.status == "solved"
    assert packet.requested_answers["voltage_across_R2"].value == pytest.approx(4.0)
