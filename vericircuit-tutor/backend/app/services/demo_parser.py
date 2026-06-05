from __future__ import annotations

from app.models.circuit_ir import CircuitProblem, Component, Goal


VOLTAGE_DIVIDER_TEXT = (
    "A 10 V voltage source is connected in series with R1 = 2 kOhm and "
    "R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit."
)

CURRENT_DIVIDER_TEXT = (
    "A 3 mA current source feeds two parallel resistors R1 = 2 kOhm and "
    "R2 = 1 kOhm connected to ground. Find the voltage at the top node and "
    "current through each resistor."
)

BRIDGE_NETWORK_TEXT = (
    "A 12 V source drives a bridge network. R1 = 1 kOhm from the source node "
    "to node n2, R2 = 2 kOhm from n2 to ground, R3 = 1.5 kOhm from the source "
    "node to node n3, R4 = 3 kOhm from n3 to ground, and R5 = 2.2 kOhm between "
    "n2 and n3. Find node voltages n2 and n3 and the current through R5."
)

BRIDGE_NETWORK_ALT_TEXT = (
    "A 9 V source drives another bridge network. R1 = 1.2 kOhm from the source "
    "node to node a, R2 = 1.8 kOhm from node a to ground, R3 = 2.7 kOhm from "
    "the source node to node b, R4 = 1.5 kOhm from node b to ground, and "
    "R5 = 3.3 kOhm between node a and node b. Find node voltages a and b and "
    "the current through R5."
)

RC_LOW_PASS_TEXT = (
    "An RC low-pass filter has a 1 V AC source at 159.154943 Hz, R1 = 1 kOhm "
    "from input to output, and C1 = 1 uF from output to ground. Find Vout."
)

OP_AMP_NON_INVERTING_TEXT = (
    "An ideal non-inverting op-amp has Vplus driven by a 1 V source, Rg = 1 kOhm "
    "from the inverting input to ground, and Rf = 9 kOhm from output to the "
    "inverting input. Find Vout."
)


def voltage_divider_problem() -> CircuitProblem:
    return CircuitProblem(
        id="voltage_divider",
        title="Voltage Divider",
        analysis_type="dc_operating_point",
        topology_id="voltage_divider",
        layout_hint={"renderer": "schemdraw_voltage_divider"},
        ground_node="0",
        nodes=["0", "n1", "n2"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["n1", "0"],
                value=10.0,
                unit="V",
                label="10 V DC source",
                voltage_reference={"positive_node": "n1", "negative_node": "0"},
                current_reference={"from_node": "n1", "to_node": "0"},
            ),
            Component(
                id="R1",
                type="resistor",
                nodes=["n1", "n2"],
                value=2000.0,
                unit="ohm",
                label="2 kOhm resistor",
                voltage_reference={"positive_node": "n1", "negative_node": "n2"},
                current_reference={"from_node": "n1", "to_node": "n2"},
            ),
            Component(
                id="R2",
                type="resistor",
                nodes=["n2", "0"],
                value=3000.0,
                unit="ohm",
                label="3 kOhm resistor",
                voltage_reference={"positive_node": "n2", "negative_node": "0"},
                current_reference={"from_node": "n2", "to_node": "0"},
            ),
        ],
        goals=[
            Goal(
                id="voltage_across_R2",
                quantity="component_voltage",
                target="R2",
                reference={"positive_node": "n2", "negative_node": "0"},
            ),
            Goal(
                id="circuit_current",
                quantity="component_current",
                target="R1",
                reference={"from_node": "n1", "to_node": "n2"},
            ),
        ],
        assumptions=[
            "The source positive terminal is connected to the top of R1.",
            "The requested circuit current is the series current through R1 and R2.",
        ],
        ambiguities=[],
        unsupported_features=[],
    )


def current_divider_problem() -> CircuitProblem:
    return CircuitProblem(
        id="current_divider",
        title="Current Source Feeding Parallel Resistors",
        analysis_type="dc_operating_point",
        topology_id="current_divider",
        layout_hint={"renderer": "schemdraw_current_divider"},
        ground_node="0",
        nodes=["0", "top"],
        components=[
            Component(
                id="I1",
                type="current_source",
                nodes=["0", "top"],
                value=0.003,
                unit="A",
                label="3 mA source feeding the top node",
                current_reference={"from_node": "0", "to_node": "top"},
                voltage_reference={"positive_node": "0", "negative_node": "top"},
            ),
            Component(
                id="R1",
                type="resistor",
                nodes=["top", "0"],
                value=2000.0,
                unit="ohm",
                label="2 kOhm branch",
                current_reference={"from_node": "top", "to_node": "0"},
                voltage_reference={"positive_node": "top", "negative_node": "0"},
            ),
            Component(
                id="R2",
                type="resistor",
                nodes=["top", "0"],
                value=1000.0,
                unit="ohm",
                label="1 kOhm branch",
                current_reference={"from_node": "top", "to_node": "0"},
                voltage_reference={"positive_node": "top", "negative_node": "0"},
            ),
        ],
        goals=[
            Goal(
                id="top_node_voltage",
                quantity="node_voltage",
                target="top",
                reference={"positive_node": "top", "negative_node": "0"},
            ),
            Goal(
                id="R1_current",
                quantity="component_current",
                target="R1",
                reference={"from_node": "top", "to_node": "0"},
            ),
            Goal(
                id="R2_current",
                quantity="component_current",
                target="R2",
                reference={"from_node": "top", "to_node": "0"},
            ),
        ],
        assumptions=[
            "The current source points from ground into the top node.",
            "Both resistors connect from the top node to ground.",
        ],
        ambiguities=[],
        unsupported_features=[],
    )


def bridge_network_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bridge_network",
        title="Five-Resistor Bridge Network",
        analysis_type="dc_operating_point",
        topology_id="bridge_network",
        layout_hint={"renderer": "schemdraw_bridge_network"},
        ground_node="0",
        nodes=["0", "n1", "n2", "n3"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["n1", "0"],
                value=12.0,
                unit="V",
                label="12 V DC source",
            ),
            Component(id="R1", type="resistor", nodes=["n1", "n2"], value=1000.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["n2", "0"], value=2000.0, unit="ohm"),
            Component(id="R3", type="resistor", nodes=["n1", "n3"], value=1500.0, unit="ohm"),
            Component(id="R4", type="resistor", nodes=["n3", "0"], value=3000.0, unit="ohm"),
            Component(id="R5", type="resistor", nodes=["n2", "n3"], value=2200.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="n2_voltage",
                quantity="node_voltage",
                target="n2",
                reference={"positive_node": "n2", "negative_node": "0"},
            ),
            Goal(
                id="n3_voltage",
                quantity="node_voltage",
                target="n3",
                reference={"positive_node": "n3", "negative_node": "0"},
            ),
            Goal(
                id="R5_current",
                quantity="component_current",
                target="R5",
                reference={"from_node": "n2", "to_node": "n3"},
            ),
        ],
        assumptions=[
            "The bridge source fixes node n1 at +12 V relative to ground.",
            "R5 current is reported positive from n2 to n3.",
        ],
        ambiguities=[],
        unsupported_features=[],
    )


def bridge_network_alt_problem() -> CircuitProblem:
    return CircuitProblem(
        id="bridge_network_alt",
        title="Second Five-Resistor Bridge Network",
        analysis_type="dc_operating_point",
        topology_id="bridge_network",
        layout_hint={"renderer": "schemdraw_bridge_network"},
        ground_node="0",
        nodes=["0", "src", "a", "b"],
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["src", "0"],
                value=9.0,
                unit="V",
                label="9 V DC source",
            ),
            Component(id="R1", type="resistor", nodes=["src", "a"], value=1200.0, unit="ohm"),
            Component(id="R2", type="resistor", nodes=["a", "0"], value=1800.0, unit="ohm"),
            Component(id="R3", type="resistor", nodes=["src", "b"], value=2700.0, unit="ohm"),
            Component(id="R4", type="resistor", nodes=["b", "0"], value=1500.0, unit="ohm"),
            Component(id="R5", type="resistor", nodes=["a", "b"], value=3300.0, unit="ohm"),
        ],
        goals=[
            Goal(
                id="a_voltage",
                quantity="node_voltage",
                target="a",
                reference={"positive_node": "a", "negative_node": "0"},
            ),
            Goal(
                id="b_voltage",
                quantity="node_voltage",
                target="b",
                reference={"positive_node": "b", "negative_node": "0"},
            ),
            Goal(
                id="R5_current",
                quantity="component_current",
                target="R5",
                reference={"from_node": "a", "to_node": "b"},
            ),
        ],
        assumptions=[
            "The bridge source fixes node src at +9 V relative to ground.",
            "R5 current is reported positive from node a to node b.",
        ],
        ambiguities=[],
        unsupported_features=[],
    )


def rc_low_pass_problem() -> CircuitProblem:
    return CircuitProblem(
        id="rc_low_pass",
        title="RC Low-Pass AC Single-Frequency",
        analysis_type="ac_single_frequency",
        topology_id="rc_low_pass",
        ground_node="0",
        nodes=["0", "in", "out"],
        frequency_hz=159.154943,
        components=[
            Component(
                id="V1",
                type="voltage_source",
                nodes=["in", "0"],
                value=0.0,
                unit="V",
                ac_magnitude=1.0,
                ac_phase_deg=0.0,
            ),
            Component(id="R1", type="resistor", nodes=["in", "out"], value=1000.0, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["out", "0"], value=1e-6, unit="F"),
        ],
        goals=[
            Goal(
                id="vout",
                quantity="node_voltage",
                target="out",
                reference={"positive_node": "out", "negative_node": "0"},
            )
        ],
        assumptions=["The AC source value is a phasor amplitude."],
    )


def op_amp_non_inverting_problem() -> CircuitProblem:
    return CircuitProblem(
        id="op_amp_non_inverting",
        title="Ideal Non-Inverting Op-Amp",
        analysis_type="dc_operating_point",
        topology_id="op_amp_non_inverting",
        ground_node="0",
        nodes=["0", "vp", "vm", "out"],
        components=[
            Component(id="V1", type="voltage_source", nodes=["vp", "0"], value=1.0, unit="V"),
            Component(id="Rg", type="resistor", nodes=["vm", "0"], value=1000.0, unit="ohm"),
            Component(id="Rf", type="resistor", nodes=["out", "vm"], value=9000.0, unit="ohm"),
            Component(
                id="U1",
                type="op_amp_ideal",
                nodes=["vp", "vm", "out", "0"],
                value=0.0,
                unit="ideal",
            ),
        ],
        goals=[
            Goal(id="vout", quantity="node_voltage", target="out"),
            Goal(id="vminus", quantity="node_voltage", target="vm"),
        ],
        assumptions=["The op-amp is ideal and operated with closed-loop negative feedback."],
    )


def unsupported_problem(problem_text: str, feature: str) -> CircuitProblem:
    return CircuitProblem(
        id="unsupported_request",
        title="Unsupported Circuit Request",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0"],
        components=[],
        goals=[],
        assumptions=[],
        ambiguities=[],
        unsupported_features=[feature, f"Original request: {problem_text}"],
    )


def ambiguous_problem(problem_text: str) -> CircuitProblem:
    return CircuitProblem(
        id="ambiguous_request",
        title="Ambiguous Circuit Request",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=["0"],
        components=[],
        goals=[],
        assumptions=[],
        ambiguities=[
            "The deterministic demo parser only recognizes the bundled examples.",
            f"Original request: {problem_text}",
        ],
        unsupported_features=[],
    )


def get_demo_examples() -> list[dict[str, str]]:
    return [
        {
            "id": "voltage_divider",
            "title": "Voltage Divider",
            "problem_text": VOLTAGE_DIVIDER_TEXT,
        },
        {
            "id": "current_divider",
            "title": "Current Source with Parallel Resistors",
            "problem_text": CURRENT_DIVIDER_TEXT,
        },
        {
            "id": "bridge_network",
            "title": "Bridge Network",
            "problem_text": BRIDGE_NETWORK_TEXT,
        },
        {
            "id": "bridge_network_alt",
            "title": "Second Bridge Network",
            "problem_text": BRIDGE_NETWORK_ALT_TEXT,
        },
        {
            "id": "rc_low_pass",
            "title": "RC Low-Pass AC",
            "problem_text": RC_LOW_PASS_TEXT,
        },
        {
            "id": "op_amp_non_inverting",
            "title": "Ideal Non-Inverting Op-Amp",
            "problem_text": OP_AMP_NON_INVERTING_TEXT,
        },
    ]


def parse_demo_problem(problem_text: str) -> CircuitProblem:
    lowered = " ".join(problem_text.lower().split())
    if "transient" in lowered or "time-domain" in lowered:
        return unsupported_problem(problem_text, "transient analysis")
    if any(term in lowered for term in ["inductor", "diode", "transistor"]):
        return unsupported_problem(problem_text, "Unsupported component outside the current MVP scope.")
    if "10 v voltage source" in lowered and "r1 = 2 kohm" in lowered and "r2 = 3 kohm" in lowered:
        return voltage_divider_problem()
    if "3 ma current source" in lowered and "parallel resistors" in lowered:
        return current_divider_problem()
    if "another bridge network" in lowered and "9 v source" in lowered and "r5" in lowered:
        return bridge_network_alt_problem()
    if "bridge" in lowered and "r5" in lowered:
        return bridge_network_problem()
    if "low-pass" in lowered and "1 uf" in lowered and "159.154943" in lowered:
        return rc_low_pass_problem()
    if "non-inverting" in lowered and ("op-amp" in lowered or "op amp" in lowered):
        return op_amp_non_inverting_problem()
    return ambiguous_problem(problem_text)
