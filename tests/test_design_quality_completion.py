import pytest

from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.graph_metrics import (
    cyclic_strongly_connected_components,
    strongly_connected_components,
)
from Src.evaluators.design_quality import DesignQualityThresholds, evaluate_design_quality
from Src.languages.python import PythonLanguageAdapter


def _report(source: str, **thresholds):
    module = PythonLanguageAdapter().parse(source)
    return evaluate_design_quality(module, thresholds=DesignQualityThresholds(**thresholds))


def test_strongly_connected_components_are_deterministic_and_keep_isolated_nodes():
    graph = CallGraph(
        [
            CallEdge("a", "b"),
            CallEdge("b", "c"),
            CallEdge("c", "a"),
            CallEdge("d", "d"),
        ],
        explicit_nodes={"isolated"},
    )

    assert strongly_connected_components(graph) == (
        ("a", "b", "c"),
        ("d",),
        ("isolated",),
    )
    assert cyclic_strongly_connected_components(graph) == (
        ("a", "b", "c"),
        ("d",),
    )


def test_design_quality_reports_scc_metrics_and_finding():
    report = _report(
        """
def a(): b()
def b(): c()
def c(): a()
def outside(): a()
""",
        high_fan_in=10,
        high_fan_out=10,
        large_series=20,
    )

    metric_values = {
        (metric.scope, metric.name): metric.value
        for metric in report.metrics
    }
    assert metric_values[("call_graph", "strongly_connected_component_count")] == 1
    assert metric_values[("call_graph", "largest_scc_size")] == 3

    finding = next(
        item for item in report.findings
        if item.code == "strongly-connected-component"
    )
    assert set(finding.subject.split(", ")) == {"a", "b", "c"}
    assert "mutually reachable nodes = 3" in finding.evidence
    assert finding.severity == "warning"


def test_cross_series_dependency_ratio_is_reported_as_coupling_candidate():
    report = _report(
        """
def root():
    a()
    x()
def a(): b()
def b(): c()
def c(): pass
def x(): y()
def y(): z()
def z(): pass
""",
        high_fan_in=10,
        high_fan_out=10,
        large_series=20,
        high_cross_series_ratio=0.30,
    )

    finding = next(
        item for item in report.findings
        if item.code == "cross-series-coupling" and item.subject == "call graph"
    )
    assert "cross-series edges = 2" in finding.evidence
    assert "33.3%" in finding.evidence
    assert "high-coupling candidate" in finding.interpretation


def test_cross_series_ratio_threshold_is_validated():
    module = PythonLanguageAdapter().parse("def run(): pass\n")

    with pytest.raises(ValueError, match="high_cross_series_ratio"):
        evaluate_design_quality(
            module,
            thresholds=DesignQualityThresholds(high_cross_series_ratio=1.1),
        )
