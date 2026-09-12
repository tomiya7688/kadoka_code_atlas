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

    def fan_out(self) -> dict[str, int]: ...

    def cycles(self) -> list[tuple[str, ...]]: ...


@dataclass(frozen=True, slots=True)
class GraphPartition: 
    """Logical graph series and nodes separated as shared high fan-in entries."""

    series: tuple[tuple[str, ...], ...]
    shared: tuple[str, ...]
    cross_series_edge_count: int
    fan_in_distribution: tuple[int, ...]
    fan_out_distribution: tuple[int, ...]
    cycle_count: int

    @property
    def shared_node_count(self) -> int:
        return len(self.shared)

    @property
    def statistics(self) -> dict[str, int | tuple[int, ...]]:
        """Return evaluator-friendly partition metrics as plain values."""
        return {
            "series_count": self.series_count,
            "max_nodes_per_series": self.max_nodes_per_series,
            "cross_series_edge_count": self.cross_series_edge_count,
            "shared_node_count": self.shared_node_count,
            "fan_in_distribution": self.fan_in_distribution,
            "fan_out_distribution": self.fan_out_distribution,
            "cycle_count": self.cycle_count,
        }

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

    fan_in = graph.fan_in()
    fan_out = graph.fan_out()
    shared = frozenset(node for node, count in fan_in.items() if count >= fan_in_threshold)
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
    return GraphPartition(
        series_tuple,
        tuple(sorted(shared)),
        cross_edges,
        tuple(sorted(fan_in.get(node, 0) for node in graph.nodes)),
        tuple(sorted(fan_out.get(node, 0) for node in graph.nodes)),
        len(graph.cycles()),
    )
