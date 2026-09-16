"""Deterministic class responsibility table generation from Common IR."""

from __future__ import annotations

import re

from Src.analyzers.class_relations import ClassRelationGraph, build_class_relation_graph
from Src.analyzers.ir import CodeEntity, ModuleIR
from Src.analyzers.ir_queries import classes, qualified_name
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name
from Src.generators.series_layout import regular_placement, shared_placement
from Src.models.output_layout import OutputPlacement
from Src.models.responsibility import ResponsibilityRow, ResponsibilityTable


class ResponsibilityTableBundle:
    __slots__ = ("tables", "statistics", "placements")

    def __init__(
        self,
        tables: tuple[ResponsibilityTable, ...],
        statistics: dict[str, int | float | tuple[int, ...]],
        placements: tuple[OutputPlacement, ...] = (),
    ) -> None:
        self.tables = tables
        self.statistics = statistics
        self.placements = placements


def _words(name: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).strip("_")
    return [item.lower() for item in normalized.split("_") if item]


def _describe(entity: CodeEntity, methods: list[CodeEntity]) -> str:
    if entity.docstring:
        return entity.docstring.splitlines()[0].strip()
    words = " ".join(_words(entity.name))
    names = {method.name.lower() for method in methods}
    if names & {"load", "read", "save", "write"}:
        return f"Handles {words} data input and output."
    if names & {"update", "process", "run", "execute"}:
        return f"Coordinates {words} processing."
    if names & {"validate", "check", "evaluate"}:
        return f"Validates or evaluates {words} state."
    return f"Manages {words} state and behavior."


def rows(module: ModuleIR) -> list[ResponsibilityRow]:
    result: list[ResponsibilityRow] = []
    for class_entity in classes(module):
        class_name = qualified_name(class_entity)
        methods = [
            entity
            for entity in module.entities
            if entity.parent == class_name and entity.kind.value == "method"
        ]
        result.append(ResponsibilityRow(class_name, _describe(class_entity, methods)))
    return result


def build_responsibility_table_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
) -> ResponsibilityTableBundle:
    """Partition responsibility tables with the shared diagram partitioner."""

    generated_rows = rows(module)
    by_name = {row.class_name: row for row in generated_rows}
    relation_graph = build_class_relation_graph(module)
    graph = ClassRelationGraph(
        nodes=set(by_name),
        edges=[
            edge
            for edge in relation_graph.edges
            if edge.caller in by_name and edge.callee in by_name
        ],
    )
    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)

    tables: list[ResponsibilityTable] = []
    placements: list[OutputPlacement] = []
    for series_index, series in enumerate(partition.series):
        selected = tuple(by_name[name] for name in series if name in by_name)
        if not selected:
            continue
        root = partition.series_roots[series_index]
        name = stable_output_name(
            f"series_{series_index + 1}",
            root,
            fallback="responsibility",
        )
        tables.append(ResponsibilityTable(name=name, rows=selected))
        placements.append(regular_placement(name, partition, series_index))

    for shared in partition.shared:
        row = by_name.get(shared)
        if row is None:
            continue
        name = stable_output_name("shared", shared, fallback="responsibility")
        tables.append(ResponsibilityTable(name=name, rows=(row,)))
        placements.append(shared_placement(name, shared))

    return ResponsibilityTableBundle(
        tuple(tables),
        partition.statistics,
        tuple(placements),
    )


def partitions(module: ModuleIR) -> list[list[ResponsibilityRow]]:
    """Compatibility helper returning the shared partitioner's grouped rows."""
    bundle = build_responsibility_table_bundle(module)
    return [list(table.rows) for table in bundle.tables]
