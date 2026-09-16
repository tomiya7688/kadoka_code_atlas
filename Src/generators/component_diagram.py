"""Renderer-neutral component diagrams built from aggregated dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.component_dependencies import ComponentDependencyGraph
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name
from Src.generators.series_layout import regular_placement, shared_placement
from Src.models.output_layout import OutputPlacement


@dataclass(frozen=True, slots=True)
class ComponentDiagramNode:
    name: str
    external: bool = False


@dataclass(frozen=True, slots=True)
class ComponentDiagramEdge:
    source: str
    target: str


@dataclass(frozen=True, slots=True)
class ComponentDiagram:
    name: str
    nodes: tuple[ComponentDiagramNode, ...]
    edges: tuple[ComponentDiagramEdge, ...]
    cycle_nodes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComponentDiagramBundle:
    diagrams: tuple[ComponentDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]
    placements: tuple[OutputPlacement, ...] = ()


def build_component_diagram_bundle(
    graph: ComponentDependencyGraph,
    *,
    fan_in_threshold: int = 3,
) -> ComponentDiagramBundle:
    """Partition aggregated component dependencies with shared hubs separated."""

    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    cycle_nodes = {node for cycle in graph.cycles() for node in cycle}
    diagrams: list[ComponentDiagram] = []
    placements: list[OutputPlacement] = []

    def make(prefix: str, logical_name: str, names: set[str]) -> ComponentDiagram:
        return ComponentDiagram(
            name=stable_output_name(prefix, logical_name, fallback="component"),
            nodes=tuple(
                ComponentDiagramNode(node, node in graph.external_nodes)
                for node in sorted(names)
            ),
            edges=tuple(
                ComponentDiagramEdge(item.caller, item.callee)
                for item in graph.edges
                if item.caller in names and item.callee in names
            ),
            cycle_nodes=tuple(sorted(names & cycle_nodes)),
        )

    for series_index, series in enumerate(partition.series):
        names = set(series)
        if not names:
            continue
        diagram = make(
            f"series_{series_index + 1}",
            partition.series_roots[series_index],
            names,
        )
        diagrams.append(diagram)
        placements.append(regular_placement(diagram.name, partition, series_index))

    for shared in partition.shared:
        names = {shared}
        names.update(item.caller for item in graph.edges if item.callee == shared)
        names.update(item.callee for item in graph.edges if item.caller == shared)
        diagram = make("shared", shared, names)
        diagrams.append(diagram)
        placements.append(shared_placement(diagram.name, shared))

    statistics = dict(partition.statistics)
    statistics["external_node_count"] = len(graph.external_nodes)
    return ComponentDiagramBundle(tuple(diagrams), statistics, tuple(placements))
