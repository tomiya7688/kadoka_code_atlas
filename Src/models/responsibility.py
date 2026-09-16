"""Renderer-neutral class responsibility table models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResponsibilityRow:
    class_name: str
    responsibility: str


@dataclass(frozen=True, slots=True)
class ResponsibilityTable:
    name: str
    rows: tuple[ResponsibilityRow, ...]
