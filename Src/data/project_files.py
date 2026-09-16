"""Filesystem discovery helpers for project source selection."""

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


def _is_ignored(root: Path, path: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts[:-1]
    except ValueError:
        relative_parts = ()
    return any(part in _IGNORED_DIRECTORIES for part in relative_parts)


def discover_supported_files(root: Path) -> list[Path]:
    """Return supported files below *root* without generated/tooling trees."""
    if root.is_file():
        return [root] if detect_language(root) != "unknown" else []

    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or _is_ignored(root, path):
            continue
        if detect_language(path) != "unknown":
            result.append(path)
    return sorted(result, key=lambda item: str(item).lower())


def discover_deployment_files(root: Path) -> list[Path]:
    """Return Docker/Compose/Kubernetes candidate files for deployment analysis."""

    if not root.is_dir():
        return []
    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or _is_ignored(root, path):
            continue
        name = path.name.lower()
        if name.startswith("dockerfile"):
            result.append(path)
            continue
        if name in {
            "compose.yml",
            "compose.yaml",
            "docker-compose.yml",
            "docker-compose.yaml",
        }:
            result.append(path)
            continue
        if path.suffix.lower() in {".yml", ".yaml"}:
            result.append(path)
    return sorted(set(result), key=lambda item: str(item).lower())
