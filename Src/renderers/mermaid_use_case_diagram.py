"""Mermaid renderer for user-facing use case diagrams."""

from __future__ import annotations

from Src.generators.use_case_diagram import UseCaseDiagram


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "\\\"").replace("\n", " ")


def render_use_case_diagram(diagram: UseCaseDiagram) -> str:
    """Render use cases using portable Mermaid flowchart syntax."""

    actors = sorted({item.actor for item in diagram.use_cases})
    actor_ids = {actor: f"actor{index}" for index, actor in enumerate(actors, start=1)}
    lines = ["flowchart LR"]
    for actor in actors:
        lines.append(f'    {actor_ids[actor]}["{_escape(actor)}"]')

    for index, use_case in enumerate(diagram.use_cases, start=1):
        ident = f"uc{index}"
        lines.append(f'    {ident}(["{_escape(use_case.name)}"])')
        relation = _escape(f"{use_case.component} / {use_case.event}")
        lines.append(f'    {actor_ids[use_case.actor]} -->|"{relation}"| {ident}')
        chain = " -> ".join((use_case.handler, *use_case.call_chain))
        lines.append(f"    %% handler-chain: {_escape(chain)}")

    return "\n".join(lines) + "\n"
