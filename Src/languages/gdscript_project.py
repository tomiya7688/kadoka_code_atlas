"""Godot project semantic-resolution boundary for GDScript adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class GDScriptProjectResolver(Protocol):
    """Resolve Godot project references without exposing parser-specific types."""

    def resolve_resource(
        self,
        reference: str,
        source_path: Path | None = None,
    ) -> Path | None:
        ...

    def resolve_class_name(self, name: str) -> Path | None:
        ...


@dataclass(slots=True)
class FilesystemGDScriptProjectResolver:
    """Minimal res:// and class_name resolver rooted at one Godot project."""

    root: Path
    class_names: dict[str, Path] = field(default_factory=dict)

    def resolve_resource(
        self,
        reference: str,
        source_path: Path | None = None,
    ) -> Path | None:
        if reference.startswith("res://"):
            candidate = (self.root / reference[len("res://"):]).resolve()
            root = self.root.resolve()
            if candidate != root and root not in candidate.parents:
                return None
            return candidate if candidate.exists() else None
        if source_path is not None:
            candidate = (source_path.parent / reference).resolve()
            return candidate if candidate.exists() else None
        return None

    def resolve_class_name(self, name: str) -> Path | None:
        return self.class_names.get(name)

    def register_class_name(self, name: str, path: Path) -> None:
        self.class_names[name] = path.resolve()
