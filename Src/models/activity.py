"""Logical activity-flow model independent of source and output formats."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ActivityNode:
    id: str
    label: str
    kind: str = "activity"


@dataclass(frozen=True, slots=True)
class ActivityEdge:
    source: str
    target: str
    label: str | None = None


@dataclass(frozen=True, slots=True)
class ActivityFlow:
    entry: str
    nodes: tuple[ActivityNode, ...] = field(default_factory=tuple)
    edges: tuple[ActivityEdge, ...] = field(default_factory=tuple)
