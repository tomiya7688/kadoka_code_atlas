"""Graph-based design quality evaluation over normalized analysis models."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.call_sequence import build_sequence_relation_graph, resolve_call_sequences
from Src.analyzers.class_relations import build_class_relation_graph
from Src.analyzers.graph_metrics import cyclic_strongly_connected_components
from Src.analyzers.ir import ModuleIR
from Src.analyzers.partition import GraphPartition, partition_graph
from Src.models.design_quality import DesignFinding, DesignMetric, DesignQualityReport


@dataclass(frozen=True, slots=True)
class DesignQualityThresholds:
    high_fan_in: int = 3
    high_fan_out: int = 5
    large_series: int = 8
    high_cross_series_ratio: float = 0.25


def evaluate_design_quality(
    module: ModuleIR,
    *,
    thresholds: DesignQualityThresholds | None = None,
) -> DesignQualityReport:
    """Evaluate structural evidence without depending on language ASTs or renderers."""

    thresholds = thresholds or DesignQualityThresholds()
    if min(thresholds.high_fan_in, thresholds.high_fan_out, thresholds.large_series) < 1:
        raise ValueError("design quality integer thresholds must be >= 1")
    if not 0.0 <= thresholds.high_cross_series_ratio <= 1.0:
        raise ValueError("high_cross_series_ratio must be between 0 and 1")

    call_graph = build_sequence_relation_graph(module, resolve_call_sequences(module))
    class_graph = build_class_relation_graph(module)
    call_partition = partition_graph(call_graph, fan_in_threshold=thresholds.high_fan_in)
    class_partition = partition_graph(class_graph, fan_in_threshold=thresholds.high_fan_in)

    call_fan_in = call_graph.fan_in()
    call_fan_out = call_graph.fan_out()
    class_fan_in = class_graph.fan_in()
    class_fan_out = class_graph.fan_out()
    call_sccs = cyclic_strongly_connected_components(call_graph)
    class_sccs = cyclic_strongly_connected_components(class_graph)

    metrics = (
        DesignMetric("node_count", len(call_graph.nodes), "call_graph"),
        DesignMetric("edge_count", len(call_graph.edges), "call_graph"),
        *_scc_metrics(call_sccs, "call_graph"),
        *_partition_metrics(call_partition, "call_graph"),
        DesignMetric("node_count", len(class_graph.nodes), "class_graph"),
        DesignMetric("edge_count", len(class_graph.edges), "class_graph"),
        *_scc_metrics(class_sccs, "class_graph"),
        *_partition_metrics(class_partition, "class_graph"),
    )

    findings: list[DesignFinding] = []
    findings.extend(
        _hub_findings(
            call_fan_in,
            call_fan_out,
            scope="callable",
            high_fan_in=thresholds.high_fan_in,
            high_fan_out=thresholds.high_fan_out,
        )
    )
    findings.extend(
        _hub_findings(
            class_fan_in,
            class_fan_out,
            scope="class",
            high_fan_in=thresholds.high_fan_in,
            high_fan_out=thresholds.high_fan_out,
        )
    )
    findings.extend(_cycle_findings(call_graph.cycles(), "call-cycle", "call graph"))
    findings.extend(_cycle_findings(class_graph.cycles(), "class-cycle", "class graph"))
    findings.extend(_scc_findings(call_sccs, "call graph"))
    findings.extend(_scc_findings(class_sccs, "class graph"))
    findings.extend(
        _partition_findings(
            call_partition,
            scope="call graph",
            large_series=thresholds.large_series,
            high_cross_series_ratio=thresholds.high_cross_series_ratio,
        )
    )
    findings.extend(
        _partition_findings(
            class_partition,
            scope="class graph",
            large_series=thresholds.large_series,
            high_cross_series_ratio=thresholds.high_cross_series_ratio,
        )
    )
    return DesignQualityReport(metrics=metrics, findings=tuple(findings))


def _scc_metrics(
    components: tuple[tuple[str, ...], ...],
    scope: str,
) -> tuple[DesignMetric, ...]:
    return (
        DesignMetric("strongly_connected_component_count", len(components), scope),
        DesignMetric(
            "largest_scc_size",
            max((len(component) for component in components), default=0),
            scope,
        ),
    )


def _partition_metrics(
    partition: GraphPartition,
    scope: str,
) -> tuple[DesignMetric, ...]:
    """Expose diagram partition locality without coupling evaluation to renderers."""

    return (
        DesignMetric("cycle_count", partition.cycle_count, scope),
        DesignMetric("series_count", partition.series_count, scope),
        DesignMetric("max_nodes_per_series", partition.max_nodes_per_series, scope),
        DesignMetric("avg_nodes_per_series", partition.avg_nodes_per_series, scope),
        DesignMetric("max_partition_depth", partition.max_partition_depth, scope),
        DesignMetric("shared_node_count", partition.shared_node_count, scope),
        DesignMetric("shared_node_ratio", partition.shared_node_ratio, scope),
        DesignMetric("cross_series_edge_count", partition.cross_series_edge_count, scope),
        DesignMetric("cross_series_edge_ratio", partition.cross_series_edge_ratio, scope),
    )


def _hub_findings(
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    *,
    scope: str,
    high_fan_in: int,
    high_fan_out: int,
) -> list[DesignFinding]:
    findings: list[DesignFinding] = []
    for name, count in sorted(fan_in.items()):
        if count < high_fan_in:
            continue
        findings.append(
            DesignFinding(
                code="high-fan-in",
                severity="info",
                subject=name,
                evidence=f"{scope} fan-in = {count}",
                interpretation="This node is a dependency hub used from multiple places.",
                note=(
                    "Logging, configuration, event buses, dependency injection and shared "
                    "error handling can legitimately have high fan-in."
                ),
            )
        )
    for name, count in sorted(fan_out.items()):
        if count < high_fan_out:
            continue
        findings.append(
            DesignFinding(
                code="high-fan-out",
                severity="warning",
                subject=name,
                evidence=f"{scope} fan-out = {count}",
                interpretation=(
                    "This node coordinates or depends on many distinct nodes and is a "
                    "responsibility-concentration candidate."
                ),
                note="Large orchestration points may be intentional, but concentrated responsibility deserves review.",
            )
        )
    return findings


def _cycle_findings(
    cycles: list[tuple[str, ...]],
    code: str,
    scope: str,
) -> list[DesignFinding]:
    return [
        DesignFinding(
            code=code,
            severity="warning",
            subject=" -> ".join(cycle),
            evidence=f"Detected cycle with {max(len(cycle) - 1, 1)} edge(s).",
            interpretation=f"The {scope} contains a dependency cycle.",
            note="Some recursive algorithms are intentional; dependency cycles still deserve explicit review.",
        )
        for cycle in cycles
    ]


def _scc_findings(
    components: tuple[tuple[str, ...], ...],
    scope: str,
) -> list[DesignFinding]:
    return [
        DesignFinding(
            code="strongly-connected-component",
            severity="warning",
            subject=", ".join(component),
            evidence=f"mutually reachable nodes = {len(component)}",
            interpretation=(
                f"The {scope} contains a strongly connected dependency region that cannot "
                "be ordered as a simple acyclic layer sequence."
            ),
            note=(
                "Intentional recursion can form a small SCC; larger SCCs usually deserve "
                "architectural review because changes can propagate in both directions."
            ),
        )
        for component in components
    ]


def _partition_findings(
    partition: GraphPartition,
    *,
    scope: str,
    large_series: int,
    high_cross_series_ratio: float,
) -> list[DesignFinding]:
    findings: list[DesignFinding] = []
    if partition.max_nodes_per_series >= large_series:
        findings.append(
            DesignFinding(
                code="large-series",
                severity="warning",
                subject=scope,
                evidence=f"largest partition contains {partition.max_nodes_per_series} nodes",
                interpretation="A large connected series remains after recursive partitioning and shared-node separation.",
                note="Large cohesive features can be valid; compare with intended architectural boundaries.",
            )
        )
    if partition.shared_node_count and partition.series_count:
        findings.append(
            DesignFinding(
                code="shared-dependency-hubs",
                severity="info",
                subject=scope,
                evidence=(
                    f"shared nodes = {partition.shared_node_count}; regular series = {partition.series_count}; "
                    f"shared ratio = {partition.shared_node_ratio:.1%}"
                ),
                interpretation="Several relationships converge on shared high fan-in nodes.",
                note="Inspect whether these hubs are intentional infrastructure or accidental coupling.",
            )
        )
    if (
        partition.cross_series_edge_count
        and partition.cross_series_edge_ratio >= high_cross_series_ratio
    ):
        findings.append(
            DesignFinding(
                code="cross-series-coupling",
                severity="warning",
                subject=scope,
                evidence=(
                    f"cross-series edges = {partition.cross_series_edge_count}; "
                    f"ratio = {partition.cross_series_edge_ratio:.1%}"
                ),
                interpretation=(
                    "A substantial fraction of dependencies cross diagram-series boundaries, "
                    "which is a high-coupling candidate and weakens locality."
                ),
                note=(
                    "Shared orchestration can legitimately connect multiple series; compare the "
                    "cross-boundary dependencies with the intended module/component boundaries."
                ),
            )
        )
    return findings
