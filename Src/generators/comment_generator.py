"""Generate source comments from language-adapter results."""

from __future__ import annotations

from collections.abc import Mapping

from Src.languages import CSharpAdapter, CppAdapter, GDScriptAdapter, JavaAdapter, LanguageAdapter
from Src.languages.python_comments_adapter import PythonAdapter
from Src.models import CommentCandidate


class UnsupportedLanguageError(ValueError):
    """Raised when no deterministic adapter is registered for a language."""


class CommentGenerator:
    """Insert deterministic comment candidates while preserving source statements."""

    def __init__(self, adapters: Mapping[str, LanguageAdapter] | None = None) -> None:
        self._adapters = dict(adapters or {
            "python": PythonAdapter(), "py": PythonAdapter(),
            "csharp": CSharpAdapter(), "cs": CSharpAdapter(),
            "gdscript": GDScriptAdapter(), "gd": GDScriptAdapter(),
            "java": JavaAdapter(),
            "cpp": CppAdapter(), "cxx": CppAdapter(),
        })

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
            lines.insert(candidate.line - 1, f"{candidate.indent}{candidate.text}{newline}")
        return "".join(lines)

    def _adapter(self, language: str) -> LanguageAdapter:
        try:
            return self._adapters[language.lower().lstrip(".")]
        except KeyError as error:
            supported = ", ".join(sorted(set(self._adapters)))
            raise UnsupportedLanguageError(f"No comment adapter for '{language}'. Supported languages: {supported}.") from error
