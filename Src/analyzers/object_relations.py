"""Language-neutral object reference analysis over Common IR."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.ir import ModuleIR, ObjectInstanceIR


@dataclass(frozen=True, slots=True)
class ObjectRelationEdge:
    caller: str
    callee: str
    label: str


@dataclass(slots=True)
class ObjectRelationGraph:
    nodes: set[str] = field(default_factory=set)
    edges: list[ObjectRelationEdge] = field(default_factory=list)

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

    def cycles(self) -> list[tuple[str, ...]]:
        return CallGraph([CallEdge(edge.caller, edge.callee) for edge in self.edges]).cycles()


def object_key(instance: ObjectInstanceIR) -> str:
    scope = instance.scope or "<module>"
    return f"{scope}:{instance.name}"


def build_object_relation_graph(module: ModuleIR) -> ObjectRelationGraph:
    """Resolve static object references while preserving isolated objects."""

    by_key = {object_key(instance): instance for instance in module.objects}
    by_scope_name = {(instance.scope, instance.name): object_key(instance) for instance in module.objects}
    by_name: dict[str, list[str]] = defaultdict(list)
    for instance in module.objects:
        by_name[instance.name].append(object_key(instance))

    edges: list[ObjectRelationEdge] = []
    seen: set[tuple[str, str, str]] = set()
    for instance in module.objects:
        source = object_key(instance)
        for label, raw_target in instance.references:
            target = by_scope_name.get((instance.scope, raw_target))
            if target is None:
                candidates = by_name.get(raw_target, ())
                if len(candidates) == 1:
                    target = candidates[0]
            if target is None or target not in by_key:
                continue
            key = (source, target, label)
            if key in seen:
                continue
            seen.add(key)
            edges.append(ObjectRelationEdge(source, target, label))

    return ObjectRelationGraph(nodes=set(by_key), edges=edges)
