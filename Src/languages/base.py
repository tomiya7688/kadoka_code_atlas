"""Contracts implemented by language-specific source adapters."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar


Parsed = TypeVar("Parsed")


class LanguageAdapter(Protocol, Generic[Parsed]):
    """Convert source text into a language-neutral or boundary-specific result."""

    language: str

    def parse(self, source: str) -> Parsed:
        """Return parsed data without changing *source*."""
