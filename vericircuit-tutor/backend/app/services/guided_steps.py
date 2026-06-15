from __future__ import annotations

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, TutorStep
from app.services.lesson_planner.ac_planner import build_ac_steps
from app.services.lesson_planner.bme_context import attach_bme_context_steps
from app.services.lesson_planner.dc_planner import build_dc_steps
from app.services.lesson_planner.graph import CircuitGraph
from app.services.lesson_planner.motifs import detect_motifs
from app.services.lesson_planner.rc_transient_planner import build_rc_transient_steps


def build_guided_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return []

    graph = CircuitGraph.from_circuit(circuit)
    motifs = detect_motifs(circuit, graph)

    if circuit.analysis_type == "dc_operating_point":
        steps = build_dc_steps(circuit, packet, graph, motifs)
    elif circuit.analysis_type in {"ac_steady_state", "ac_single_frequency", "ac_sweep"}:
        steps = build_ac_steps(circuit, packet, graph, motifs)
    elif circuit.analysis_type == "rc_transient":
        steps = build_rc_transient_steps(circuit, packet, graph, motifs)
    else:
        steps = []

    return attach_bme_context_steps(circuit, packet, steps, motifs)
