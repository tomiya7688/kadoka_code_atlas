"""Intermediate representation for deterministic comment generation."""

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
    BRANCH = "branch"


@dataclass(frozen=True)
class CommentCandidate:
    """A comment proposed at a source line without modifying the source yet."""

    target: CommentTarget
    name: str
    line: int
    indent: str
    text: str


@dataclass(frozen=True)
class ParsedSource:
    """Language-neutral result returned by a language adapter."""

    language: str
    candidates: tuple[CommentCandidate, ...]
