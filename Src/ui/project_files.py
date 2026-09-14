"""UI-neutral file discovery helpers for desktop front ends."""

from __future__ import annotations

from pathlib import Path

_EXTENSION_LANGUAGE = {
    ".py": "python",
    ".gd": "gdscript",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".java": "java",
    ".go": "go",
    ".yml": "yaml",
    ".yaml": "yaml",
}

_IGNORED_DIRECTORIES = {
    ".git",
    ".dev",
    ".codex",
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
}


def detect_language(path: Path) -> str:
    """Return a stable language id for a selected file."""
    return _EXTENSION_LANGUAGE.get(path.suffix.lower(), "unknown")


def discover_supported_files(root: Path) -> list[Path]:
    """Return supported files below *root* without generated/tooling trees."""
    if root.is_file():
        return [root] if detect_language(root) != "unknown" else []

    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(root).parts[:-1]
        except ValueError:
            relative_parts = ()
        if any(part in _IGNORED_DIRECTORIES for part in relative_parts):
            continue
        if detect_language(path) != "unknown":
            result.append(path)
    return sorted(result, key=lambda item: str(item).lower())
