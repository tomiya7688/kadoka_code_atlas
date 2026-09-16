"""Canonical language-neutral models for comment-generation candidates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommentTarget(str, Enum):
    """Kinds of source structure that can receive a generated comment."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    FIELD = "field"
    SIGNAL = "signal"
    BRANCH = "branch"


@dataclass(frozen=True)
class CommentCandidate:
    """The single shared candidate contract used by all comment pipelines.

    ``indent`` and ``line`` are source-rewrite metadata. ``text`` is the
    proposed comment text supplied to the selected text backend or compatibility
    rewriter; parser-specific AST objects never cross this boundary.
    """

    target: CommentTarget
    name: str
    line: int
    indent: str
    text: str


@dataclass(frozen=True)
class ParsedSource:
    """Normalized comment-analysis result returned by a CommentAdapter."""

    language: str
    candidates: tuple[CommentCandidate, ...]
