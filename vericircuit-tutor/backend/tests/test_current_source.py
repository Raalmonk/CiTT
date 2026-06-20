import pytest

from app.services.demo_parser import current_divider_problem
from app.services.pipeline import solve_circuit


def test_current_source_parallel_resistors():
    circuit = current_divider_problem()
    packet = solve_circuit(circuit)

    assert packet.status == "solved"
    assert packet.verification.passed
    assert packet.node_voltages["top"] == pytest.approx(2.0)
    assert packet.component_results["R1"].current.value == pytest.approx(0.001)
    assert packet.component_results["R2"].current.value == pytest.approx(0.002)
    assert packet.component_results["I1"].power.value == pytest.approx(-0.006)
