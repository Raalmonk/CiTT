from __future__ import annotations

from collections import defaultdict

from app.models.circuit_ir import CircuitProblem, Component, is_ideal_op_amp_type


class CircuitGraph:
    def __init__(self, circuit: CircuitProblem) -> None:
        self.circuit = circuit
        self.ground = circuit.ground_node
        self.components_by_id = {component.id: component for component in circuit.components}
        self._node_components: dict[str, list[Component]] = defaultdict(list)
        for component in circuit.components:
            for node in component.nodes:
                self._node_components[node].append(component)

    @classmethod
    def from_circuit(cls, circuit: CircuitProblem) -> "CircuitGraph":
        return cls(circuit)

    def component(self, component_id: str) -> Component | None:
        return self.components_by_id.get(component_id)

    def components_at(self, node: str) -> list[Component]:
        return list(self._node_components.get(node, []))

    def components_of_type(self, component_type: str) -> list[Component]:
        return [component for component in self.circuit.components if component.type == component_type]

    def ideal_op_amps(self) -> list[Component]:
        return [
            component
            for component in self.circuit.components
            if is_ideal_op_amp_type(component.type)
        ]

    def two_terminal_components(self) -> list[Component]:
        return [component for component in self.circuit.components if len(component.nodes) == 2]

    def components_between(
        self,
        node_a: str,
        node_b: str,
        component_type: str | None = None,
    ) -> list[Component]:
        target = {node_a, node_b}
        return [
            component
            for component in self.two_terminal_components()
            if set(component.nodes) == target
            and (component_type is None or component.type == component_type)
        ]

    def first_between(
        self,
        node_a: str,
        node_b: str,
        component_type: str | None = None,
    ) -> Component | None:
        return next(iter(self.components_between(node_a, node_b, component_type)), None)

    def other_node(self, component: Component, node: str) -> str | None:
        if len(component.nodes) != 2 or node not in component.nodes:
            return None
        return component.nodes[1] if component.nodes[0] == node else component.nodes[0]

    def source_node(self, source: Component) -> str | None:
        if len(source.nodes) != 2 or self.ground not in source.nodes:
            return None
        return self.other_node(source, self.ground)

    def source_at_node(self, node: str, source_type: str | None = None) -> Component | None:
        for component in self.components_at(node):
            if component.type not in {"voltage_source", "current_source"}:
                continue
            if source_type is not None and component.type != source_type:
                continue
            if self.ground in component.nodes:
                return component
        return None

    def voltage_sources_to_ground(self) -> list[Component]:
        return [
            component
            for component in self.components_of_type("voltage_source")
            if self.ground in component.nodes
        ]

    def current_sources_to_ground(self) -> list[Component]:
        return [
            component
            for component in self.components_of_type("current_source")
            if self.ground in component.nodes
        ]
