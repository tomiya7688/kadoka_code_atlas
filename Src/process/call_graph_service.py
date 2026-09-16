"""Application service for partitioned call graph generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.data.files import read_text, write_text
from Src.generators.call_graph import build_call_graph_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_call_graph import render_call_graph


@dataclass(frozen=True, slots=True)
class CallGraphAnalysisRequest:
    source: Path
    language: str


@dataclass(frozen=True, slots=True)
class CallGraphOutput:
    name: str
    content: str
    format: str = "mermaid"


@dataclass(frozen=True, slots=True)
class CallGraphSetResult:
    outputs: tuple[CallGraphOutput, ...]
    statistics: dict[str, int | float | tuple[int, ...]]


class CallGraphService:
    """Generate partitioned call graph sets without UI-specific behavior."""

    def generate(
        self,
        request: CallGraphAnalysisRequest,
        *,
        fan_in_threshold: int = 3,
        root: str | None = None,
        max_depth: int | None = None,
    ) -> CallGraphSetResult:
        language = request.language.lower().lstrip(".")
        if language not in {"python", "py"}:
            raise ValueError(
                "Partitioned call graph analysis is currently available for Python source files only."
            )
        module = PythonLanguageAdapter().parse(read_text(request.source))
        bundle = build_call_graph_bundle(
            module,
            fan_in_threshold=fan_in_threshold,
            root=root,
            max_depth=max_depth,
        )
        outputs = tuple(
            CallGraphOutput(diagram.name, render_call_graph(diagram.graph))
            for diagram in bundle.diagrams
        )
        return CallGraphSetResult(outputs, bundle.statistics)

    @staticmethod
    def save(
        output_root: Path,
        result: CallGraphSetResult,
    ) -> tuple[Path, ...]:
        target = output_root / "call_graphs"
        paths: list[Path] = []
        seen: set[Path] = set()
        for output in result.outputs:
            path = target / f"{output.name}.mmd"
            if path in seen:
                raise ValueError(f"Duplicate call graph output path: {path}")
            seen.add(path)
            write_text(path, output.content)
            paths.append(path)
        return tuple(paths)
