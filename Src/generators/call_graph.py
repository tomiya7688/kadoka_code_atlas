"""High-level call graph generation helpers."""

from __future__ import annotations

from Src.analyzers.call_graph import CallGraph
from Src.analyzers.ir import ModuleIR
from Src.renderers.mermaid_call_graph import render_call_graph


def generate_call_graph_mermaid(
    module: ModuleIR,
    *,
    root: str | None = None,
    max_depth: int | None = None,
    direction: str = "LR",
) -> str:
    """Build a call graph from IR and render it as Mermaid."""
    graph = CallGraph.from_module(module)
    if root is not None:
        graph = graph.reachable_from(root, max_depth=max_depth)
    return render_call_graph(graph, direction=direction)
