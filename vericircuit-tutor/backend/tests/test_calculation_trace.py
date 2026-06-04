from app.services.demo_parser import VOLTAGE_DIVIDER_TEXT
from app.services.parser_service import parse_problem
from app.services.pipeline import solve_circuit


def test_calculation_trace_exists_on_solved_packet():
    parsed = parse_problem(VOLTAGE_DIVIDER_TEXT)
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)

    trace = packet.calculation_trace
    assert trace.parser_used == "demo"
    assert trace.solver_name == "internal_mna_v1"
    assert trace.solver_method == "Modified Nodal Analysis"
    assert trace.solver_backend == "numpy.linalg.solve"
    assert trace.answer_source == "mna_solver"
    assert trace.verification_source == "verifier.py"
    assert trace.unknown_order == ["V(n1)", "V(n2)", "I(V1)"]
    assert len(trace.mna_matrix) == 3
    assert len(trace.rhs_vector) == 3
    assert len(trace.solution_vector) == 3


def test_llm_used_for_numerical_answer_is_always_false_for_pipeline():
    parsed = parse_problem(VOLTAGE_DIVIDER_TEXT, mode="demo")
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)

    assert packet.calculation_trace.llm_used_for_numerical_answer is False

