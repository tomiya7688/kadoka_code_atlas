"""Process-level contracts for boundary-specific orchestration."""

from __future__ import annotations

from typing import Protocol

from Src.models.comments import ParsedSource


class CommentAdapter(Protocol):
    """Convert source text into comment-generation candidates only."""

    language: str

    def parse(self, source: str) -> ParsedSource:
        """Return comment candidates without exposing parser-specific types."""
