"""Renderer-neutral deployment diagram generation."""

from __future__ import annotations

from dataclasses import dataclass
import re

from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.partition import partition_graph
from Src.models.deployment import DeploymentConnection, DeploymentNode, DeploymentTopology


@dataclass(frozen=True, slots=True)
class DeploymentDiagram:
    name: str
    nodes: tuple[DeploymentNode, ...]
    connections: tuple[DeploymentConnection, ...]


@dataclass(frozen=True, slots=True)
class DeploymentDiagramBundle:
    diagrams: tuple[DeploymentDiagram, ...]
    statistics: dict[str, int | tuple[int, ...]]


@dataclass(frozen=True, slots=True)
class _Edge:
    caller: str
    callee: str


@dataclass(slots=True)
class _Graph:
    nodes: set[str]
    edges: list[_Edge]

    def _call_graph(self) -> CallGraph:
        return CallGraph([CallEdge(item.caller, item.callee) for item in self.edges])

    def fan_in(self) -> dict[str, int]:
        counts = self._call_graph().fan_in()
        return {node: counts.get(node, 0) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        counts = self._call_graph().fan_out()
        return {node: counts.get(node, 0) for node in self.nodes}

    def cycles(self) -> list[tuple[str, ...]]:
        return self._call_graph().cycles()


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-")
    return normalized or "deployment"


def build_deployment_diagram_bundle(
    topology: DeploymentTopology,
    *,
    fan_in_threshold: int = 3,
) -> DeploymentDiagramBundle:
    """Partition a deployment topology while preserving confidence metadata."""

    node_by_id = {node.id: node for node in topology.nodes}
    graph = _Graph(
        set(node_by_id),
        [_Edge(item.source, item.target) for item in topology.connections],
    )
    partition = partition_graph(graph, fan_in_threshold=fan_in_threshold)
    diagrams: list[DeploymentDiagram] = []

    def make(name: str, ids: set[str]) -> DeploymentDiagram:
        return DeploymentDiagram(
            _safe_name(name),
            tuple(node_by_id[node_id] for node_id in sorted(ids) if node_id in node_by_id),
            tuple(
                item
                for item in topology.connections
                if item.source in ids and item.target in ids
            ),
        )

    for series in partition.series:
        ids = set(series)
        if ids:
            diagrams.append(make(f"series_{series[0]}", ids))

    for shared in partition.shared:
        ids = {shared}
        ids.update(item.source for item in topology.connections if item.target == shared)
        ids.update(item.target for item in topology.connections if item.source == shared)
        diagrams.append(make(f"shared_{shared}", ids))

    statistics = dict(partition.statistics)
    statistics["confirmed_node_count"] = sum(
        1 for node in topology.nodes if node.confidence == "confirmed"
    )
    statistics["inferred_node_count"] = sum(
        1 for node in topology.nodes if node.confidence == "inferred"
    )
    statistics["unknown_node_count"] = sum(
        1 for node in topology.nodes if node.confidence == "unknown"
    )
    return DeploymentDiagramBundle(tuple(diagrams), statistics)
