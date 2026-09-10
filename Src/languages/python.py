"""Python AST adapter for deterministic, conservative comment suggestions."""

from __future__ import annotations

import ast
import re

from Src.models import CommentCandidate, CommentTarget, ParsedSource


_WORDS = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|_+")


def _words(name: str) -> str:
    return " ".join(part.lower() for part in _WORDS.split(name) if part).strip()


def _has_leading_comment(lines: list[str], line: int) -> bool:
    """Return whether a contiguous comment directly precedes a definition."""
    index = line - 2
    while index >= 0 and not lines[index].strip():
        index -= 1
    return index >= 0 and lines[index].lstrip().startswith("#")


def _has_body_comment(lines: list[str], node: ast.AST) -> bool:
    """Return whether the first meaningful line in a callable body is a comment."""
    index = node.lineno
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index < len(lines) and lines[index].lstrip().startswith("#")


def _function_comment(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    if node.name.startswith("__") and node.name.endswith("__"):
        return None
    action = _words(node.name)
    if not action:
        return None
    if node.name.startswith(("is_", "has_", "can_", "should_")):
        return f"# Checks whether {action.split(' ', 1)[-1]}."
    if node.name.startswith(("get_", "find_", "load_", "read_")):
        return f"# Retrieves {action.split(' ', 1)[-1]}."
    return f"# Performs the {action} operation."


class PythonAdapter:
    """Extract safe class and callable comment candidates from Python source."""

    language = "python"

    def parse(self, source: str) -> ParsedSource:
        tree = ast.parse(source)
        lines = source.splitlines()
        candidates: list[CommentCandidate] = []

        for parent in ast.walk(tree):
            parent_is_class = isinstance(parent, ast.ClassDef)
            for node in ast.iter_child_nodes(parent):
                if isinstance(node, ast.ClassDef):
                    if ast.get_docstring(node) or _has_leading_comment(lines, node.lineno) or _has_body_comment(lines, node):
                        continue
                    candidates.append(CommentCandidate(
                        CommentTarget.CLASS, node.name, node.lineno,
                        " " * node.col_offset,
                        f"# Groups behavior related to {_words(node.name)}.",
                    ))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) or _has_leading_comment(lines, node.lineno) or _has_body_comment(lines, node):
                        continue
                    text = _function_comment(node)
                    if text:
                        candidates.append(CommentCandidate(
                            CommentTarget.METHOD if parent_is_class else CommentTarget.FUNCTION,
                            node.name, node.lineno, " " * node.col_offset, text,
                        ))

        return ParsedSource(self.language, tuple(sorted(candidates, key=lambda item: item.line)))
