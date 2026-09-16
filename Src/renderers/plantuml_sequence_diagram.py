"""PlantUML renderer for sequence diagrams."""

from __future__ import annotations

from hashlib import sha1

from Src.models.sequence_diagram import SequenceDiagram


def _alias(name: str) -> str:
    return f"p_{sha1(name.encode('utf-8')).hexdigest()[:10]}"


def _quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def render_plantuml_sequence_diagram(diagram: SequenceDiagram) -> str:
    """Render a renderer-neutral sequence diagram as PlantUML."""

    aliases = {name: _alias(name) for name in diagram.participants}
    lines = ["@startuml"]
    for participant in diagram.participants:
        lines.append(f'participant "{_quote(participant)}" as {aliases[participant]}')

    for message in diagram.messages:
        caller = aliases.setdefault(message.caller, _alias(message.caller))
        callee = aliases.setdefault(message.callee, _alias(message.callee))
        label = _quote(message.label)
        arrow = "-->" if message.kind == "return" else "->"
        lines.append(f"{caller} {arrow} {callee} : {label}")

    lines.append("@enduml")
    return "\n".join(lines) + "\n"
