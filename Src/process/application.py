"""UI-independent application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.analyzers.ci import parse_github_actions
from Src.data.files import read_text
from Src.evaluators import evaluate_ci
from Src.generators import CommentGenerator
from Src.renderers import render_ci_workflow


@dataclass(frozen=True, slots=True)
class CommentRequest:
    source: Path
    language: str


@dataclass(frozen=True, slots=True)
class CIRequest:
    source: Path


@dataclass(frozen=True, slots=True)
class CommentResult:
    content: str


@dataclass(frozen=True, slots=True)
class CIResult:
    content: str
    findings: tuple[object, ...]


class ApplicationService:
    """Orchestrate analysis and generation without presentation decisions."""

    def generate_comments(self, request: CommentRequest) -> CommentResult:
        return CommentResult(CommentGenerator().generate(read_text(request.source), request.language))

    def analyze_ci(self, request: CIRequest) -> CIResult:
        workflow = parse_github_actions(read_text(request.source))
        return CIResult(render_ci_workflow(workflow), evaluate_ci(workflow))
