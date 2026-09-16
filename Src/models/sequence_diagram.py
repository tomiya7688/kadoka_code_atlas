"""Renderer-neutral sequence diagram models."""

from __future__ import annotations

from dataclasses import dataclass

from Src.models.output_layout import OutputPlacement


@dataclass(frozen=True, slots=True)
class SequenceMessage:
    caller: str
    callee: str
    label: str
    depth: int = 0
    kind: str = "call"


@dataclass(frozen=True, slots=True)
class SequenceDiagram:
    name: str
    participants: tuple[str, ...]
    messages: tuple[SequenceMessage, ...]


@dataclass(frozen=True, slots=True)
class SequenceDiagramBundle:
    diagrams: tuple[SequenceDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]
    placements: tuple[OutputPlacement, ...] = ()
