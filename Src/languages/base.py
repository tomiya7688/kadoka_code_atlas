"""Contracts implemented by language-specific Common IR adapters."""

from __future__ import annotations

from typing import Protocol

from Src.analyzers.ir import ModuleIR


class LanguageAdapter(Protocol):
    """Convert source text into the language-neutral Common IR."""

    language: str

    def parse(self, source: str) -> ModuleIR:
        """Return passive Common IR facts without changing *source*."""
