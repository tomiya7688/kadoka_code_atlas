"""Contracts implemented by language-specific source adapters."""

from __future__ import annotations

from typing import Protocol

from Src.models import ParsedSource


class LanguageAdapter(Protocol):
    """Extract deterministic comment candidates from one source language."""

    language: str

    def parse(self, source: str) -> ParsedSource:
        """Return comment candidates without changing *source*."""
