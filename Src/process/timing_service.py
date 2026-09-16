"""Application service for logical timing analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.data.files import read_text, write_text
from Src.generators.timing_chart import build_timing_chart_bundle
from Src.languages.python_timing import PythonTimingLanguageAdapter
from Src.renderers.mermaid_timing_chart import render_timing_chart


@dataclass(frozen=True, slots=True)
class TimingAnalysisRequest:
    source: Path
    language: str = "python"


@dataclass(frozen=True, slots=True)
class TimingOutput:
    name: str
    content: str
    format: str = "mermaid"


@dataclass(frozen=True, slots=True)
class TimingSetResult:
    outputs: tuple[TimingOutput, ...]
    statistics: dict[str, int]


class TimingService:
    """Orchestrate logical timing analysis without UI decisions."""

    def generate(self, request: TimingAnalysisRequest) -> TimingSetResult:
        language = request.language.lower().lstrip(".")
        if language not in {"python", "py"}:
            raise ValueError("Timing analysis is currently available for Python source files only.")
        if not request.source.is_file():
            raise ValueError("Timing analysis expects a source file.")

        module = PythonTimingLanguageAdapter().parse(read_text(request.source))
        bundle = build_timing_chart_bundle(module)
        outputs = tuple(
            TimingOutput(chart.name, render_timing_chart(chart))
            for chart in bundle.charts
        )
        return TimingSetResult(outputs, bundle.statistics)

    @staticmethod
    def save(output_root: Path, result: TimingSetResult) -> tuple[Path, ...]:
        target = output_root / "timing_charts"
        paths: list[Path] = []
        seen: set[Path] = set()
        for output in result.outputs:
            path = target / f"{output.name}.mmd"
            if path in seen:
                raise ValueError(f"Duplicate timing output path: {path}")
            seen.add(path)
            write_text(path, output.content)
            paths.append(path)
        return tuple(paths)
