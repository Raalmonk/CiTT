import pytest

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.parser_service import parse_image_problem, parse_problem
from app.services.pipeline import solve_circuit


def test_two_electrode_voltage_clamp_keeps_command_voltage_symbolic():
    circuit = CircuitProblem(
        id="two_electrode_voltage_clamp",
        title="2-Electrode Voltage Clamp Equilibrium",
        topology_id="two_electrode_voltage_clamp",
        ground_node="0",
        nodes=["0", "Vc", "Vm", "Vo"],
        components=[
            Component(
                id="DiffAmp",
                type="op_amp_nonideal",
                nodes=["Vc", "Vm", "Vo", "0"],
                value=100.0,
                unit="gain",
                open_loop_gain=100.0,
            ),
            Component(
                id="R_m",
                type="resistor",
                nodes=["Vm", "0"],
                value=10.0,
                unit="ohm",
                label="R_m = 10 ohm",
            ),
            Component(
                id="R_o",
                type="resistor",
                nodes=["Vo", "Vm"],
                value=10.0,
                unit="ohm",
                label="R_o = 10 ohm",
            ),
        ],
        goals=[Goal(id="vm_equilibrium", quantity="node_voltage", target="Vm")],
        assumptions=["A = 100", "Rm = Ro = 10 ohm"],
        ambiguities=[
            "Value for command voltage V_c is unspecified.",
            "Value for voltage electrode resistance R_e is unspecified.",
        ],
    )

    packet = solve_circuit(circuit, parser_used="gemini_image")

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.requested_answers == {}
    answer = packet.symbolic_requested_answers["vm_equilibrium"]
    assert answer.expression == "50/51 V_c"
    assert answer.numeric_coefficient == pytest.approx(50 / 51)
    assert packet.calculation_trace.solver_name == "symbolic_voltage_clamp_v1"
    assert packet.calculation_trace.parser_used == "gemini_image"
    assert packet.guided_steps
    assert not packet.warnings


def test_text_parser_falls_back_to_symbolic_voltage_clamp_template(monkeypatch):
    import app.services.parser_service as parser_service

    prompt = (
        "In a 2-electrode voltage clamp, what is V_m at equilibrium? "
        "Assume A to be 100, Rm = Ro = 10 ohm."
    )

    monkeypatch.setattr(
        parser_service,
        "parse_with_gemini",
        lambda _problem_text, **_kwargs: CircuitProblem(
            id="tevc_equilibrium",
            title="2-Electrode Voltage Clamp Equilibrium",
            topology_id=None,
            ground_node="0",
            nodes=["0"],
            components=[],
            goals=[],
            ambiguities=[
                "The command voltage (V_cmd) or any other input sources are not given.",
                "The nodes for the amplifier with gain A=100 are not defined.",
            ],
        ),
    )

    result = parse_problem(prompt)
    packet = solve_circuit(result.circuit, parser_used=result.parser_used)

    assert result.circuit.topology_id == "two_electrode_voltage_clamp"
    assert result.circuit.components
    assert result.circuit.ambiguities == []
    assert result.parser_used == "gemini_voltage_clamp_fallback"
    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.symbolic_requested_answers["vm_equilibrium"].expression == "50/51 V_c"


def test_image_parser_rescues_voltage_clamp_re_ro_symbolic_ambiguity(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "parse_image_with_gemini",
        lambda **_kwargs: CircuitProblem(
            id="image_voltage_clamp",
            title="Voltage clamp schematic",
            topology_id=None,
            ground_node="0",
            nodes=["0", "Vc", "Vm", "Vo"],
            components=[
                Component(
                    id="DiffAmp",
                    type="op_amp_nonideal",
                    nodes=["Vc", "Vm", "Vo", "0"],
                    value=100.0,
                    unit="gain",
                    label="Differential amplifier A = 100",
                    open_loop_gain=100.0,
                ),
                Component(
                    id="Re1",
                    type="resistor",
                    nodes=["Vm", "0"],
                    value=10.0,
                    unit="ohm",
                    label="Re = 10 ohm",
                ),
                Component(
                    id="Re2",
                    type="resistor",
                    nodes=["Vo", "Vm"],
                    value=10.0,
                    unit="ohm",
                    label="Re = 10 ohm",
                ),
            ],
            goals=[Goal(id="vm_equilibrium", quantity="node_voltage", target="Vm")],
            assumptions=["A = 100", "Ro = 10 ohm"],
            ambiguities=[
                "The command voltage Vc magnitude is not explicitly specified in the text.",
                "The problem text states 'Ro = 10 ohm' while the schematic labels both electrode resistors as 'Re'.",
            ],
        ),
    )

    result = parse_image_problem(
        problem_text="Find Vm at equilibrium. Assume A = 100 and Ro = 10 ohm.",
        image_bytes=b"fake-image",
        mime_type="image/png",
    )
    packet = solve_circuit(result.circuit, parser_used=result.parser_used)

    assert result.parser_used == "gemini_image_voltage_clamp_fallback"
    assert result.circuit.topology_id == "two_electrode_voltage_clamp"
    assert result.circuit.ambiguities == []
    assert [component.id for component in result.circuit.components] == ["DiffAmp", "R_m", "R_o"]
    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.symbolic_requested_answers["vm_equilibrium"].expression == "50/51 V_c"
