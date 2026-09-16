"""Renderer-neutral package/module diagrams built from dependency graphs."""

from __future__ import annotations

from dataclasses import dataclass
import re

from Src.analyzers.package_dependencies import PackageDependencyGraph
from Src.analyzers.partition import partition_graph


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
    statistics: dict[str, int | tuple[int, ...]]


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-")
    return normalized or "package"


def build_package_diagram_bundle(
    graph: PackageDependencyGraph,
    *,
    fan_in_threshold: int = 3,
) -> PackageDiagramBundle:
    """Partition one dependency graph into normal and shared package diagrams."""

    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    cycle_nodes = {
        node
        for cycle in graph.cycles()
        for node in cycle
    }
    isolated = set(graph.isolated_nodes())
    diagrams: list[PackageDiagram] = []

    def make(name: str, nodes: set[str]) -> PackageDiagram:
        edges = tuple(
            PackageDiagramEdge(item.caller, item.callee)
            for item in graph.edges
            if item.caller in nodes and item.callee in nodes
        )
        return PackageDiagram(
            name=_safe_name(name),
            nodes=tuple(sorted(nodes)),
            edges=edges,
            cycle_nodes=tuple(sorted(nodes & cycle_nodes)),
            isolated_nodes=tuple(sorted(nodes & isolated)),
        )

    for series in partition.series:
        nodes = set(series)
        if nodes:
            diagrams.append(make(f"series_{series[0]}", nodes))

    for shared in partition.shared:
        nodes = {shared}
        nodes.update(item.caller for item in graph.edges if item.callee == shared)
        nodes.update(item.callee for item in graph.edges if item.caller == shared)
        diagrams.append(make(f"shared_{shared}", nodes))

    statistics = dict(partition.statistics)
    statistics["isolated_node_count"] = len(isolated)
    return PackageDiagramBundle(tuple(diagrams), statistics)
