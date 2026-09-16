"""Passive logical models used by class-diagram generators and renderers."""

from __future__ import annotations

from dataclasses import dataclass

from Src.models.output_layout import OutputPlacement


@dataclass(frozen=True, slots=True)
class ClassMember:
    name: str
    parameters: tuple[str, ...] = ()
    visibility: str = "unspecified"


@dataclass(frozen=True, slots=True)
class ClassNode:
    name: str
    members: tuple[ClassMember, ...] = ()
    external: bool = False


@dataclass(frozen=True, slots=True)
class ClassRelation:
    source: str
    target: str
    kind: str


@dataclass(frozen=True, slots=True)
class ClassDiagram:
    name: str
    nodes: tuple[ClassNode, ...]
    relations: tuple[ClassRelation, ...]


@dataclass(frozen=True, slots=True)
class ClassDiagramBundle:
    diagrams: tuple[ClassDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]
    placements: tuple[OutputPlacement, ...] = ()
