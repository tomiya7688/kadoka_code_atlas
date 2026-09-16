"""Language-neutral component dependency aggregation."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.package_dependencies import (
    ModuleDependencyUnit,
    resolve_module_reference,
)


@dataclass(frozen=True, slots=True)
class ComponentDependencyUnit:
    module: ModuleDependencyUnit
    component: str


@dataclass(frozen=True, slots=True)
class ComponentDependencyEdge:
    caller: str
    callee: str


@dataclass(slots=True)
class ComponentDependencyGraph:
    nodes: set[str]
    edges: list[ComponentDependencyEdge]
    external_nodes: set[str]

    def _plain_graph(self) -> CallGraph:
        return CallGraph([CallEdge(item.caller, item.callee) for item in self.edges])

    def fan_in(self) -> dict[str, int]:
        counts = self._plain_graph().fan_in()
        return {node: counts.get(node, 0) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        counts = self._plain_graph().fan_out()
        return {node: counts.get(node, 0) for node in self.nodes}

    def cycles(self) -> list[tuple[str, ...]]:
        return self._plain_graph().cycles()


def build_component_dependency_graph(
    units: list[ComponentDependencyUnit],
) -> ComponentDependencyGraph:
    """Aggregate module imports to components and retain external dependencies."""

    module_units = [item.module for item in units]
    known_names = {item.name for item in module_units}
    component_by_module = {item.module.name: item.component for item in units}
    internal_components = set(component_by_module.values())
    external_nodes: set[str] = set()
    edges: list[ComponentDependencyEdge] = []
    seen: set[tuple[str, str]] = set()

    def add(source: str, target: str) -> None:
        if source == target:
            return
        key = (source, target)
        if key not in seen:
            seen.add(key)
            edges.append(ComponentDependencyEdge(*key))

    for item in units:
        source = item.component
        for reference in item.module.imports:
            target_module = resolve_module_reference(item.module, reference, known_names)
            if target_module:
                add(source, component_by_module[target_module])
                continue
            if reference.startswith("."):
                continue
            external_name = reference.split(".", 1)[0]
            if not external_name or external_name in internal_components:
                continue
            external = f"external:{external_name}"
            external_nodes.add(external)
            add(source, external)

    return ComponentDependencyGraph(
        nodes=internal_components | external_nodes,
        edges=edges,
        external_nodes=external_nodes,
    )
