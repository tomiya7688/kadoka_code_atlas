"""Renderer-neutral logical timing charts."""

from __future__ import annotations

from dataclasses import dataclass
import re

from Src.analyzers.ir import ModuleIR


@dataclass(frozen=True, slots=True)
class TimingChartEvent:
    order: int
    kind: str
    line: int
    target: str | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class TimingChart:
    name: str
    owner: str
    is_async: bool
    events: tuple[TimingChartEvent, ...]


@dataclass(frozen=True, slots=True)
class TimingChartBundle:
    charts: tuple[TimingChart, ...]
    statistics: dict[str, int]


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-")
    return normalized or "timing"


def build_timing_chart_bundle(module: ModuleIR) -> TimingChartBundle:
    """Build one logical chart per function/method timing flow."""

    charts: list[TimingChart] = []
    counts = {
        "chart_count": 0,
        "async_flow_count": 0,
        "await_count": 0,
        "parallel_start_count": 0,
        "parallel_join_count": 0,
        "wait_count": 0,
        "sync_count": 0,
        "timer_count": 0,
        "callback_count": 0,
        "periodic_count": 0,
    }

    for flow in module.timing_flows:
        if not flow.events:
            continue
        events = tuple(
            TimingChartEvent(
                event.order,
                event.kind,
                event.line,
                event.target,
                event.detail,
            )
            for event in flow.events
        )
        charts.append(
            TimingChart(
                name=_safe_name(flow.owner),
                owner=flow.owner,
                is_async=flow.is_async,
                events=events,
            )
        )
        counts["chart_count"] += 1
        if flow.is_async:
            counts["async_flow_count"] += 1
        for event in events:
            key = f"{event.kind}_count"
            if key in counts:
                counts[key] += 1

    return TimingChartBundle(tuple(charts), counts)
