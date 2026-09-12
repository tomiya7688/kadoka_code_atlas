"""Format-independent partitioning for relation graphs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class RelationEdge(Protocol):
    caller: str
    callee: str


class RelationGraph(Protocol):
    nodes: set[str]
    edges: Sequence[RelationEdge]

    def fan_in(self) -> dict[str, int]: ...


@dataclass(frozen=True, slots=True)
class GraphPartition: 
    """Logical graph series and nodes separated as shared high fan-in entries."""

    series: tuple[tuple[str, ...], ...]
    shared: tuple[str, ...]
    cross_series_edge_count: int

    @property
    def series_count(self) -> int:
        return len(self.series)

    @property
    def max_nodes_per_series(self) -> int:
        return max((len(item) for item in self.series), default=0)


def partition_graph(graph: RelationGraph, *, fan_in_threshold: int = 3) -> GraphPartition:
    """Split a graph into connected caller/dependency series and shared nodes."""
    if fan_in_threshold < 1:
        raise ValueError("fan_in_threshold must be >= 1")

    shared = frozenset(
        node for node, count in graph.fan_in().items() if count >= fan_in_threshold
    )
    adjacency: dict[str, set[str]] = {node: set() for node in graph.nodes if node not in shared}
    for edge in graph.edges:
        if edge.caller in adjacency and edge.callee in adjacency:
            adjacency[edge.caller].add(edge.callee)
            adjacency[edge.callee].add(edge.caller)

    series: list[tuple[str, ...]] = []
    remaining = set(adjacency)
    while remaining:
        root = min(remaining)
        stack = [root]
        component: set[str] = set()
        while stack:
            node = stack.pop()
            if node not in remaining:
                continue
            remaining.remove(node)
            component.add(node)
            stack.extend(adjacency[node] & remaining)
        series.append(tuple(sorted(component)))

    series.sort(key=lambda item: item[0])
    series_tuple = tuple(series)
    series_by_node = {node: index for index, item in enumerate(series_tuple) for node in item}
    cross_edges = sum(
        1
        for edge in graph.edges
        if edge.caller in series_by_node
        and edge.callee in series_by_node
        and series_by_node[edge.caller] != series_by_node[edge.callee]
    )
    return GraphPartition(series_tuple, tuple(sorted(shared)), cross_edges)
