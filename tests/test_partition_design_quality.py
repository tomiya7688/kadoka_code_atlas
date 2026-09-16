from Src.evaluators.design_quality import DesignQualityThresholds, evaluate_design_quality
from Src.languages.python import PythonLanguageAdapter


def test_design_quality_exposes_recursive_partition_locality_metrics() -> None:
    module = PythonLanguageAdapter().parse(
        """
def A():
    B()
    X()

def B():
    C()
    D()

def C():
    E()
    F()

def D(): pass
def E(): pass
def F(): pass
def X(): pass
"""
    )

    report = evaluate_design_quality(
        module,
        thresholds=DesignQualityThresholds(
            high_fan_in=10,
            high_fan_out=10,
            large_series=20,
        ),
    )
    call_metrics = {
        metric.name: metric.value
        for metric in report.metrics
        if metric.scope == "call_graph"
    }

    assert call_metrics["series_count"] == 3
    assert call_metrics["max_partition_depth"] == 2
    assert call_metrics["cross_series_edge_count"] == 2
    assert call_metrics["cross_series_edge_ratio"] == 2 / 6
    assert call_metrics["shared_node_ratio"] == 0.0
