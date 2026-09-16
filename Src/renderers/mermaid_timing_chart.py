"""Mermaid renderer for logical timing charts."""

from __future__ import annotations

from Src.generators.timing_chart import TimingChart


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "\\\"").replace("\n", " ")


def render_timing_chart(chart: TimingChart) -> str:
    """Render logical timing relations without inventing real durations."""

    targets = sorted({event.target for event in chart.events if event.target})
    participants = {chart.owner: "p0"}
    for index, target in enumerate(targets, start=1):
        participants[target] = f"p{index}"

    lines = ["sequenceDiagram", f'    participant p0 as "{_escape(chart.owner)}"']
    for target in targets:
        lines.append(f'    participant {participants[target]} as "{_escape(target)}"')

    if chart.is_async:
        lines.append("    Note over p0: async flow")

    for event in chart.events:
        target_id = participants.get(event.target or "")
        detail = _escape(event.detail or event.target or event.kind)
        if event.kind == "call" and target_id:
            lines.append(f"    p0->>{target_id}: {event.order}. call {detail}")
        elif event.kind == "await" and target_id:
            lines.append(f"    p0->>{target_id}: {event.order}. await {detail}")
            lines.append(f"    {target_id}-->>p0: resume")
        elif event.kind == "parallel_start" and target_id:
            lines.append(f"    p0-){target_id}: {event.order}. parallel start {detail}")
        elif event.kind == "parallel_join":
            lines.append(f"    Note over p0: {event.order}. join {detail}")
        elif event.kind == "wait":
            lines.append(f"    Note over p0: {event.order}. wait {detail}")
        elif event.kind == "sync_wait":
            lines.append(f"    Note over p0: {event.order}. sync wait {detail}")
        elif event.kind == "sync":
            lines.append(f"    Note over p0: {event.order}. sync {detail}")
        elif event.kind == "timer":
            if target_id:
                lines.append(f"    p0-) {target_id}: {event.order}. timer {detail}")
            else:
                lines.append(f"    Note over p0: {event.order}. timer {detail}")
        elif event.kind == "callback":
            if target_id:
                lines.append(f"    p0-) {target_id}: {event.order}. callback {detail}")
            else:
                lines.append(f"    Note over p0: {event.order}. callback {detail}")
        elif event.kind == "periodic":
            lines.append(f"    Note over p0: {event.order}. periodic {detail}")
        else:
            lines.append(f"    Note over p0: {event.order}. {event.kind} {detail}")

    return "\n".join(lines) + "\n"
