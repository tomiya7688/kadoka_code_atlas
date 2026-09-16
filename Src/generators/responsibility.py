"""Deterministic class responsibility table generation from Common IR."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from collections.abc import Sequence

from Src.analyzers.class_relations import ClassRelationGraph, build_class_relation_graph
from Src.analyzers.ir import CodeEntity, ModuleIR
from Src.analyzers.ir_queries import classes, qualified_name
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name


@dataclass(frozen=True, slots=True)
class ResponsibilityRow:
    class_name: str
    responsibility: str


@dataclass(frozen=True, slots=True)
class ResponsibilityTable:
    name: str
    rows: tuple[ResponsibilityRow, ...]


@dataclass(frozen=True, slots=True)
class ResponsibilityTableBundle:
    tables: tuple[ResponsibilityTable, ...]
    statistics: dict[str, int | tuple[int, ...]]


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


def to_markdown(rows_: Sequence[ResponsibilityRow]) -> str:
    lines = ["| Class | Responsibility |", "| --- | --- |"]
    lines.extend(f"| {row.class_name} | {row.responsibility} |" for row in rows_)
    return "\n".join(lines) + "\n"


def to_csv(rows_: Sequence[ResponsibilityRow]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["Class", "Responsibility"])
    writer.writerows((row.class_name, row.responsibility) for row in rows_)
    return output.getvalue()


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
    for index, series in enumerate(partition.series, start=1):
        selected = tuple(by_name[name] for name in series if name in by_name)
        if not selected:
            continue
        root = selected[0].class_name
        tables.append(
            ResponsibilityTable(
                name=stable_output_name(
                    f"series_{index}",
                    root,
                    fallback="responsibility",
                ),
                rows=selected,
            )
        )

    for shared in partition.shared:
        row = by_name.get(shared)
        if row is None:
            continue
        tables.append(
            ResponsibilityTable(
                name=stable_output_name("shared", shared, fallback="responsibility"),
                rows=(row,),
            )
        )

    return ResponsibilityTableBundle(tuple(tables), partition.statistics)


def partitions(module: ModuleIR) -> list[list[ResponsibilityRow]]:
    """Compatibility helper returning the shared partitioner's grouped rows."""
    bundle = build_responsibility_table_bundle(module)
    return [list(table.rows) for table in bundle.tables]
