"""PlantUML renderer for class diagrams."""

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


def _alias(name: str) -> str:
    return f"c_{sha1(name.encode('utf-8')).hexdigest()[:10]}"


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_plantuml_class_diagram(diagram: ClassDiagram) -> str:
    """Render a renderer-neutral class diagram as PlantUML."""

    aliases = {node.name: _alias(node.name) for node in diagram.nodes}
    lines = ["@startuml", "left to right direction"]

    for node in diagram.nodes:
        alias = aliases[node.name]
        label = _quote(node.name)
        if node.external:
            lines.append(f'class "{label}" as {alias} <<external>>')
            continue
        lines.append(f'class "{label}" as {alias} {{')
        for member in node.members:
            prefix = _VISIBILITY_PREFIX.get(member.visibility, "~")
            parameters = ", ".join(member.parameters)
            lines.append(f"  {prefix}{member.name}({parameters})")
        lines.append("}")

    for relation in diagram.relations:
        source = aliases.get(relation.source, _alias(relation.source))
        target = aliases.get(relation.target, _alias(relation.target))
        if relation.kind == "inheritance":
            lines.append(f"{target} <|-- {source}")
        else:
            lines.append(f"{source} --> {target} : uses")

    lines.append("@enduml")
    return "\n".join(lines) + "\n"
