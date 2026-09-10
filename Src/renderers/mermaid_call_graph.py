"""Mermaid renderer for call graphs."""

from __future__ import annotations

import re

from Src.analyzers.call_graph import CallGraph


def _node_id(name: str) -> str:
    return "n_" + re.sub(r"[^0-9A-Za-z_]", "_", name)


def render_call_graph(graph: CallGraph, direction: str = "LR") -> str:
    lines = [f"flowchart {direction}"]
    for node in sorted(graph.nodes):
        lines.append(f'    {_node_id(node)}["{node}"]')
    for edge in graph.edges:
        lines.append(f"    {_node_id(edge.caller)} --> {_node_id(edge.callee)}")
    return "\n".join(lines) + "\n"
