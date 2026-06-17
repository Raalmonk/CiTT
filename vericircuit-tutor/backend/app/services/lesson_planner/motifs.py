from __future__ import annotations

from dataclasses import dataclass, field

from app.models.circuit_ir import CircuitProblem, Component
from app.services.lesson_planner.graph import CircuitGraph


@dataclass(frozen=True)
class VoltageDividerMotif:
    source_id: str
    top_node: str
    output_node: str
    ground_node: str
    upper_resistor_id: str
    lower_resistor_id: str


@dataclass(frozen=True)
class RCLowPassMotif:
    source_id: str
    input_node: str
    output_node: str
    ground_node: str
    resistor_id: str
    capacitor_id: str


@dataclass(frozen=True)
class TransimpedanceMotif:
    op_amp_id: str
    current_source_id: str
    feedback_resistor_id: str
    summing_node: str
    output_node: str
    reference_node: str


@dataclass(frozen=True)
class DifferentialAmpMotif:
    op_amp_id: str
    positive_source_id: str
    negative_source_id: str
    positive_input_node: str
    negative_input_node: str
    op_amp_plus_node: str
    op_amp_minus_node: str
    output_node: str
    feedback_resistor_id: str
    negative_input_resistor_id: str
    positive_input_resistor_id: str
    reference_resistor_id: str | None = None


@dataclass(frozen=True)
class CircuitMotifs:
    voltage_dividers: list[VoltageDividerMotif] = field(default_factory=list)
    rc_low_passes: list[RCLowPassMotif] = field(default_factory=list)
    transimpedance: TransimpedanceMotif | None = None
    differential_amp: DifferentialAmpMotif | None = None


def detect_motifs(circuit: CircuitProblem, graph: CircuitGraph) -> CircuitMotifs:
    return CircuitMotifs(
        voltage_dividers=_detect_voltage_dividers(graph),
        rc_low_passes=_detect_rc_low_passes(graph),
        transimpedance=_detect_transimpedance(graph),
        differential_amp=_detect_differential_amp(graph),
    )


def _detect_voltage_dividers(graph: CircuitGraph) -> list[VoltageDividerMotif]:
    motifs: list[VoltageDividerMotif] = []
    for source in graph.voltage_sources_to_ground():
        top_node = graph.source_node(source)
        if top_node is None:
            continue
        for upper in graph.components_at(top_node):
            if upper.type != "resistor" or len(upper.nodes) != 2:
                continue
            output_node = graph.other_node(upper, top_node)
            if output_node is None or output_node == graph.ground:
                continue
            for lower in graph.components_between(output_node, graph.ground, "resistor"):
                output_components = {component.id for component in graph.components_at(output_node)}
                if output_components != {upper.id, lower.id}:
                    continue
                motifs.append(
                    VoltageDividerMotif(
                        source_id=source.id,
                        top_node=top_node,
                        output_node=output_node,
                        ground_node=graph.ground,
                        upper_resistor_id=upper.id,
                        lower_resistor_id=lower.id,
                    )
                )
    return motifs


def _detect_rc_low_passes(graph: CircuitGraph) -> list[RCLowPassMotif]:
    motifs: list[RCLowPassMotif] = []
    for source in graph.voltage_sources_to_ground():
        input_node = graph.source_node(source)
        if input_node is None:
            continue
        for resistor in graph.components_at(input_node):
            if resistor.type != "resistor" or len(resistor.nodes) != 2:
                continue
            output_node = graph.other_node(resistor, input_node)
            if output_node is None or output_node == graph.ground:
                continue
            for capacitor in graph.components_between(output_node, graph.ground, "capacitor"):
                motifs.append(
                    RCLowPassMotif(
                        source_id=source.id,
                        input_node=input_node,
                        output_node=output_node,
                        ground_node=graph.ground,
                        resistor_id=resistor.id,
                        capacitor_id=capacitor.id,
                    )
                )
    return motifs


def _detect_transimpedance(graph: CircuitGraph) -> TransimpedanceMotif | None:
    for op_amp in graph.ideal_op_amps():
        plus_node, minus_node, output_node, reference_node = op_amp.nodes
        if plus_node != graph.ground and reference_node != graph.ground:
            continue
        feedback = graph.first_between(output_node, minus_node, "resistor")
        if feedback is None:
            continue
        current_source = graph.first_between(minus_node, graph.ground, "current_source")
        if current_source is None:
            continue
        return TransimpedanceMotif(
            op_amp_id=op_amp.id,
            current_source_id=current_source.id,
            feedback_resistor_id=feedback.id,
            summing_node=minus_node,
            output_node=output_node,
            reference_node=plus_node,
        )
    return None


def _source_node_for_grounded_voltage_source(graph: CircuitGraph, node: str) -> Component | None:
    source = graph.source_at_node(node, source_type="voltage_source")
    if source is None or graph.ground not in source.nodes:
        return None
    return source


def _detect_differential_amp(graph: CircuitGraph) -> DifferentialAmpMotif | None:
    for op_amp in graph.ideal_op_amps():
        plus_node, minus_node, output_node, _reference_node = op_amp.nodes
        feedback = graph.first_between(output_node, minus_node, "resistor")
        if feedback is None:
            continue

        negative_input_resistor = _input_resistor_from_grounded_source(graph, minus_node)
        positive_input_resistor = _input_resistor_from_grounded_source(graph, plus_node)
        if negative_input_resistor is None or positive_input_resistor is None:
            continue

        negative_input_node = graph.other_node(negative_input_resistor, minus_node)
        positive_input_node = graph.other_node(positive_input_resistor, plus_node)
        if negative_input_node is None or positive_input_node is None:
            continue

        negative_source = _source_node_for_grounded_voltage_source(graph, negative_input_node)
        positive_source = _source_node_for_grounded_voltage_source(graph, positive_input_node)
        if negative_source is None or positive_source is None:
            continue

        reference_resistor = graph.first_between(plus_node, graph.ground, "resistor")
        return DifferentialAmpMotif(
            op_amp_id=op_amp.id,
            positive_source_id=positive_source.id,
            negative_source_id=negative_source.id,
            positive_input_node=positive_input_node,
            negative_input_node=negative_input_node,
            op_amp_plus_node=plus_node,
            op_amp_minus_node=minus_node,
            output_node=output_node,
            feedback_resistor_id=feedback.id,
            negative_input_resistor_id=negative_input_resistor.id,
            positive_input_resistor_id=positive_input_resistor.id,
            reference_resistor_id=reference_resistor.id if reference_resistor else None,
        )
    return None


def _input_resistor_from_grounded_source(graph: CircuitGraph, op_amp_input_node: str) -> Component | None:
    for component in graph.components_at(op_amp_input_node):
        if component.type != "resistor" or len(component.nodes) != 2:
            continue
        source_node = graph.other_node(component, op_amp_input_node)
        if source_node is None:
            continue
        if _source_node_for_grounded_voltage_source(graph, source_node) is not None:
            return component
    return None
