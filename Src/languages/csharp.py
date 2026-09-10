"""Conservative C# adapter for Unity and .NET comment suggestions."""

from __future__ import annotations

import re

from Src.models import CommentCandidate, CommentTarget, ParsedSource


_TYPE = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|abstract|sealed|partial|"
    r"readonly|unsafe|new)\s+)*(?:class|struct|interface|record(?:\s+(?:class|struct))?)\s+"
    r"(?P<name>@?[A-Za-z_]\w*)"
)
_METHOD = re.compile(
    r"^\s*(?!(?:return|throw|new|await)\b)(?:(?:public|private|protected|internal|static|async|virtual|override|abstract|"
    r"sealed|extern|unsafe|new|partial)\s+)*(?:[A-Za-z_][\w<>,?.\[\]]*\s+)+"
    r"(?P<name>@?[A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:=>|\{|;|where\b|$)"
)
_PROPERTY = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|virtual|override|abstract|sealed|"
    r"required|new)\s+)*(?:[A-Za-z_][\w<>,?.\[\]]*\s+)+(?P<name>@?[A-Za-z_]\w*)\s*"
    r"\{[^}]*\b(?:get|set|init)\b"
)
_FIELD = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|readonly|const|new)\s+)+"
    r"(?:[A-Za-z_][\w<>,?.\[\]]*\s+)+(?P<name>@?[A-Za-z_]\w*)\s*(?:=|;)"
)
_UNITY_BASE = re.compile(r":\s*(?:MonoBehaviour|ScriptableObject)\b")
_CONTROL_NAMES = {"if", "for", "foreach", "while", "switch", "catch", "using", "lock"}
_WORDS = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|_+")
_UNITY_LIFECYCLE = {
    "Awake": "// Initializes Unity component state.",
    "OnEnable": "// Prepares the component when Unity enables it.",
    "Start": "// Performs startup work after Unity initializes the component.",
    "Update": "// Updates component behavior once per rendered frame.",
    "FixedUpdate": "// Updates physics-related behavior on Unity's fixed timestep.",
    "OnDisable": "// Releases state when Unity disables the component.",
    "OnDestroy": "// Releases resources before Unity destroys the component.",
}


def _words(name: str) -> str:
    return " ".join(part.lower() for part in _WORDS.split(name.lstrip("@")) if part)


def _has_leading_comment(lines: list[str], line: int) -> bool:
    index = line - 2
    while index >= 0 and not lines[index].strip():
        index -= 1
    return index >= 0 and lines[index].lstrip().startswith("//")


def _is_serialized_field(lines: list[str], line: int) -> bool:
    index = line - 2
    while index >= 0 and not lines[index].strip():
        index -= 1
    return index >= 0 and lines[index].strip().startswith("[SerializeField")


def _comment_for_method(name: str) -> str:
    if name in _UNITY_LIFECYCLE:
        return _UNITY_LIFECYCLE[name]
    words = _words(name)
    if name.lstrip("@").startswith(("Is", "Has", "Can", "Should")):
        return f"// Checks whether {words.split(' ', 1)[-1]}."
    if name.lstrip("@").startswith(("Get", "Find", "Load", "Read")):
        return f"// Retrieves {words.split(' ', 1)[-1]}."
    return f"// Performs the {words} operation."


class CSharpAdapter:
    """Extract safe C# candidates for Unity scripts and .NET source files."""

    language = "csharp"

    def parse(self, source: str) -> ParsedSource:
        lines = source.splitlines()
        candidates: list[CommentCandidate] = []
        for line_number, line in enumerate(lines, start=1):
            if _has_leading_comment(lines, line_number):
                continue
            indent = line[: len(line) - len(line.lstrip())]
            if match := _TYPE.match(line):
                name = match.group("name")
                text = f"// Groups behavior related to {_words(name)}."
                if _UNITY_BASE.search(line):
                    text = f"// Coordinates this Unity {_words(name)} component."
                candidates.append(CommentCandidate(CommentTarget.CLASS, name, line_number, indent, text))
            elif match := _PROPERTY.match(line):
                name = match.group("name")
                candidates.append(CommentCandidate(
                    CommentTarget.PROPERTY, name, line_number, indent,
                    f"// Provides access to {_words(name)}.",
                ))
            elif match := _FIELD.match(line):
                name = match.group("name")
                if _is_serialized_field(lines, line_number):
                    candidates.append(CommentCandidate(
                        CommentTarget.FIELD, name, line_number, indent,
                        f"// Stores the serialized {_words(name)} setting.",
                    ))
            elif match := _METHOD.match(line):
                name = match.group("name")
                if name.lstrip("@") not in _CONTROL_NAMES:
                    candidates.append(CommentCandidate(
                        CommentTarget.METHOD, name, line_number, indent,
                        _comment_for_method(name),
                    ))
        return ParsedSource(self.language, tuple(candidates))
