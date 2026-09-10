"""Compatibility Python adapter for the line-oriented comment generator."""

from __future__ import annotations

import ast
import re

from Src.models import CommentCandidate, CommentTarget, ParsedSource

_WORDS = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|_+")


def _words(name: str) -> str:
    return " ".join(part.lower() for part in _WORDS.split(name) if part).strip()


def _has_leading_comment(lines: list[str], line: int) -> bool:
    index = line - 2
    while index >= 0 and not lines[index].strip():
        index -= 1
    return index >= 0 and lines[index].lstrip().startswith("#")


def _has_body_comment(lines: list[str], node: ast.AST) -> bool:
    index = node.lineno
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index < len(lines) and lines[index].lstrip().startswith("#")


class PythonAdapter:
    """Extract conservative comment candidates without replacing the common IR adapter."""

    language = "python-comments"

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
                    candidates.append(CommentCandidate(CommentTarget.CLASS, node.name, node.lineno, " " * node.col_offset, f"# Groups behavior related to {_words(node.name)}."))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) or _has_leading_comment(lines, node.lineno) or _has_body_comment(lines, node):
                        continue
                    name = node.name
                    if name.startswith("__") and name.endswith("__"):
                        continue
                    words = _words(name)
                    if name.startswith(("is_", "has_", "can_", "should_")):
                        text = f"# Checks whether {words.split(' ', 1)[-1]}."
                    elif name.startswith(("get_", "find_", "load_", "read_")):
                        text = f"# Retrieves {words.split(' ', 1)[-1]}."
                    else:
                        text = f"# Performs the {words} operation."
                    candidates.append(CommentCandidate(CommentTarget.METHOD if parent_is_class else CommentTarget.FUNCTION, name, node.lineno, " " * node.col_offset, text))
        return ParsedSource(self.language, tuple(sorted(candidates, key=lambda item: item.line)))
