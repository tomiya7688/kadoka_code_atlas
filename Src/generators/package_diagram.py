"""Renderer-neutral package/module diagrams built from dependency graphs."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.package_dependencies import PackageDependencyGraph
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name
from Src.generators.series_layout import regular_placement, shared_placement
from Src.models.output_layout import OutputPlacement


@dataclass(frozen=True, slots=True)
class PackageDiagramEdge:
    source: str
    target: str


@dataclass(frozen=True, slots=True)
class PackageDiagram:
    name: str
    nodes: tuple[str, ...]
    edges: tuple[PackageDiagramEdge, ...]
    cycle_nodes: tuple[str, ...] = ()
    isolated_nodes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PackageDiagramBundle:
    diagrams: tuple[PackageDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]
    placements: tuple[OutputPlacement, ...] = ()


def build_package_diagram_bundle(
    graph: PackageDependencyGraph,
    *,
    fan_in_threshold: int = 3,
) -> PackageDiagramBundle:
    """Partition one dependency graph into normal and shared package diagrams."""

    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    cycle_nodes = {node for cycle in graph.cycles() for node in cycle}
    isolated = set(graph.isolated_nodes())
    diagrams: list[PackageDiagram] = []
    placements: list[OutputPlacement] = []

    def make(prefix: str, logical_name: str, nodes: set[str]) -> PackageDiagram:
        edges = tuple(
            PackageDiagramEdge(item.caller, item.callee)
            for item in graph.edges
            if item.caller in nodes and item.callee in nodes
        )
        return PackageDiagram(
            name=stable_output_name(prefix, logical_name, fallback="package"),
            nodes=tuple(sorted(nodes)),
            edges=edges,
            cycle_nodes=tuple(sorted(nodes & cycle_nodes)),
            isolated_nodes=tuple(sorted(nodes & isolated)),
        )

    for series_index, series in enumerate(partition.series):
        nodes = set(series)
        if not nodes:
            continue
        diagram = make(
            f"series_{series_index + 1}",
            partition.series_roots[series_index],
            nodes,
        )
        diagrams.append(diagram)
        placements.append(regular_placement(diagram.name, partition, series_index))

    for shared in partition.shared:
        nodes = {shared}
        nodes.update(item.caller for item in graph.edges if item.callee == shared)
        nodes.update(item.callee for item in graph.edges if item.caller == shared)
        diagram = make("shared", shared, nodes)
        diagrams.append(diagram)
        placements.append(shared_placement(diagram.name, shared))

    statistics = dict(partition.statistics)
    statistics["isolated_node_count"] = len(isolated)
    return PackageDiagramBundle(tuple(diagrams), statistics, tuple(placements))
