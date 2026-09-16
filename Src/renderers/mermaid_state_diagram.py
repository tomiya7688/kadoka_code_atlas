"""Mermaid renderer for logical state diagrams."""

from __future__ import annotations

from Src.generators.state_diagram import StateDiagram


def _label(event: str | None, condition: str | None) -> str:
    pieces: list[str] = []
    if event:
        pieces.append(event)
    if condition:
        pieces.append(f"[{condition}]")
    return " ".join(pieces)


def render_state_diagram(diagram: StateDiagram) -> str:
    """Render a state diagram without inspecting source-language syntax."""

    lines = [
        "stateDiagram-v2",
        f"    %% {diagram.owner}.{diagram.state_variable} : {diagram.state_type}",
    ]
    if diagram.initial_state:
        lines.append(f"    [*] --> {diagram.initial_state}")

    has_any = any(item.source == "*" for item in diagram.transitions)
    if has_any:
        lines.append('    state "Any current state" as __any')

    for transition in diagram.transitions:
        source = "__any" if transition.source == "*" else transition.source
        suffix = _label(transition.event, transition.condition)
        rendered = f"    {source} --> {transition.target}"
        if suffix:
            rendered += f": {suffix}"
        lines.append(rendered)

    for terminal in diagram.terminal_states:
        lines.append(f"    {terminal} --> [*]")
    return "\n".join(lines) + "\n"
