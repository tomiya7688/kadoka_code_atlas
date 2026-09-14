"""UI-independent application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.analyzers.ci import parse_github_actions
from Src.data.files import read_text
from Src.evaluators import evaluate_ci
from Src.generators import CommentGenerator, generate_call_graph_mermaid, rows, to_csv, to_markdown
from Src.languages.python import PythonLanguageAdapter
from Src.renderers import render_ci_workflow


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

    @staticmethod
    def _python_module(request: SourceAnalysisRequest):
        language = request.language.lower().lstrip(".")
        if language not in {"python", "py"}:
            raise ValueError("This analysis is currently available for Python source files only.")
        return PythonLanguageAdapter().parse(read_text(request.source))
