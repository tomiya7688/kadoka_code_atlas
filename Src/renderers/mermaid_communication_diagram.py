"""Mermaid renderer for logical communication diagrams."""

from __future__ import annotations

from Src.models.communication_diagram import CommunicationDiagram


def render_communication_diagram(diagram: CommunicationDiagram) -> str:
    lines = ["flowchart LR"]
    ids = {name: f"p{index}" for index, name in enumerate(diagram.participants)}
    for name in diagram.participants:
        lines.append(f'    {ids[name]}["{_label(name)}"]')
    for message in diagram.messages:
        source = ids[message.source]
        target = ids[message.target]
        text = _label(f"{message.order}: {message.label}")
        lines.append(f'    {source} -->|"{text}"| {target}')
    return "\n".join(lines) + "\n"


def _label(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', "'")
        .replace("\n", " ")
        .replace("\r", " ")
    )
