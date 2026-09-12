"""Contracts for format-specific renderers."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar


Input = TypeVar("Input")


class Renderer(Protocol, Generic[Input]):
    """Render a logical output value into a concrete text format."""

    def render(self, value: Input) -> str:
        """Return formatted output without modifying *value*."""
