"""Language- and renderer-independent metrics over relation graphs."""

from __future__ import annotations

from Src.analyzers.partition import RelationGraph


def strongly_connected_components(graph: RelationGraph) -> tuple[tuple[str, ...], ...]:
    """Return deterministic strongly connected components for a relation graph."""

    adjacency: dict[str, tuple[str, ...]] = {node: () for node in graph.nodes}
    outgoing: dict[str, set[str]] = {node: set() for node in graph.nodes}
    for edge in graph.edges:
        outgoing.setdefault(edge.caller, set()).add(edge.callee)
        outgoing.setdefault(edge.callee, set())
    adjacency = {node: tuple(sorted(targets)) for node, targets in outgoing.items()}

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in adjacency.get(node, ()):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])

        if lowlinks[node] != indices[node]:
            return

        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        components.append(tuple(sorted(component)))

    for node in sorted(adjacency):
        if node not in indices:
            visit(node)

    return tuple(sorted(components, key=lambda item: (item[0], len(item), item)))


def cyclic_strongly_connected_components(
    graph: RelationGraph,
) -> tuple[tuple[str, ...], ...]:
    """Return SCCs that actually contain a dependency cycle."""

    self_loops = {
        edge.caller
        for edge in graph.edges
        if edge.caller == edge.callee
    }
    return tuple(
        component
        for component in strongly_connected_components(graph)
        if len(component) > 1 or component[0] in self_loops
    )
