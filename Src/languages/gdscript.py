"""Godot GDScript adapter for deterministic comment suggestions."""

from __future__ import annotations

import re

from Src.models import CommentCandidate, CommentTarget, ParsedSource

_EXTENDS = re.compile(r"^\s*extends\s+(?P<name>[A-Za-z_]\w*)")
_SIGNAL = re.compile(r"^\s*signal\s+(?P<name>[A-Za-z_]\w*)")
_VARIABLE = re.compile(r"^\s*(?P<annotation>@export|@onready)\s+(?:var|const)\s+(?P<name>[A-Za-z_]\w*)")
_FUNCTION = re.compile(r"^\s*(?:static\s+)?func\s+(?P<name>[A-Za-z_]\w*)\s*\(")
_WORDS = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|_+")
_LIFECYCLE = {
    "_ready": "# Initializes node state after it enters the scene tree.",
    "_process": "# Updates node behavior once per rendered frame.",
    "_physics_process": "# Updates physics-related behavior on Godot's fixed timestep.",
    "_input": "# Handles input events before GUI nodes consume them.",
    "_unhandled_input": "# Handles input events that GUI nodes did not consume.",
    "_exit_tree": "# Releases node state before it leaves the scene tree.",
}


def _words(name: str) -> str:
    return " ".join(part.lower() for part in _WORDS.split(name) if part)


def _has_leading_comment(lines: list[str], line: int) -> bool:
    index = line - 2
    while index >= 0 and not lines[index].strip():
        index -= 1
    return index >= 0 and lines[index].lstrip().startswith("#")


def _function_comment(name: str) -> str:
    if name in _LIFECYCLE:
        return _LIFECYCLE[name]
    words = _words(name)
    if name.startswith(("is_", "has_", "can_", "should_")):
        return f"# Checks whether {words.split(' ', 1)[-1]}."
    if name.startswith(("get_", "find_", "load_", "read_")):
        return f"# Retrieves {words.split(' ', 1)[-1]}."
    return f"# Performs the {words} operation."


class GDScriptAdapter:
    """Extract Godot-specific structural candidates without changing source code."""

    language = "gdscript"

    def parse(self, source: str) -> ParsedSource:
        lines = source.splitlines()
        candidates: list[CommentCandidate] = []
        for line_number, line in enumerate(lines, start=1):
            if _has_leading_comment(lines, line_number):
                continue
            indent = line[: len(line) - len(line.lstrip())]
            if match := _EXTENDS.match(line):
                name = match.group("name")
                candidates.append(CommentCandidate(CommentTarget.MODULE, name, line_number, indent, f"# Defines behavior for a {name} node."))
            elif match := _SIGNAL.match(line):
                name = match.group("name")
                candidates.append(CommentCandidate(CommentTarget.SIGNAL, name, line_number, indent, f"# Declares the {_words(name)} signal."))
            elif match := _VARIABLE.match(line):
                name = match.group("name")
                text = f"# Configures the exported {_words(name)} value." if match.group("annotation") == "@export" else f"# Caches the ready {_words(name)} node reference."
                candidates.append(CommentCandidate(CommentTarget.FIELD, name, line_number, indent, text))
            elif match := _FUNCTION.match(line):
                name = match.group("name")
                candidates.append(CommentCandidate(CommentTarget.FUNCTION, name, line_number, indent, _function_comment(name)))
        return ParsedSource(self.language, tuple(candidates))
