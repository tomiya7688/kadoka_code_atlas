"""Renderer-neutral logical models for object diagrams."""

from __future__ import annotations

from dataclasses import dataclass

from Src.models.output_layout import OutputPlacement


@dataclass(frozen=True, slots=True)
class ObjectField:
    name: str
    value: str


@dataclass(frozen=True, slots=True)
class ObjectNode:
    key: str
    name: str
    type_name: str
    fields: tuple[ObjectField, ...] = ()


@dataclass(frozen=True, slots=True)
class ObjectReference:
    source: str
    target: str
    label: str


@dataclass(frozen=True, slots=True)
class ObjectDiagram:
    name: str
    nodes: tuple[ObjectNode, ...]
    references: tuple[ObjectReference, ...]


@dataclass(frozen=True, slots=True)
class ObjectDiagramBundle:
    diagrams: tuple[ObjectDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]
    placements: tuple[OutputPlacement, ...] = ()
