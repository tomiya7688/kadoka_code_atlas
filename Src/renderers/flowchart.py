"""Renderer entry point for logical flowcharts."""

from __future__ import annotations

from Src.models.activity import ActivityFlow
from Src.renderers.mermaid_activity import render_activity_flow


def render_flowchart(flow: ActivityFlow, direction: str = "TD") -> str:
    """Render a logical flowchart using the initial Mermaid backend."""
    return render_activity_flow(flow, direction=direction)
