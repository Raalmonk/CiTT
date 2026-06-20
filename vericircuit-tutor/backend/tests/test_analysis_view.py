from fastapi.testclient import TestClient

from app.main import app
from app.models.circuit_ir import CircuitProblem
from app.services.analysis_view import build_analysis_view
from app.services.demo_parser import (
    bridge_network_problem,
    current_divider_problem,
    voltage_divider_problem,
)
from app.services.pipeline import solve_circuit


def test_voltage_divider_kcl_reports_r1_entering_and_r2_leaving():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit, parser_used="fixture")

    view = build_analysis_view(circuit, packet)
    n2_report = view.node_kcl["n2"]
    terms = {term.component_id: term for term in n2_report.terms}

    assert view.status == "available"
    assert terms["R1"].direction == "entering"
    assert terms["R2"].direction == "leaving"
    assert terms["R1"].signed_current_leaving_a < 0
    assert terms["R2"].signed_current_leaving_a > 0
    assert n2_report.residual_a <= 1e-8
    assert n2_report.passed is True


def test_current_divider_top_node_kcl_reports_source_entering_and_resistors_leaving():
    circuit = current_divider_problem()
    packet = solve_circuit(circuit, parser_used="fixture")

    view = build_analysis_view(circuit, packet)
    top_report = view.node_kcl["top"]
    terms = {term.component_id: term for term in top_report.terms}

    assert terms["I1"].direction == "entering"
    assert terms["R1"].direction == "leaving"
    assert terms["R2"].direction == "leaving"
    assert top_report.residual_a <= 1e-8
    assert top_report.passed is True


def test_balanced_bridge_reports_zero_r5_current_and_kcl_passes():
    circuit = bridge_network_problem()
    packet = solve_circuit(circuit, parser_used="fixture")

    view = build_analysis_view(circuit, packet)

    assert view.component_flows["R5"].is_zero_current is True
    assert abs(view.component_flows["R5"].current_a) <= 1e-12
    assert view.node_kcl["n2"].passed is True
    assert view.node_kcl["n3"].passed is True
    assert view.node_kcl["n2"].residual_a <= 1e-8
    assert view.node_kcl["n3"].residual_a <= 1e-8


def test_analysis_view_endpoint_returns_blocked_for_ambiguous_or_unsupported_packet():
    client = TestClient(app)
    for circuit in [
        CircuitProblem(
            id="ambiguous_request",
            title="Ambiguous Circuit Request",
            ground_node="0",
            nodes=["0"],
            ambiguities=["Topology and component values are not specified."],
        ),
        CircuitProblem(
            id="unsupported_request",
            title="Unsupported Circuit Request",
            ground_node="0",
            nodes=["0"],
            unsupported_features=["unsupported transient source"],
        ),
    ]:
        packet = solve_circuit(circuit, parser_used="fixture")

        response = client.post(
            "/analysis_view",
            json={
                "circuit_ir": circuit.model_dump(),
                "solution_packet": packet.model_dump(),
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "blocked"
        assert payload["component_flows"] == {}
        assert payload["node_kcl"] == {}
        assert payload["reason"] == "Analysis view is unavailable because the solution is not verified."


def test_analysis_view_does_not_alter_solver_output():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit, parser_used="fixture")
    before = packet.model_dump()

    build_analysis_view(circuit, packet)

    assert packet.model_dump() == before
