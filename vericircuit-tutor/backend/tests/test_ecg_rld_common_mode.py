import pytest

from app.models.circuit_ir import CircuitProblem, Component, Goal
from app.services.pipeline import solve_circuit


def _ecg_rld_problem(ambiguities: list[str] | None = None) -> CircuitProblem:
    return CircuitProblem(
        id="ecg_rld_common_mode",
        title="ECG Right-Leg Drive Circuit Common-Mode Analysis",
        analysis_type="dc_operating_point",
        ground_node="0",
        nodes=[
            "0",
            "Vcm",
            "Vo",
            "V1",
            "V2",
            "V3",
            "A2_inv",
            "A2_out",
            "Aau_out",
            "A3_inv",
            "A3_noninv",
            "A3_out",
            "V4",
            "A4_inv",
            "V5",
        ],
        components=[
            Component(id="id_source", type="current_source", nodes=["0", "Vcm"], value=1e-7, unit="A"),
            Component(id="R_RL", type="resistor", nodes=["Vcm", "Vo"], value=100_000, unit="ohm"),
            Component(id="A1", type="ideal_op_amp", nodes=["Vcm", "V1", "V2", "0"], value=0, unit="ideal"),
            Component(
                id="A2",
                type="ideal_op_amp",
                nodes=["Vcm", "A2_inv", "A2_out", "0"],
                value=0,
                unit="ideal",
            ),
            Component(id="R_a1", type="resistor", nodes=["V2", "V3"], value=10_000, unit="ohm"),
            Component(id="R_a2", type="resistor", nodes=["A2_out", "V3"], value=10_000, unit="ohm"),
            Component(
                id="Aau",
                type="ideal_op_amp",
                nodes=["0", "V3", "Aau_out", "0"],
                value=0,
                unit="ideal",
            ),
            Component(id="R_f", type="resistor", nodes=["Vo", "V3"], value=2_000_000, unit="ohm"),
            Component(
                id="A3",
                type="ideal_op_amp",
                nodes=["A3_noninv", "A3_inv", "A3_out", "0"],
                value=0,
                unit="ideal",
            ),
            Component(id="R_3a", type="resistor", nodes=["V2", "A3_inv"], value=10_000, unit="ohm"),
            Component(id="R_3b", type="resistor", nodes=["A2_out", "A3_noninv"], value=10_000, unit="ohm"),
            Component(id="R_4_fixed", type="resistor", nodes=["A3_inv", "A3_out"], value=47_000, unit="ohm"),
            Component(id="C1", type="capacitor", nodes=["A3_out", "V4"], value=1e-6, unit="F"),
            Component(id="R7", type="resistor", nodes=["V4", "0"], value=3_300_000, unit="ohm"),
            Component(
                id="A4",
                type="ideal_op_amp",
                nodes=["V4", "A4_inv", "V5", "0"],
                value=0,
                unit="ideal",
            ),
            Component(id="R5", type="resistor", nodes=["A4_inv", "0"], value=4700, unit="ohm"),
            Component(id="R6", type="resistor", nodes=["A4_inv", "V5"], value=150_000, unit="ohm"),
            Component(id="C2", type="capacitor", nodes=["A4_inv", "V5"], value=1e-8, unit="F"),
        ],
        goals=[
            Goal(id="goal_Vcm", quantity="node_voltage", target="Vcm"),
            Goal(id="goal_Vo", quantity="node_voltage", target="Vo"),
            Goal(id="goal_V1", quantity="node_voltage", target="V1"),
            Goal(id="goal_V2", quantity="node_voltage", target="V2"),
            Goal(id="goal_V3", quantity="node_voltage", target="V3"),
            Goal(id="goal_V4", quantity="node_voltage", target="V4"),
            Goal(id="goal_V5", quantity="node_voltage", target="V5"),
        ],
        assumptions=[
            "Operational amplifiers are ideal.",
            "System is not saturated.",
            "There is no differential ECG signal input, only a pure common-mode displacement current id.",
        ],
        ambiguities=ambiguities
        or [
            "Values for R1 and R2 are not provided.",
            "Value for the current-limiting resistor Ro is not provided.",
            "Exact value of the adjustable potentiometer R4 is missing.",
            "The connection topology for R2-R1-R2 is ambiguously described as series connected.",
        ],
        unsupported_features=[],
    )


def test_ecg_rld_common_mode_ignores_irrelevant_missing_values():
    packet = solve_circuit(_ecg_rld_problem(), parser_used="gemini")

    expected_vcm = 0.01 / 401.0
    expected_vo = -400.0 * expected_vcm

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.calculation_trace.solver_name == "ecg_rld_common_mode_v1"
    assert packet.requested_answers["goal_Vcm"].value == pytest.approx(expected_vcm)
    assert packet.requested_answers["goal_Vo"].value == pytest.approx(expected_vo)
    assert packet.requested_answers["goal_V1"].value == pytest.approx(expected_vcm)
    assert packet.requested_answers["goal_V2"].value == pytest.approx(expected_vcm)
    assert packet.requested_answers["goal_V3"].value == pytest.approx(0.0)
    assert packet.requested_answers["goal_V4"].value == pytest.approx(0.0)
    assert packet.requested_answers["goal_V5"].value == pytest.approx(0.0)
    assert any("R1 and R2" in warning for warning in packet.warnings)


def test_ecg_rld_common_mode_handles_omitted_dc_post_stage():
    circuit = _ecg_rld_problem(ambiguities=[])
    circuit.components = [
        component
        for component in circuit.components
        if component.id
        not in {"A3", "R_3a", "R_3b", "R_4_fixed", "C1", "A4", "R5", "R6", "C2"}
    ]
    circuit.nonblocking_ambiguities = [
        "Ideal non-inverting A4 output V5 lacks R4 trim values and its feedback network is omitted."
    ]

    packet = solve_circuit(circuit, parser_used="gemini")

    assert packet.status == "solved"
    assert packet.verification_badge.label == "PASS"
    assert packet.requested_answers["goal_V5"].value == pytest.approx(0.0)


def test_ecg_rld_common_mode_still_blocks_needed_missing_feedback_value():
    packet = solve_circuit(
        _ecg_rld_problem(ambiguities=["Value for Rf is not provided."]),
        parser_used="gemini",
    )

    assert packet.status == "ambiguous"
    assert packet.verification_badge.label == "AMBIGUOUS"
