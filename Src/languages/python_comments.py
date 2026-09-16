"""Python-specific source rewriting for generated comments."""

from __future__ import annotations

from collections.abc import Sequence

from Src.models import CommentCandidate


def apply_python_comments(source: str, candidates: Sequence[CommentCandidate]) -> str:
    """Insert canonical comment candidates while preserving existing source text.

    Candidates are applied from bottom to top so original line numbers stay valid.
    A nearby standalone comment suppresses insertion to avoid obvious duplicates.
    This is a Python-specific compatibility rewriter; parsing and comment-text
    generation remain separate concerns.
    """

    lines = source.splitlines(keepends=True)
    default_newline = "\r\n" if "\r\n" in source else "\n"

    for candidate in sorted(candidates, key=lambda item: item.line, reverse=True):
        index = max(0, candidate.line - 1)
        previous = lines[index - 1].strip() if index > 0 else ""
        if previous.startswith("#"):
            continue

        newline = default_newline
        if index < len(lines) and lines[index].endswith("\r\n"):
            newline = "\r\n"
        text = candidate.text
        if not text.lstrip().startswith("#"):
            text = f"# {text}"
        lines.insert(index, f"{candidate.indent}{text}{newline}")

    return "".join(lines)
