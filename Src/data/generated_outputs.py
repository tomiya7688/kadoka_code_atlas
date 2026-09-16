"""Common filesystem contract for generated output sets."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from Src.data.files import write_text


class GeneratedOutputLike(Protocol):
    name: str
    content: str
    format: str
    relative_dir: tuple[str, ...]


_EXTENSIONS = {
    "mermaid": ".mmd",
    "plantuml": ".puml",
    "markdown": ".md",
    "csv": ".csv",
    "source": ".txt",
}


def save_generated_outputs(
    output_root: Path,
    category: str,
    outputs: Sequence[GeneratedOutputLike],
) -> tuple[Path, ...]:
    """Save outputs under one stable generator folder and optional series folders."""

    target = output_root / category
    paths: list[Path] = []
    seen: set[Path] = set()
    for output in outputs:
        extension = _EXTENSIONS.get(output.format, ".txt")
        path = target.joinpath(*output.relative_dir) / f"{output.name}{extension}"
        if path in seen:
            raise ValueError(f"Duplicate generated output path: {path}")
        seen.add(path)
        write_text(path, output.content)
        paths.append(path)
    return tuple(paths)
