"""High-level call graph generation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.call_graph import CallGraph
from Src.analyzers.ir import ModuleIR
from Src.analyzers.partition import partition_graph
from Src.generators.output_names import stable_output_name
from Src.renderers.mermaid_call_graph import render_call_graph


@dataclass(frozen=True, slots=True)
class CallGraphDiagram:
    name: str
    graph: CallGraph


@dataclass(frozen=True, slots=True)
class CallGraphBundle:
    diagrams: tuple[CallGraphDiagram, ...]
    statistics: dict[str, int | float | tuple[int, ...]]


def build_call_graph_bundle(
    module: ModuleIR,
    *,
    fan_in_threshold: int = 3,
    root: str | None = None,
    max_depth: int | None = None,
) -> CallGraphBundle:
    """Build partitioned caller-centered call graphs plus shared-hub graphs."""

    graph = CallGraph.from_module(module)
    if root is not None:
        graph = graph.reachable_from(root, max_depth=max_depth)

    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    shared = set(partition.shared)
    series_by_node = {
        node: index for index, series in enumerate(partition.series) for node in series
    }

    diagrams: list[CallGraphDiagram] = []
    for index, series in enumerate(partition.series, start=1):
        selected = set(series)
        edges = [
            edge
            for edge in graph.edges
            if edge.caller in selected
            and edge.callee not in shared
            and (
                edge.callee in selected
                or series_by_node.get(edge.callee) != series_by_node.get(edge.caller)
            )
        ]
        boundary_targets = {
            edge.callee for edge in edges if edge.callee not in selected
        }
        root_name = (
            partition.series_roots[index - 1]
            if index - 1 < len(partition.series_roots)
            else series[0]
        )
        diagrams.append(
            CallGraphDiagram(
                stable_output_name(
                    f"series_{index}",
                    root_name,
                    fallback="call_graph",
                ),
                CallGraph(
                    edges=edges,
                    explicit_nodes=selected | boundary_targets,
                ),
            )
        )

    for shared_node in partition.shared:
        edges = [
            edge
            for edge in graph.edges
            if edge.callee == shared_node or edge.caller == shared_node
        ]
        explicit_nodes = {
            shared_node,
            *(edge.caller for edge in edges),
            *(edge.callee for edge in edges),
        }
        diagrams.append(
            CallGraphDiagram(
                stable_output_name("shared", shared_node, fallback="call_graph"),
                CallGraph(edges=edges, explicit_nodes=explicit_nodes),
            )
        )

    return CallGraphBundle(tuple(diagrams), partition.statistics)


def generate_call_graph_mermaid(
    module: ModuleIR,
    *,
    root: str | None = None,
    max_depth: int | None = None,
    direction: str = "LR",
) -> str:
    """Build a call graph from IR and render it as Mermaid."""
    graph = CallGraph.from_module(module)
    if root is not None:
        graph = graph.reachable_from(root, max_depth=max_depth)
    return render_call_graph(graph, direction=direction)
