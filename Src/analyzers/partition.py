"""Format-independent recursive partitioning for relation graphs."""

from __future__ import annotations

from collections import deque
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
    """Logical graph series plus evaluator-friendly partition metadata."""

    series: tuple[tuple[str, ...], ...]
    shared: tuple[str, ...]
    cross_series_edge_count: int
    fan_in_distribution: tuple[int, ...]
    fan_out_distribution: tuple[int, ...]
    cycle_count: int
    series_roots: tuple[str, ...] = ()
    series_depths: tuple[int, ...] = ()
    series_parents: tuple[str | None, ...] = ()
    regular_edge_count: int = 0
    total_node_count: int = 0

    @property
    def shared_node_count(self) -> int:
        return len(self.shared)

    @property
    def series_count(self) -> int:
        return len(self.series)

    @property
    def max_nodes_per_series(self) -> int:
        return max((len(item) for item in self.series), default=0)

    @property
    def max_partition_depth(self) -> int:
        return max(self.series_depths, default=0)

    @property
    def avg_nodes_per_series(self) -> float:
        if not self.series:
            return 0.0
        return sum(len(item) for item in self.series) / len(self.series)

    @property
    def cross_series_edge_ratio(self) -> float:
        if not self.regular_edge_count:
            return 0.0
        return self.cross_series_edge_count / self.regular_edge_count

    @property
    def shared_node_ratio(self) -> float:
        if not self.total_node_count:
            return 0.0
        return self.shared_node_count / self.total_node_count

    @property
    def statistics(self) -> dict[str, int | float | tuple[int, ...]]:
        """Return evaluator-friendly partition metrics as plain values."""
        return {
            "series_count": self.series_count,
            "max_nodes_per_series": self.max_nodes_per_series,
            "avg_nodes_per_series": self.avg_nodes_per_series,
            "max_partition_depth": self.max_partition_depth,
            "cross_series_edge_count": self.cross_series_edge_count,
            "cross_series_edge_ratio": self.cross_series_edge_ratio,
            "shared_node_count": self.shared_node_count,
            "shared_node_ratio": self.shared_node_ratio,
            "fan_in_distribution": self.fan_in_distribution,
            "fan_out_distribution": self.fan_out_distribution,
            "cycle_count": self.cycle_count,
        }


def partition_graph(
    graph: RelationGraph,
    *,
    fan_in_threshold: int = 3,
    min_child_series_size: int = 3,
) -> GraphPartition:
    """Recursively split caller-centered closed branches and shared dependency hubs.

    High fan-in nodes are removed into ``shared`` first. Regular weak components are
    then examined for locally closed child branches. A branch is separated only when
    its parent actually branches (fan-out >= 2), the child region is large enough,
    exactly one edge enters it from the parent, and no edge leaves it. This keeps
    simple call chains stable while allowing nested feature branches to become their
    own readable series.
    """
    if fan_in_threshold < 1:
        raise ValueError("fan_in_threshold must be >= 1")
    if min_child_series_size < 2:
        raise ValueError("min_child_series_size must be >= 2")

    fan_in = graph.fan_in()
    fan_out = graph.fan_out()
    shared = frozenset(
        node for node, count in fan_in.items() if count >= fan_in_threshold
    )
    regular_nodes = set(graph.nodes) - shared
    regular_edges = [
        edge
        for edge in graph.edges
        if edge.caller in regular_nodes and edge.callee in regular_nodes
    ]
    cycles = graph.cycles()
    cycle_nodes = {
        node
        for cycle in cycles
        for node in (cycle[:-1] if len(cycle) > 1 and cycle[0] == cycle[-1] else cycle)
    }

    records: list[tuple[tuple[str, ...], str, int, str | None]] = []
    for component in _weak_components(regular_nodes, regular_edges):
        records.extend(
            _split_component(
                component,
                regular_edges,
                cycle_nodes,
                depth=0,
                parent_root=None,
                root_hint=None,
                min_child_series_size=min_child_series_size,
            )
        )

    series_tuple = tuple(record[0] for record in records)
    roots = tuple(record[1] for record in records)
    depths = tuple(record[2] for record in records)
    parents = tuple(record[3] for record in records)
    series_by_node = {
        node: index for index, item in enumerate(series_tuple) for node in item
    }
    cross_edges = sum(
        1
        for edge in regular_edges
        if series_by_node.get(edge.caller) != series_by_node.get(edge.callee)
    )

    return GraphPartition(
        series=series_tuple,
        shared=tuple(sorted(shared)),
        cross_series_edge_count=cross_edges,
        fan_in_distribution=tuple(
            sorted(fan_in.get(node, 0) for node in graph.nodes)
        ),
        fan_out_distribution=tuple(
            sorted(fan_out.get(node, 0) for node in graph.nodes)
        ),
        cycle_count=len(cycles),
        series_roots=roots,
        series_depths=depths,
        series_parents=parents,
        regular_edge_count=len(regular_edges),
        total_node_count=len(graph.nodes),
    )


def _weak_components(
    nodes: set[str],
    edges: Sequence[RelationEdge],
) -> list[set[str]]:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        adjacency[edge.caller].add(edge.callee)
        adjacency[edge.callee].add(edge.caller)

    components: list[set[str]] = []
    remaining = set(nodes)
    while remaining:
        start = min(remaining)
        stack = [start]
        component: set[str] = set()
        while stack:
            node = stack.pop()
            if node not in remaining:
                continue
            remaining.remove(node)
            component.add(node)
            stack.extend(sorted(adjacency[node] & remaining, reverse=True))
        components.append(component)
    components.sort(key=lambda item: min(item))
    return components


def _split_component(
    component: set[str],
    edges: Sequence[RelationEdge],
    cycle_nodes: set[str],
    *,
    depth: int,
    parent_root: str | None,
    root_hint: str | None,
    min_child_series_size: int,
) -> list[tuple[tuple[str, ...], str, int, str | None]]:
    internal_edges = [
        edge
        for edge in edges
        if edge.caller in component and edge.callee in component
    ]
    outgoing: dict[str, set[str]] = {node: set() for node in component}
    incoming: dict[str, set[str]] = {node: set() for node in component}
    for edge in internal_edges:
        outgoing[edge.caller].add(edge.callee)
        incoming[edge.callee].add(edge.caller)

    roots = sorted(node for node in component if not incoming[node])
    root = root_hint if root_hint in component else (roots[0] if roots else min(component))
    distances = _directed_distances(root, outgoing)

    candidates: list[tuple[int, str, str, set[str]]] = []
    for parent in sorted(component):
        if len(outgoing[parent]) < 2:
            continue
        for child in sorted(outgoing[parent]):
            subtree = _reachable(child, outgoing)
            if len(subtree) < min_child_series_size or subtree == component:
                continue
            if subtree & cycle_nodes:
                continue
            boundary_in = [
                edge
                for edge in internal_edges
                if edge.callee in subtree and edge.caller not in subtree
            ]
            boundary_out = [
                edge
                for edge in internal_edges
                if edge.caller in subtree and edge.callee not in subtree
            ]
            if boundary_out:
                continue
            if len(boundary_in) != 1:
                continue
            entrance = boundary_in[0]
            if entrance.caller != parent or entrance.callee != child:
                continue
            candidates.append(
                (distances.get(parent, len(component) + 1), parent, child, subtree)
            )

    selected: list[tuple[str, str, set[str]]] = []
    occupied: set[str] = set()
    for _, parent, child, subtree in sorted(
        candidates,
        key=lambda item: (item[0], item[1], item[2], -len(item[3])),
    ):
        if subtree & occupied:
            continue
        selected.append((parent, child, subtree))
        occupied.update(subtree)

    local_nodes = component - occupied
    if not local_nodes:
        local_nodes = set(component)
        selected = []

    records = [(tuple(sorted(local_nodes)), root, depth, parent_root)]
    for _, child, subtree in selected:
        records.extend(
            _split_component(
                subtree,
                internal_edges,
                cycle_nodes,
                depth=depth + 1,
                parent_root=root,
                root_hint=child,
                min_child_series_size=min_child_series_size,
            )
        )
    return records


def _directed_distances(
    root: str,
    outgoing: dict[str, set[str]],
) -> dict[str, int]:
    distances = {root: 0}
    queue: deque[str] = deque([root])
    while queue:
        node = queue.popleft()
        for child in sorted(outgoing[node]):
            if child in distances:
                continue
            distances[child] = distances[node] + 1
            queue.append(child)
    return distances


def _reachable(start: str, outgoing: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in result:
            continue
        result.add(node)
        stack.extend(sorted(outgoing[node] - result, reverse=True))
    return result
