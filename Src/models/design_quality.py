"""Passive models for graph-based design quality evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DesignMetric:
    name: str
    value: int | float | str
    scope: str


@dataclass(frozen=True, slots=True)
class DesignFinding:
    code: str
    severity: str
    subject: str
    evidence: str
    interpretation: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class DesignQualityReport:
    metrics: tuple[DesignMetric, ...]
    findings: tuple[DesignFinding, ...]
