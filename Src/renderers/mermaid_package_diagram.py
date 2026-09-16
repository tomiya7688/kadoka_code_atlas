"""Mermaid renderer for package/module dependency diagrams."""

from __future__ import annotations

import re

from Src.generators.package_diagram import PackageDiagram


def _node_id(name: str) -> str:
    return "pkg_" + re.sub(r"[^A-Za-z0-9_]", "_", name)


def render_package_diagram(diagram: PackageDiagram) -> str:
    """Render package/module dependencies without source-language knowledge."""

    lines = ["flowchart LR"]
    for node in diagram.nodes:
        lines.append(f'    {_node_id(node)}["{node}"]')
    for edge in diagram.edges:
        lines.append(f"    {_node_id(edge.source)} --> {_node_id(edge.target)}")

    if diagram.cycle_nodes:
        lines.append("    classDef cycle stroke-width:3px")
        ids = ",".join(_node_id(node) for node in diagram.cycle_nodes)
        lines.append(f"    class {ids} cycle")
    if diagram.isolated_nodes:
        lines.append("    classDef isolated stroke-dasharray: 5 5")
        ids = ",".join(_node_id(node) for node in diagram.isolated_nodes)
        lines.append(f"    class {ids} isolated")
    return "\n".join(lines) + "\n"
