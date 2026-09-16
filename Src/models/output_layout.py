"""Passive output placement metadata for partitioned generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OutputPlacement:
    """Describe where one logical output belongs beneath its generator folder."""

    output_name: str
    relative_dir: tuple[str, ...] = ()
    series_root: str | None = None
    parent_series_root: str | None = None
    depth: int = 0
    shared: bool = False
