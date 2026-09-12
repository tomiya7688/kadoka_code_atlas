"""Mermaid renderer for logical activity flows."""

from __future__ import annotations

import re

from Src.models.activity import ActivityFlow


def _id(value: str) -> str:
    return "act_" + re.sub(r"[^0-9A-Za-z_]", "_", value)


def render_activity_flow(flow: ActivityFlow, direction: str = "TD") -> str:
    lines = [f"flowchart {direction}"]
    for node in flow.nodes:
        bracket = "{" + node.label + "}" if node.kind == "decision" else "[" + node.label + "]"
        lines.append(f'    {_id(node.id)}{bracket}')
    for edge in flow.edges:
        suffix = f"|{edge.label}|" if edge.label else ""
        lines.append(f"    {_id(edge.source)} -->{suffix} {_id(edge.target)}")
    return "\n".join(lines) + "\n"
