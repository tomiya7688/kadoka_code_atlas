"""Generate source comments from language-adapter results."""

from __future__ import annotations

from collections.abc import Mapping

from Src.generators.comment_backend import CommentTextBackend, RuleBasedCommentBackend
from Src.process.contracts import CommentAdapter
from Src.process.comment_registry import default_comment_adapters
from Src.models import CommentCandidate


class UnsupportedLanguageError(ValueError):
    """Raised when no deterministic adapter is registered for a language."""


class CommentGenerator:
    """Insert deterministic comment candidates while preserving source statements."""

    def __init__(self, adapters: Mapping[str, CommentAdapter] | None = None, backend: CommentTextBackend | None = None) -> None:
        self._backend = backend or RuleBasedCommentBackend()
        self._adapters = dict(adapters or default_comment_adapters())

    def supported_languages(self) -> tuple[str, ...]:
        """Return registered comment adapter names in deterministic order."""
        return tuple(sorted(self._adapters))

    def candidates(self, source: str, language: str) -> tuple[CommentCandidate, ...]:
        """Return suggestions only; this method never mutates source text."""
        return self._adapter(language).parse(source).candidates

    def generate(self, source: str, language: str) -> str:
        """Return *source* with comments inserted immediately above selected nodes."""
        candidates = self.candidates(source, language)
        if not candidates:
            return source
        lines = source.splitlines(keepends=True)
        newline = "\r\n" if "\r\n" in source else "\n"
        for candidate in reversed(candidates):
            text = self._backend.generate(candidate)
            lines.insert(candidate.line - 1, f"{candidate.indent}{text}{newline}")
        return "".join(lines)

    def _adapter(self, language: str) -> CommentAdapter:
        try:
            return self._adapters[language.lower().lstrip(".")]
        except KeyError as error:
            supported = ", ".join(sorted(set(self._adapters)))
            raise UnsupportedLanguageError(f"No comment adapter for '{language}'. Supported languages: {supported}.") from error
