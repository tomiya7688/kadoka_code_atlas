"""Mermaid renderer for logical object diagrams."""

from __future__ import annotations

from Src.models.object_diagram import ObjectDiagram


def render_object_diagram(diagram: ObjectDiagram) -> str:
    lines = ["flowchart LR"]
    ids = {node.key: f"o{index}" for index, node in enumerate(diagram.nodes)}
    for node in diagram.nodes:
        parts = [f"{node.name} : {node.type_name}"]
        parts.extend(f"{field.name} = {field.value}" for field in node.fields)
        label = "<br/>".join(_label(part) for part in parts)
        lines.append(f'    {ids[node.key]}["{label}"]')
    for reference in diagram.references:
        if reference.source not in ids or reference.target not in ids:
            continue
        lines.append(
            f"    {ids[reference.source]} -->|{_edge_label(reference.label)}| {ids[reference.target]}"
        )
    return "\n".join(lines) + "\n"


def _label(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ").replace('"', "'")


def _edge_label(value: str) -> str:
    return _label(value).replace("|", "/")
