"""Graph-based design quality evaluation over normalized analysis models."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.call_sequence import build_sequence_relation_graph, resolve_call_sequences
from Src.analyzers.class_relations import build_class_relation_graph
from Src.analyzers.ir import ModuleIR
from Src.analyzers.partition import partition_graph
from Src.models.design_quality import DesignFinding, DesignMetric, DesignQualityReport


@dataclass(frozen=True, slots=True)
class DesignQualityThresholds:
    high_fan_in: int = 3
    high_fan_out: int = 5
    large_series: int = 8


def evaluate_design_quality(
    module: ModuleIR,
    *,
    thresholds: DesignQualityThresholds | None = None,
) -> DesignQualityReport:
    """Evaluate structural evidence without depending on language ASTs or renderers."""

    thresholds = thresholds or DesignQualityThresholds()
    if min(thresholds.high_fan_in, thresholds.high_fan_out, thresholds.large_series) < 1:
        raise ValueError("design quality thresholds must be >= 1")

    call_graph = build_sequence_relation_graph(module, resolve_call_sequences(module))
    class_graph = build_class_relation_graph(module)
    call_partition = partition_graph(call_graph, fan_in_threshold=thresholds.high_fan_in)
    class_partition = partition_graph(class_graph, fan_in_threshold=thresholds.high_fan_in)

    call_fan_in = call_graph.fan_in()
    call_fan_out = call_graph.fan_out()
    class_fan_in = class_graph.fan_in()
    class_fan_out = class_graph.fan_out()

    metrics = (
        DesignMetric("node_count", len(call_graph.nodes), "call_graph"),
        DesignMetric("edge_count", len(call_graph.edges), "call_graph"),
        DesignMetric("cycle_count", call_partition.cycle_count, "call_graph"),
        DesignMetric("series_count", call_partition.series_count, "call_graph"),
        DesignMetric("max_nodes_per_series", call_partition.max_nodes_per_series, "call_graph"),
        DesignMetric("shared_node_count", call_partition.shared_node_count, "call_graph"),
        DesignMetric("cross_series_edge_count", call_partition.cross_series_edge_count, "call_graph"),
        DesignMetric("node_count", len(class_graph.nodes), "class_graph"),
        DesignMetric("edge_count", len(class_graph.edges), "class_graph"),
        DesignMetric("cycle_count", class_partition.cycle_count, "class_graph"),
        DesignMetric("series_count", class_partition.series_count, "class_graph"),
        DesignMetric("max_nodes_per_series", class_partition.max_nodes_per_series, "class_graph"),
        DesignMetric("shared_node_count", class_partition.shared_node_count, "class_graph"),
        DesignMetric("cross_series_edge_count", class_partition.cross_series_edge_count, "class_graph"),
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
    findings.extend(
        _partition_findings(
            call_partition.max_nodes_per_series,
            call_partition.shared_node_count,
            call_partition.series_count,
            scope="call graph",
            large_series=thresholds.large_series,
        )
    )
    findings.extend(
        _partition_findings(
            class_partition.max_nodes_per_series,
            class_partition.shared_node_count,
            class_partition.series_count,
            scope="class graph",
            large_series=thresholds.large_series,
        )
    )
    return DesignQualityReport(metrics=metrics, findings=tuple(findings))


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
                interpretation="This node coordinates or depends on many distinct nodes.",
                note="Large orchestration points may be intentional, but can also indicate concentrated responsibility.",
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


def _partition_findings(
    max_nodes: int,
    shared_nodes: int,
    series_count: int,
    *,
    scope: str,
    large_series: int,
) -> list[DesignFinding]:
    findings: list[DesignFinding] = []
    if max_nodes >= large_series:
        findings.append(
            DesignFinding(
                code="large-series",
                severity="warning",
                subject=scope,
                evidence=f"largest partition contains {max_nodes} nodes",
                interpretation="A large connected series remains after shared-node separation.",
                note="Large cohesive features can be valid; compare with intended architectural boundaries.",
            )
        )
    if shared_nodes and series_count:
        findings.append(
            DesignFinding(
                code="shared-dependency-hubs",
                severity="info",
                subject=scope,
                evidence=f"shared nodes = {shared_nodes}; regular series = {series_count}",
                interpretation="Several relationships converge on shared high fan-in nodes.",
                note="Inspect whether these hubs are intentional infrastructure or accidental coupling.",
            )
        )
    return findings
