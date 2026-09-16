"""Markdown renderer for graph-based design quality reports."""

from __future__ import annotations

from Src.models.design_quality import DesignQualityReport


def render_design_quality_markdown(report: DesignQualityReport) -> str:
    lines = ["# Design quality report", "", "## Metrics", "", "| Scope | Metric | Value |", "| --- | --- | ---: |"]
    for metric in report.metrics:
        lines.append(f"| {metric.scope} | {metric.name} | {metric.value} |")

    lines.extend(["", "## Findings", ""])
    if not report.findings:
        lines.append("No structural findings were detected with the current thresholds.")
        return "\n".join(lines) + "\n"

    for finding in report.findings:
        lines.extend(
            [
                f"### [{finding.severity.upper()}] {finding.code}: {finding.subject}",
                "",
                f"- Evidence: {finding.evidence}",
                f"- Interpretation: {finding.interpretation}",
            ]
        )
        if finding.note:
            lines.append(f"- Note: {finding.note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
