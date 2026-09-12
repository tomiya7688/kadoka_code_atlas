"""Queries and derived names kept outside the data-only Common IR."""

from __future__ import annotations

from collections.abc import Iterable

from Src.analyzers.ir import CodeEntity, EntityKind, ModuleIR


def qualified_name(entity: CodeEntity) -> str:
    return f"{entity.parent}.{entity.name}" if entity.parent else entity.name


def classes(module: ModuleIR) -> list[CodeEntity]:
    return [entity for entity in module.entities if entity.kind is EntityKind.CLASS]


def functions(module: ModuleIR) -> list[CodeEntity]:
    return [entity for entity in module.entities if entity.kind in {EntityKind.FUNCTION, EntityKind.METHOD}]
