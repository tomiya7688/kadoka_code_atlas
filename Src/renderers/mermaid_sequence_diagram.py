"""Mermaid renderer for logical sequence diagrams."""

from __future__ import annotations

from Src.models.sequence_diagram import SequenceDiagram


def render_sequence_diagram(diagram: SequenceDiagram) -> str:
    lines = ["sequenceDiagram"]
    ids = {name: f"p{index}" for index, name in enumerate(diagram.participants)}
    for name in diagram.participants:
        lines.append(f"    participant {ids[name]} as {_label(name)}")
    for message in diagram.messages:
        caller = ids[message.caller]
        callee = ids[message.callee]
        arrow = "-->>" if message.kind == "return" else "->>"
        lines.append(f"    {caller}{arrow}{callee}: {_label(message.label)}")
    return "\n".join(lines) + "\n"


def _label(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ").replace(":", "-")
