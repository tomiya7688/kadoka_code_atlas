"""Mermaid classDiagram renderer."""

from __future__ import annotations

from hashlib import sha1

from Src.models.class_diagram import ClassDiagram

_VISIBILITY_PREFIX = {
    "public": "+",
    "protected": "#",
    "internal": "~",
    "private": "-",
    "unspecified": "~",
}


def render_class_diagram(diagram: ClassDiagram) -> str:
    lines = ["classDiagram", "direction LR"]
    ids = {node.name: _node_id(node.name) for node in diagram.nodes}

    for node in diagram.nodes:
        node_id = ids[node.name]
        label = _escape(node.name)
        if not node.members:
            lines.append(f'    class {node_id}["{label}"]')
            continue
        lines.append(f'    class {node_id}["{label}"] {{')
        for member in node.members:
            prefix = _VISIBILITY_PREFIX.get(member.visibility, "~")
            parameters = ", ".join(member.parameters)
            lines.append(f"        {prefix}{member.name}({parameters})")
        lines.append("    }")

    for relation in diagram.relations:
        source = ids.get(relation.source, _node_id(relation.source))
        target = ids.get(relation.target, _node_id(relation.target))
        if relation.kind == "inheritance":
            lines.append(f"    {target} <|-- {source}")
        else:
            lines.append(f"    {source} --> {target} : uses")

    return "\n".join(lines) + "\n"


def _node_id(name: str) -> str:
    return f"c_{sha1(name.encode('utf-8')).hexdigest()[:10]}"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
