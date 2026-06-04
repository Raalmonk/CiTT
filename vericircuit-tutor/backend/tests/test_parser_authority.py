import pytest
from pydantic import ValidationError

from app.models.circuit_ir import CircuitProblem
from app.services.demo_parser import voltage_divider_problem
from app.services.pipeline import solve_circuit


def test_circuit_problem_rejects_injected_final_numerical_answers():
    payload = voltage_divider_problem().model_dump()
    payload["final_answer"] = {"voltage_across_R2": "999 V"}

    with pytest.raises(ValidationError):
        CircuitProblem.model_validate(payload)


def test_parser_ir_has_no_numerical_answer_fields_and_solver_still_owns_answer():
    circuit = voltage_divider_problem()
    assert not hasattr(circuit, "final_answer")
    assert not hasattr(circuit, "requested_answers")

    packet = solve_circuit(circuit, parser_used="demo")

    assert packet.requested_answers["voltage_across_R2"].value == pytest.approx(6.0)
    assert packet.calculation_trace.answer_source == "mna_solver"
    assert packet.calculation_trace.llm_used_for_numerical_answer is False

