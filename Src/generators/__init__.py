"""Logical output generators."""

from .call_graph import generate_call_graph_mermaid
from .comment_backend import CommentTextBackend, RuleBasedCommentBackend
from .comment_generator import CommentGenerator, UnsupportedLanguageError
from .comments import CommentCandidate, RuleBasedCommentGenerator
from .responsibility import ResponsibilityRow, partitions, rows, to_csv, to_markdown

__all__ = [
    "CommentCandidate",
    "CommentTextBackend",
    "CommentGenerator",
    "RuleBasedCommentBackend",
    "RuleBasedCommentGenerator",
    "ResponsibilityRow",
    "rows",
    "to_csv",
    "to_markdown",
    "partitions",
    "UnsupportedLanguageError",
    "generate_call_graph_mermaid",
]
