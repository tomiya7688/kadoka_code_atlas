"""Language-neutral class relation analysis built from Common IR."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.ir import EntityKind, ModuleIR
from Src.analyzers.ir_queries import classes, qualified_name


@dataclass(frozen=True, slots=True)
class ClassRelationEdge:
    caller: str
    callee: str
    relation: str


@dataclass(slots=True)
class ClassRelationGraph:
    nodes: set[str]
    edges: list[ClassRelationEdge]

    def _plain_graph(self) -> CallGraph:
        return CallGraph([CallEdge(edge.caller, edge.callee) for edge in self.edges])

    def fan_in(self) -> dict[str, int]:
        counts = self._plain_graph().fan_in()
        return {node: counts.get(node, 0) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        counts = self._plain_graph().fan_out()
        return {node: counts.get(node, 0) for node in self.nodes}

    def cycles(self) -> list[tuple[str, ...]]:
        return self._plain_graph().cycles()


def build_class_relation_graph(module: ModuleIR) -> ClassRelationGraph:
    """Build inheritance and class-use relations without touching language ASTs."""
    class_entities = classes(module)
    known = {qualified_name(entity): entity for entity in class_entities}
    simple: dict[str, list[str]] = {}
    for name in known:
        simple.setdefault(name.rsplit(".", 1)[-1], []).append(name)

    def resolve(reference: str) -> str | None:
        if reference in known:
            return reference
        parts = reference.split(".")
        for end in range(len(parts), 0, -1):
            candidate = ".".join(parts[:end])
            if candidate in known:
                return candidate
            matches = simple.get(parts[end - 1], ())
            if len(matches) == 1:
                return matches[0]
        return None

    edges: list[ClassRelationEdge] = []
    seen: set[tuple[str, str, str]] = set()
    external_nodes: set[str] = set()

    def add(source: str, target: str, relation: str) -> None:
        if source == target:
            return
        key = (source, target, relation)
        if key not in seen:
            seen.add(key)
            edges.append(ClassRelationEdge(source, target, relation))

    for entity in class_entities:
        source = qualified_name(entity)
        for base in entity.bases:
            target = resolve(base) or base
            if target and target not in known:
                external_nodes.add(target)
            if target:
                add(source, target, "inheritance")

    for entity in module.entities:
        if entity.kind is not EntityKind.METHOD or not entity.parent:
            continue
        if entity.parent not in known:
            continue
        for call in entity.calls:
            target = resolve(call)
            if target:
                add(entity.parent, target, "uses")

    return ClassRelationGraph(set(known) | external_nodes, edges)
