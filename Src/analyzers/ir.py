"""Language-independent intermediate representation used by analyzers and generators."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EntityKind(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


@dataclass(slots=True)
class CodeEntity:
    """A source entity normalized from a language-specific syntax tree."""

    kind: EntityKind
    name: str
    line: int
    end_line: int
    indent: int = 0
    parent: str | None = None
    docstring: str | None = None
    parameters: tuple[str, ...] = ()
    decorators: tuple[str, ...] = ()
    calls: tuple[str, ...] = ()

    @property
    def qualified_name(self) -> str:
        return f"{self.parent}.{self.name}" if self.parent else self.name


@dataclass(slots=True)
class ModuleIR:
    """Normalized representation of one source module/file."""

    language: str
    entities: list[CodeEntity] = field(default_factory=list)

    def classes(self) -> list[CodeEntity]:
        return [entity for entity in self.entities if entity.kind is EntityKind.CLASS]

    def functions(self) -> list[CodeEntity]:
        return [
            entity
            for entity in self.entities
            if entity.kind in {EntityKind.FUNCTION, EntityKind.METHOD}
        ]
