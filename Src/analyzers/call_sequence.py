"""Language-neutral call-sequence analysis over Common IR."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.ir import ModuleIR
from Src.analyzers.ir_queries import functions, qualified_name


@dataclass(frozen=True, slots=True)
class ResolvedCall:
    raw: str
    target: str


@dataclass(slots=True)
class SequenceRelationGraph:
    """Internal callable graph used by the shared partitioner."""

    nodes: set[str] = field(default_factory=set)
    edges: list[CallEdge] = field(default_factory=list)

    def fan_in(self) -> dict[str, int]:
        callers: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            callers[edge.callee].add(edge.caller)
        return {node: len(callers[node]) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        callees: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            callees[edge.caller].add(edge.callee)
        return {node: len(callees[node]) for node in self.nodes}

    def cycles(self) -> list[tuple[str, ...]]:
        return CallGraph(list(self.edges)).cycles()


def resolve_call_sequences(module: ModuleIR) -> dict[str, tuple[ResolvedCall, ...]]:
    """Resolve ordered raw calls to known callable qualified names where possible."""
    callable_entities = functions(module)
    qualified = {qualified_name(entity): entity for entity in callable_entities}
    by_simple_name: dict[str, list[str]] = defaultdict(list)
    for name, entity in qualified.items():
        by_simple_name[entity.name].append(name)

    resolved: dict[str, tuple[ResolvedCall, ...]] = {}
    for caller_name, entity in qualified.items():
        ordered = entity.call_sequence or entity.calls
        items: list[ResolvedCall] = []
        for raw in ordered:
            target = _resolve_target(raw, caller_name, entity.parent, qualified, by_simple_name)
            items.append(ResolvedCall(raw=raw, target=target))
        resolved[caller_name] = tuple(items)
    return resolved


def build_sequence_relation_graph(
    module: ModuleIR,
    sequences: dict[str, tuple[ResolvedCall, ...]] | None = None,
) -> SequenceRelationGraph:
    """Build the partition graph from internal callable-to-callable relationships."""
    sequences = sequences or resolve_call_sequences(module)
    internal = set(sequences)
    edges: list[CallEdge] = []
    seen: set[tuple[str, str]] = set()
    for caller, calls in sequences.items():
        for call in calls:
            if call.target not in internal:
                continue
            key = (caller, call.target)
            if key in seen:
                continue
            seen.add(key)
            edges.append(CallEdge(caller, call.target))
    return SequenceRelationGraph(nodes=internal, edges=edges)


def _resolve_target(
    raw: str,
    caller_name: str,
    parent: str | None,
    qualified: dict[str, object],
    by_simple_name: dict[str, list[str]],
) -> str:
    if raw in qualified:
        return raw

    if parent and raw.startswith(("self.", "cls.")):
        suffix = raw.split(".", 1)[1]
        candidate = f"{parent}.{suffix}"
        if candidate in qualified:
            return candidate

    if "." not in raw:
        matches = by_simple_name.get(raw, ())
        if len(matches) == 1:
            return matches[0]

    return raw
