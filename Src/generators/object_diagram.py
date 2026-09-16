"""Static object-diagram generation over Common IR and shared partitioning."""

from __future__ import annotations

from Src.analyzers.ir import ModuleIR
from Src.analyzers.object_relations import build_object_relation_graph, object_key
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name
from Src.generators.series_layout import regular_placement, shared_placement
from Src.models.object_diagram import (
    ObjectDiagram,
    ObjectDiagramBundle,
    ObjectField,
    ObjectNode,
    ObjectReference,
)
from Src.models.output_layout import OutputPlacement


def build_object_diagram_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
) -> ObjectDiagramBundle:
    """Build static object diagrams from normalized instance/reference facts."""

    graph = build_object_relation_graph(module)
    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    instances = {object_key(instance): instance for instance in module.objects}

    def node_model(key: str) -> ObjectNode:
        instance = instances[key]
        return ObjectNode(
            key=key,
            name=instance.name,
            type_name=instance.type_name,
            fields=tuple(ObjectField(name, value) for name, value in instance.values),
        )

    def reference_model(edge) -> ObjectReference:
        return ObjectReference(edge.caller, edge.callee, edge.label)

    diagrams: list[ObjectDiagram] = []
    placements: list[OutputPlacement] = []
    for series_index, series in enumerate(partition.series):
        selected = set(series)
        references = tuple(
            reference_model(edge)
            for edge in graph.edges
            if edge.caller in selected and edge.callee in selected
        )
        root = partition.series_roots[series_index]
        name = stable_output_name(
            f"series_{series_index + 1}",
            root,
            fallback="object",
        )
        diagrams.append(
            ObjectDiagram(
                name=name,
                nodes=tuple(node_model(key) for key in series),
                references=references,
            )
        )
        placements.append(regular_placement(name, partition, series_index))

    for shared in partition.shared:
        related = [
            edge
            for edge in graph.edges
            if edge.callee == shared or edge.caller == shared
        ]
        selected = {shared}
        for edge in related:
            selected.add(edge.caller)
            selected.add(edge.callee)
        name = stable_output_name("shared", shared, fallback="object")
        diagrams.append(
            ObjectDiagram(
                name=name,
                nodes=tuple(node_model(key) for key in sorted(selected)),
                references=tuple(reference_model(edge) for edge in related),
            )
        )
        placements.append(shared_placement(name, shared))

    return ObjectDiagramBundle(
        tuple(diagrams),
        partition.statistics,
        tuple(placements),
    )
