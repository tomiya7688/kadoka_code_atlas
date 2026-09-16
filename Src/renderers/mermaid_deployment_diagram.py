"""Mermaid renderer for deployment diagrams."""

from __future__ import annotations

from Src.generators.deployment_diagram import DeploymentDiagram


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "\\\"").replace("\n", " ")


def _node_line(node_id: str, label: str, kind: str) -> str:
    text = _escape(label)
    if kind == "database":
        return f'    {node_id}[("{text}")]'
    if kind in {"external-dependency", "external-image"}:
        return f'    {node_id}{{{{"{text}"}}}}'
    if kind == "ingress":
        return f'    {node_id}(["{text}"])'
    if kind in {"workload", "container-image"}:
        return f'    {node_id}[["{text}"]]'
    return f'    {node_id}["{text}"]'


def render_deployment_diagram(diagram: DeploymentDiagram) -> str:
    """Render one deployment diagram with confidence encoded as line style/class."""

    ordered = sorted(diagram.nodes, key=lambda item: item.id)
    ids = {node.id: f"n{index}" for index, node in enumerate(ordered)}
    lines = ["flowchart LR"]
    for node in ordered:
        label = node.label
        if node.environment:
            label = f"{label}\\n[{node.environment}]"
        lines.append(_node_line(ids[node.id], label, node.kind))

    for connection in diagram.connections:
        if connection.source not in ids or connection.target not in ids:
            continue
        relation = _escape(f"{connection.relation} [{connection.confidence}]")
        arrow = "-.->" if connection.confidence == "inferred" else "-->"
        lines.append(
            f'    {ids[connection.source]} {arrow}|"{relation}"| {ids[connection.target]}'
        )

    lines.extend(
        [
            "    classDef confirmed stroke-width:2px;",
            "    classDef inferred stroke-dasharray:5 5;",
            "    classDef unknown stroke-dasharray:2 4;",
        ]
    )
    for node in ordered:
        confidence = node.confidence if node.confidence in {"confirmed", "inferred", "unknown"} else "unknown"
        lines.append(f"    class {ids[node.id]} {confidence};")
    return "\n".join(lines) + "\n"
