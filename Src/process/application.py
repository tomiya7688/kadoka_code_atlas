"""UI-independent application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.analyzers.ci import parse_github_actions
from Src.data.files import read_text, write_text
from Src.data.project_files import detect_language, discover_supported_files
from Src.evaluators import evaluate_ci
from Src.generators import CommentGenerator, generate_call_graph_mermaid, rows, to_csv, to_markdown
from Src.generators.class_diagram import ClassDiagramOptions, build_class_diagram_bundle
from Src.generators.sequence_diagram import build_sequence_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.renderers import render_ci_workflow
from Src.renderers.mermaid_class_diagram import render_class_diagram
from Src.renderers.mermaid_sequence_diagram import render_sequence_diagram


@dataclass(frozen=True, slots=True)
class CommentRequest:
    source: Path
    language: str


@dataclass(frozen=True, slots=True)
class CIRequest:
    source: Path


@dataclass(frozen=True, slots=True)
class SourceAnalysisRequest:
    source: Path
    language: str


@dataclass(frozen=True, slots=True)
class CommentResult:
    content: str


@dataclass(frozen=True, slots=True)
class CIResult:
    content: str
    findings: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class TextResult:
    content: str
    format: str = "text"


@dataclass(frozen=True, slots=True)
class GeneratedOutput:
    name: str
    content: str
    format: str


@dataclass(frozen=True, slots=True)
class DiagramSetResult:
    outputs: tuple[GeneratedOutput, ...]
    statistics: dict[str, int | tuple[int, ...]]


class ApplicationService:
    """Orchestrate analysis and generation without presentation decisions."""

    def generate_comments(self, request: CommentRequest) -> CommentResult:
        return CommentResult(CommentGenerator().generate(read_text(request.source), request.language))

    def analyze_ci(self, request: CIRequest) -> CIResult:
        workflow = parse_github_actions(read_text(request.source))
        return CIResult(render_ci_workflow(workflow), evaluate_ci(workflow))

    def generate_call_graph(
        self,
        request: SourceAnalysisRequest,
        *,
        root: str | None = None,
        max_depth: int | None = None,
    ) -> TextResult:
        module = self._python_module(request)
        return TextResult(
            generate_call_graph_mermaid(module, root=root, max_depth=max_depth),
            format="mermaid",
        )

    def generate_responsibility_table(
        self,
        request: SourceAnalysisRequest,
        *,
        output_format: str = "markdown",
    ) -> TextResult:
        module = self._python_module(request)
        table_rows = rows(module)
        normalized = output_format.lower()
        if normalized == "csv":
            return TextResult(to_csv(table_rows), format="csv")
        if normalized != "markdown":
            raise ValueError(f"Unsupported responsibility output format: {output_format}")
        return TextResult(to_markdown(table_rows), format="markdown")

    def generate_class_diagrams(
        self,
        request: SourceAnalysisRequest,
        *,
        fan_in_threshold: int = 3,
        options: ClassDiagramOptions | None = None,
    ) -> DiagramSetResult:
        module = self._python_module(request)
        bundle = build_class_diagram_bundle(
            module,
            fan_in_threshold=fan_in_threshold,
            options=options,
        )
        outputs = tuple(
            GeneratedOutput(diagram.name, render_class_diagram(diagram), "mermaid")
            for diagram in bundle.diagrams
        )
        return DiagramSetResult(outputs, bundle.statistics)

    def generate_sequence_diagrams(
        self,
        request: SourceAnalysisRequest,
        *,
        fan_in_threshold: int = 3,
        max_depth: int = 8,
    ) -> DiagramSetResult:
        module = self._python_module(request)
        bundle = build_sequence_diagram_bundle(
            module,
            fan_in_threshold=fan_in_threshold,
            max_depth=max_depth,
        )
        outputs = tuple(
            GeneratedOutput(diagram.name, render_sequence_diagram(diagram), "mermaid")
            for diagram in bundle.diagrams
        )
        return DiagramSetResult(outputs, bundle.statistics)

    def detect_language(self, path: Path) -> str:
        return detect_language(path)

    def discover_supported_files(self, root: Path) -> list[Path]:
        return discover_supported_files(root)

    def save_text(self, path: Path, content: str) -> None:
        write_text(path, content)

    def save_diagram_set(
        self,
        output_root: Path,
        result: DiagramSetResult,
        *,
        category: str,
    ) -> tuple[Path, ...]:
        target = output_root / category
        paths: list[Path] = []
        for output in result.outputs:
            extension = ".mmd" if output.format == "mermaid" else ".txt"
            path = target / f"{output.name}{extension}"
            write_text(path, output.content)
            paths.append(path)
        return tuple(paths)

    @staticmethod
    def _python_module(request: SourceAnalysisRequest):
        language = request.language.lower().lstrip(".")
        if language not in {"python", "py"}:
            raise ValueError("This analysis is currently available for Python source files only.")
        return PythonLanguageAdapter().parse(read_text(request.source))
