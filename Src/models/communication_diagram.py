"""Renderer-neutral communication diagram models."""

from __future__ import annotations

from dataclasses import dataclass

from Src.models.output_layout import OutputPlacement


@dataclass(frozen=True, slots=True)
class CommunicationMessage:
    source: str
    target: str
    order: str
    label: str


@dataclass(frozen=True, slots=True)
class CommunicationDiagram:
    name: str
    participants: tuple[str, ...]
    messages: tuple[CommunicationMessage, ...]


@dataclass(frozen=True, slots=True)
class CommunicationDiagramBundle:
    diagrams: tuple[CommunicationDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]
    placements: tuple[OutputPlacement, ...] = ()
