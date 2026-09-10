"""Language-independent call graph analysis built from ModuleIR."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .ir import ModuleIR


@dataclass(frozen=True, slots=True)
class CallEdge:
    caller: str
    callee: str
    call_type: str = "direct"


@dataclass(slots=True)
class CallGraph:
    edges: list[CallEdge] = field(default_factory=list)

    @classmethod
    def from_module(cls, module: ModuleIR) -> "CallGraph":
        edges: list[CallEdge] = []
        for entity in module.functions():
            for callee in entity.calls:
                edges.append(CallEdge(entity.qualified_name, callee))
        return cls(edges)

    @property
    def nodes(self) -> set[str]:
        return {name for edge in self.edges for name in (edge.caller, edge.callee)}

    def fan_in(self) -> dict[str, int]:
        callers: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            callers[edge.callee].add(edge.caller)
        return {node: len(callers[node]) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        callees: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            callees[edge.caller].add(edge.callee)
        return {node: len(callees[node]) for node in self.nodes}

    def outgoing(self, caller: str) -> list[CallEdge]:
        return [edge for edge in self.edges if edge.caller == caller]

    def incoming(self, callee: str) -> list[CallEdge]:
        return [edge for edge in self.edges if edge.callee == callee]

    def reachable_from(self, root: str, max_depth: int | None = None) -> "CallGraph":
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be >= 0 or None")

        selected: list[CallEdge] = []
        seen_edges: set[CallEdge] = set()
        visited_depth: dict[str, int] = {root: 0}
        queue: list[tuple[str, int]] = [(root, 0)]

        while queue:
            node, depth = queue.pop(0)
            if max_depth is not None and depth >= max_depth:
                continue
            for edge in self.outgoing(node):
                if edge not in seen_edges:
                    selected.append(edge)
                    seen_edges.add(edge)
                next_depth = depth + 1
                previous = visited_depth.get(edge.callee)
                if previous is None or next_depth < previous:
                    visited_depth[edge.callee] = next_depth
                    queue.append((edge.callee, next_depth))

        return CallGraph(selected)

    def high_fan_in_nodes(self, threshold: int = 3) -> set[str]:
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        return {node for node, count in self.fan_in().items() if count >= threshold}

    def cycles(self) -> list[tuple[str, ...]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            adjacency[edge.caller].add(edge.callee)

        found: set[tuple[str, ...]] = set()

        def canonicalize(cycle: list[str]) -> tuple[str, ...]:
            body = cycle[:-1]
            rotations = [tuple(body[i:] + body[:i]) for i in range(len(body))]
            smallest = min(rotations)
            return smallest + (smallest[0],)

        def walk(node: str, path: list[str], active: set[str]) -> None:
            for nxt in adjacency.get(node, ()):
                if nxt in active:
                    start = path.index(nxt)
                    found.add(canonicalize(path[start:] + [nxt]))
                    continue
                if nxt in path:
                    continue
                walk(nxt, path + [nxt], active | {nxt})

        for node in sorted(self.nodes):
            walk(node, [node], {node})

        return sorted(found)
