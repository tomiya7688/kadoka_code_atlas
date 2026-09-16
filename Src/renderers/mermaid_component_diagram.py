"""Mermaid renderer for logical component diagrams."""

from __future__ import annotations

import re

from Src.generators.component_diagram import ComponentDiagram


def _node_id(name: str) -> str:
    return "component_" + re.sub(r"[^A-Za-z0-9_]", "_", name)


def _label(name: str) -> str:
    return name.removeprefix("external:")


def render_component_diagram(diagram: ComponentDiagram) -> str:
    """Render internal components and external dependencies distinctly."""

    lines = ["flowchart LR"]
    for node in diagram.nodes:
        node_id = _node_id(node.name)
        label = _label(node.name)
        if node.external:
            lines.append(f'    {node_id}(["{label}"])')
        else:
            lines.append(f'    {node_id}["{label}"]')
    for edge in diagram.edges:
        lines.append(f"    {_node_id(edge.source)} --> {_node_id(edge.target)}")
    if diagram.cycle_nodes:
        lines.append("    classDef cycle stroke-width:3px")
        ids = ",".join(_node_id(node) for node in diagram.cycle_nodes)
        lines.append(f"    class {ids} cycle")
    return "\n".join(lines) + "\n"
