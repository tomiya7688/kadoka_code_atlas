"""Communication diagram generation by reusing sequence analysis and partitioning."""

from __future__ import annotations

from Src.analyzers.ir import ModuleIR
from Src.generators.sequence_diagram import (
    SequenceDiagramOptions,
    build_sequence_diagram_bundle,
)
from Src.models.communication_diagram import (
    CommunicationDiagram,
    CommunicationDiagramBundle,
    CommunicationMessage,
)


def build_communication_diagram_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
    max_depth: int = 8,
    show_duplicate_calls: bool = True,
) -> CommunicationDiagramBundle:
    """Convert partitioned call sequences into numbered communication diagrams."""
    sequence_bundle = build_sequence_diagram_bundle(
        module,
        fan_in_threshold=fan_in_threshold,
        max_depth=max_depth,
        options=SequenceDiagramOptions(
            show_duplicate_calls=show_duplicate_calls,
            show_returns=False,
        ),
    )

    diagrams: list[CommunicationDiagram] = []
    for sequence in sequence_bundle.diagrams:
        calls = tuple(message for message in sequence.messages if message.kind == "call")
        orders = _message_orders(tuple(message.depth for message in calls))
        messages = tuple(
            CommunicationMessage(
                source=_participant(message.caller),
                target=_participant(message.callee),
                order=order,
                label=message.label,
            )
            for message, order in zip(calls, orders)
        )
        participants = _participants(
            tuple(_participant(name) for name in sequence.participants),
            messages,
        )
        diagrams.append(
            CommunicationDiagram(
                name=sequence.name,
                participants=participants,
                messages=messages,
            )
        )

    return CommunicationDiagramBundle(
        tuple(diagrams),
        sequence_bundle.statistics,
        sequence_bundle.placements,
    )


def _message_orders(depths: tuple[int, ...]) -> tuple[str, ...]:
    counters: list[int] = []
    result: list[str] = []
    for depth in depths:
        if depth < 0:
            raise ValueError("communication message depth must be >= 0")
        while len(counters) <= depth:
            counters.append(0)
        counters = counters[: depth + 1]
        counters[depth] += 1
        result.append(".".join(str(value) for value in counters))
    return tuple(result)


def _participant(callable_name: str) -> str:
    if "." not in callable_name:
        return callable_name
    return callable_name.rsplit(".", 1)[0]


def _participants(
    candidates: tuple[str, ...],
    messages: tuple[CommunicationMessage, ...],
) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for name in candidates:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    for message in messages:
        for name in (message.source, message.target):
            if name not in seen:
                seen.add(name)
                ordered.append(name)
    return tuple(ordered)
