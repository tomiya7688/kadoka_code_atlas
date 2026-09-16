from Src.evaluators.design_quality import DesignQualityThresholds, evaluate_design_quality
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.design_quality_markdown import render_design_quality_markdown


def _report(source: str, **thresholds):
    module = PythonLanguageAdapter().parse(source)
    return evaluate_design_quality(module, thresholds=DesignQualityThresholds(**thresholds))


def test_design_quality_reports_call_cycle_with_evidence():
    report = _report(
        """
def a(): b()
def b(): a()
""",
        high_fan_in=10,
        high_fan_out=10,
        large_series=10,
    )

    finding = next(item for item in report.findings if item.code == "call-cycle")
    assert finding.severity == "warning"
    assert "a" in finding.subject and "b" in finding.subject
    assert "cycle" in finding.interpretation.lower()
    assert any(metric.name == "cycle_count" and metric.value == 1 for metric in report.metrics)


def test_high_fan_in_is_informational_and_explains_legitimate_hubs():
    report = _report(
        """
def first(): shared()
def second(): shared()
def third(): shared()
def shared(): pass
""",
        high_fan_in=3,
        high_fan_out=10,
        large_series=10,
    )

    finding = next(
        item for item in report.findings
        if item.code == "high-fan-in" and item.subject == "shared"
    )
    assert finding.severity == "info"
    assert "fan-in = 3" in finding.evidence
    assert "Logging" in finding.note


def test_high_fan_out_and_large_partition_are_warnings():
    report = _report(
        """
def main():
    one()
    two()
    three()
def one(): pass
def two(): pass
def three(): pass
""",
        high_fan_in=10,
        high_fan_out=3,
        large_series=4,
    )

    codes = {item.code for item in report.findings}
    assert "high-fan-out" in codes
    assert "large-series" in codes


def test_markdown_renderer_includes_metrics_findings_and_notes():
    report = _report(
        """
def one(): shared()
def two(): shared()
def shared(): pass
""",
        high_fan_in=2,
        high_fan_out=10,
        large_series=10,
    )
    rendered = render_design_quality_markdown(report)

    assert rendered.startswith("# Design quality report\n")
    assert "## Metrics" in rendered
    assert "## Findings" in rendered
    assert "high-fan-in" in rendered
    assert "Evidence:" in rendered
    assert "Note:" in rendered
