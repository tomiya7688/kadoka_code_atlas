"""Sequence diagram generation over ordered Common IR calls and shared partitioning."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from Src.analyzers.call_sequence import (
    ResolvedCall,
    build_sequence_relation_graph,
    resolve_call_sequences,
)
from Src.analyzers.ir import ModuleIR
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name
from Src.generators.series_layout import regular_placement, shared_placement
from Src.models.output_layout import OutputPlacement
from Src.models.sequence_diagram import (
    SequenceDiagram,
    SequenceDiagramBundle,
    SequenceMessage,
)


@dataclass(frozen=True, slots=True)
class SequenceDiagramOptions:
    """User-selectable sequence rendering semantics before renderer selection."""

    show_duplicate_calls: bool = True
    show_returns: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, object] | None) -> "SequenceDiagramOptions":
        if value is None:
            return cls()
        duplicate = value.get("show_duplicate_calls", True)
        returns = value.get("show_returns", False)
        if not isinstance(duplicate, bool):
            raise ValueError("sequence_diagram.show_duplicate_calls must be boolean")
        if not isinstance(returns, bool):
            raise ValueError("sequence_diagram.show_returns must be boolean")
        return cls(show_duplicate_calls=duplicate, show_returns=returns)


def build_sequence_diagram_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
    max_depth: int = 8,
    options: SequenceDiagramOptions | None = None,
) -> SequenceDiagramBundle:
    """Generate entry/caller-centered sequence diagrams plus shared callee diagrams."""
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    options = options or SequenceDiagramOptions()

    sequences = resolve_call_sequences(module)
    graph = build_sequence_relation_graph(module, sequences)
    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    blocked_cycle_edges = _cycle_edges(graph.cycles())
    incoming: dict[str, set[str]] = {node: set() for node in graph.nodes}
    for edge in graph.edges:
        incoming.setdefault(edge.callee, set()).add(edge.caller)

    diagrams: list[SequenceDiagram] = []
    placements: list[OutputPlacement] = []
    for series_index, series in enumerate(partition.series):
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
                options=options,
                blocked_cycle_edges=blocked_cycle_edges,
            )
            name = stable_output_name(
                f"series_{series_index + 1}",
                root,
                fallback="sequence",
            )
            diagrams.append(
                SequenceDiagram(
                    name=name,
                    participants=_participants(root, messages),
                    messages=messages,
                )
            )
            placements.append(regular_placement(name, partition, series_index))

    for shared in partition.shared:
        messages: list[SequenceMessage] = []
        emitted: set[tuple[str, str, str]] = set()
        for caller in sorted(incoming.get(shared, ())):
            if (caller, shared) in blocked_cycle_edges:
                continue
            label = _first_label(caller, shared, sequences)
            if _append_call(messages, emitted, caller, shared, label, 0, options):
                if options.show_returns:
                    messages.append(SequenceMessage(shared, caller, "return", 0, "return"))
        for call in sequences.get(shared, ()):
            if (shared, call.target) in blocked_cycle_edges:
                continue
            if _append_call(messages, emitted, shared, call.target, call.raw, 1, options):
                if options.show_returns and call.target in sequences:
                    messages.append(SequenceMessage(call.target, shared, "return", 1, "return"))
        frozen = tuple(messages)
        name = stable_output_name("shared", shared, fallback="sequence")
        diagrams.append(
            SequenceDiagram(
                name=name,
                participants=_participants(shared, frozen),
                messages=frozen,
            )
        )
        placements.append(shared_placement(name, shared))

    return SequenceDiagramBundle(
        tuple(diagrams),
        partition.statistics,
        tuple(placements),
    )


def _expand_sequence(
    root: str,
    sequences: dict[str, tuple[ResolvedCall, ...]],
    *,
    allowed: set[str],
    max_depth: int,
    options: SequenceDiagramOptions,
    blocked_cycle_edges: set[tuple[str, str]],
) -> tuple[SequenceMessage, ...]:
    messages: list[SequenceMessage] = []
    emitted: set[tuple[str, str, str]] = set()

    def walk(caller: str, depth: int, active: frozenset[str]) -> None:
        if depth >= max_depth:
            return
        for call in sequences.get(caller, ()):
            if (caller, call.target) in blocked_cycle_edges or call.target in active:
                continue
            if not _append_call(messages, emitted, caller, call.target, call.raw, depth, options):
                continue
            is_internal = call.target in sequences
            if call.target in allowed and is_internal:
                walk(call.target, depth + 1, active | {call.target})
            if options.show_returns and is_internal:
                messages.append(SequenceMessage(call.target, caller, "return", depth, "return"))

    walk(root, 0, frozenset({root}))
    return tuple(messages)


def _append_call(
    messages: list[SequenceMessage],
    emitted: set[tuple[str, str, str]],
    caller: str,
    callee: str,
    label: str,
    depth: int,
    options: SequenceDiagramOptions,
) -> bool:
    key = (caller, callee, label)
    if not options.show_duplicate_calls and key in emitted:
        return False
    emitted.add(key)
    messages.append(SequenceMessage(caller, callee, label, depth, "call"))
    return True


def _cycle_edges(cycles: list[tuple[str, ...]]) -> set[tuple[str, str]]:
    return {
        (caller, callee)
        for cycle in cycles
        for caller, callee in zip(cycle, cycle[1:])
    }


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
