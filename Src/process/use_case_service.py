"""Application service for GUI-originated use case analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.data.files import read_text, write_text
from Src.generators.use_case_diagram import build_use_case_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.languages.python_usecase import PythonUseCaseLanguageAdapter
from Src.renderers.mermaid_use_case_diagram import render_use_case_diagram


@dataclass(frozen=True, slots=True)
class UseCaseAnalysisRequest:
    source: Path
    language: str = "python"


@dataclass(frozen=True, slots=True)
class UseCaseOutput:
    name: str
    content: str
    format: str = "mermaid"


@dataclass(frozen=True, slots=True)
class UseCaseSetResult:
    outputs: tuple[UseCaseOutput, ...]
    statistics: dict[str, int]


class UseCaseService:
    """Orchestrate use case analysis without presentation-layer parsing."""

    def generate(
        self,
        request: UseCaseAnalysisRequest,
        *,
        max_depth: int = 5,
    ) -> UseCaseSetResult:
        language = request.language.lower().lstrip(".")
        if language not in {"python", "py"}:
            raise ValueError("Use case analysis is currently available for Python source files only.")
        if not request.source.is_file():
            raise ValueError("Use case analysis expects a source file.")

        source = read_text(request.source)
        module = PythonLanguageAdapter().parse(source)
        event_module = PythonUseCaseLanguageAdapter().parse(source)
        module.input_events = event_module.input_events
        bundle = build_use_case_diagram_bundle(module, max_depth=max_depth)
        outputs = tuple(
            UseCaseOutput(diagram.name, render_use_case_diagram(diagram))
            for diagram in bundle.diagrams
        )
        return UseCaseSetResult(outputs, bundle.statistics)

    @staticmethod
    def save(output_root: Path, result: UseCaseSetResult) -> tuple[Path, ...]:
        target = output_root / "use_case_diagrams"
        paths: list[Path] = []
        seen: set[Path] = set()
        for output in result.outputs:
            path = target / f"{output.name}.mmd"
            if path in seen:
                raise ValueError(f"Duplicate use case output path: {path}")
            seen.add(path)
            write_text(path, output.content)
            paths.append(path)
        return tuple(paths)
