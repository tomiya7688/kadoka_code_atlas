"""Flowchart generation entry points."""

from __future__ import annotations

from Src.models.activity import ActivityFlow


def generate_flowchart(flow: ActivityFlow) -> ActivityFlow:
    """Return the logical flowchart model for renderer selection.

    Language adapters construct the passive model; this layer intentionally
    contains no AST or parser dependency.
    """
    return flow
