"""Sequence diagram generation over ordered Common IR calls and shared partitioning."""

from __future__ import annotations

from Src.analyzers.call_sequence import (
    ResolvedCall,
    build_sequence_relation_graph,
    resolve_call_sequences,
)
from Src.analyzers.ir import ModuleIR
from Src.analyzers.partition import partition_graph
from Src.models.sequence_diagram import (
    SequenceDiagram,
    SequenceDiagramBundle,
    SequenceMessage,
)


def build_sequence_diagram_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
    max_depth: int = 8,
) -> SequenceDiagramBundle:
    """Generate entry/caller-centered sequence diagrams plus shared callee diagrams."""
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    sequences = resolve_call_sequences(module)
    graph = build_sequence_relation_graph(module, sequences)
    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    incoming: dict[str, set[str]] = {node: set() for node in graph.nodes}
    for edge in graph.edges:
        incoming.setdefault(edge.callee, set()).add(edge.caller)

    diagrams: list[SequenceDiagram] = []
    for series_index, series in enumerate(partition.series, start=1):
        selected = set(series)
        roots = [
            node
            for node in series
            if not (incoming.get(node, set()) & selected)
        ]
        if not roots and series:
            roots = [series[0]]
        for root in roots:
            messages = _expand_sequence(
                root,
                sequences,
                allowed=selected,
                max_depth=max_depth,
            )
            diagrams.append(
                SequenceDiagram(
                    name=f"series_{series_index}_{_slug(root)}",
                    participants=_participants(root, messages),
                    messages=messages,
                )
            )

    for shared in partition.shared:
        messages: list[SequenceMessage] = []
        for caller in sorted(incoming.get(shared, ())):
            label = _first_label(caller, shared, sequences)
            messages.append(SequenceMessage(caller, shared, label, 0))
        for call in sequences.get(shared, ()):
            messages.append(SequenceMessage(shared, call.target, call.raw, 1))
        frozen = tuple(messages)
        diagrams.append(
            SequenceDiagram(
                name=f"shared_{_slug(shared)}",
                participants=_participants(shared, frozen),
                messages=frozen,
            )
        )

    return SequenceDiagramBundle(tuple(diagrams), partition.statistics)


def _expand_sequence(
    root: str,
    sequences: dict[str, tuple[ResolvedCall, ...]],
    *,
    allowed: set[str],
    max_depth: int,
) -> tuple[SequenceMessage, ...]:
    messages: list[SequenceMessage] = []

    def walk(caller: str, depth: int, active: frozenset[str]) -> None:
        if depth >= max_depth:
            return
        for call in sequences.get(caller, ()):
            messages.append(SequenceMessage(caller, call.target, call.raw, depth))
            if call.target not in allowed or call.target not in sequences:
                continue
            if call.target in active:
                continue
            walk(call.target, depth + 1, active | {call.target})

    walk(root, 0, frozenset({root}))
    return tuple(messages)


def _participants(
    root: str,
    messages: tuple[SequenceMessage, ...],
) -> tuple[str, ...]:
    ordered: list[str] = [root]
    seen = {root}
    for message in messages:
        for name in (message.caller, message.callee):
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
    return tuple(ordered)


def _first_label(
    caller: str,
    callee: str,
    sequences: dict[str, tuple[ResolvedCall, ...]],
) -> str:
    for call in sequences.get(caller, ()):
        if call.target == callee:
            return call.raw
    return callee.rsplit(".", 1)[-1]


def _slug(value: str) -> str:
    result = "".join(character if character.isalnum() else "_" for character in value)
    return result.strip("_") or "sequence"
