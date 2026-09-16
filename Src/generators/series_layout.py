"""Shared output placement helpers for partitioned generators."""

from __future__ import annotations

from Src.analyzers.partition import GraphPartition
from Src.generators.output_names import stable_output_name
from Src.models.output_layout import OutputPlacement


def series_directory(root: str, *, fallback: str = "series") -> str:
    """Return a stable renderer-independent directory name for one series root."""

    return stable_output_name("series", root, fallback=fallback)


def regular_placement(
    output_name: str,
    partition: GraphPartition,
    series_index: int,
) -> OutputPlacement:
    """Return placement metadata for a regular partition series."""

    root = partition.series_roots[series_index]
    depth = partition.series_depths[series_index]
    parent = partition.series_parents[series_index]
    return OutputPlacement(
        output_name=output_name,
        relative_dir=(series_directory(root),),
        series_root=root,
        parent_series_root=parent,
        depth=depth,
    )


def shared_placement(output_name: str, shared_root: str) -> OutputPlacement:
    """Return placement metadata for a high fan-in shared series."""

    return OutputPlacement(
        output_name=output_name,
        relative_dir=("shared",),
        series_root=shared_root,
        shared=True,
    )
