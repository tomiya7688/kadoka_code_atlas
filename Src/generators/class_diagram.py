"""Class diagram logical generation over Common IR and shared partitioning."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.class_relations import ClassRelationGraph, build_class_relation_graph
from Src.analyzers.ir import EntityKind, ModuleIR, Visibility
from Src.analyzers.ir_queries import classes, qualified_name
from Src.analyzers.partition import partition_graph
from Src.models.class_diagram import (
    ClassDiagram,
    ClassDiagramBundle,
    ClassMember,
    ClassNode,
    ClassRelation,
)


@dataclass(frozen=True, slots=True)
class ClassDiagramOptions:
    include_public: bool = True
    include_protected: bool = True
    include_internal: bool = True
    include_private: bool = True
    include_methods: bool = True
    include_inheritance: bool = True
    include_uses: bool = True

    def includes_visibility(self, visibility: Visibility) -> bool:
        return {
            Visibility.PUBLIC: self.include_public,
            Visibility.PROTECTED: self.include_protected,
            Visibility.INTERNAL: self.include_internal,
            Visibility.PRIVATE: self.include_private,
            Visibility.UNSPECIFIED: True,
        }[visibility]


def build_class_diagram_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
    options: ClassDiagramOptions | None = None,
) -> ClassDiagramBundle:
    """Generate caller-centered series plus callee-centered shared diagrams."""
    options = options or ClassDiagramOptions()
    graph = build_class_relation_graph(module)
    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    class_entities = {qualified_name(entity): entity for entity in classes(module)}
    methods_by_class: dict[str, list] = {name: [] for name in class_entities}
    for entity in module.entities:
        if entity.kind is EntityKind.METHOD and entity.parent in methods_by_class:
            methods_by_class[entity.parent].append(entity)

    visible_relations = [
        edge
        for edge in graph.edges
        if (edge.relation != "inheritance" or options.include_inheritance)
        and (edge.relation != "uses" or options.include_uses)
    ]

    def node_model(name: str) -> ClassNode:
        entity = class_entities.get(name)
        if entity is None:
            return ClassNode(name=name, external=True)
        members: list[ClassMember] = []
        if options.include_methods:
            for method in methods_by_class.get(name, ()):
                if not options.includes_visibility(method.visibility):
                    continue
                members.append(
                    ClassMember(
                        method.name,
                        method.parameters,
                        method.visibility.value,
                    )
                )
        return ClassNode(name=name, members=tuple(members))

    def relation_model(edge) -> ClassRelation:
        return ClassRelation(edge.caller, edge.callee, edge.relation)

    diagrams: list[ClassDiagram] = []
    for index, series in enumerate(partition.series, start=1):
        selected = set(series)
        relations = tuple(
            relation_model(edge)
            for edge in visible_relations
            if edge.caller in selected and edge.callee in selected
        )
        diagrams.append(
            ClassDiagram(
                name=f"series_{index}_{_slug(series[0])}",
                nodes=tuple(node_model(name) for name in series),
                relations=relations,
            )
        )

    for shared in partition.shared:
        incoming = [edge for edge in visible_relations if edge.callee == shared]
        selected = {shared, *(edge.caller for edge in incoming)}
        diagrams.append(
            ClassDiagram(
                name=f"shared_{_slug(shared)}",
                nodes=tuple(node_model(name) for name in sorted(selected)),
                relations=tuple(relation_model(edge) for edge in incoming),
            )
        )

    return ClassDiagramBundle(tuple(diagrams), partition.statistics)


def _slug(value: str) -> str:
    result = "".join(character if character.isalnum() else "_" for character in value)
    return result.strip("_") or "diagram"
