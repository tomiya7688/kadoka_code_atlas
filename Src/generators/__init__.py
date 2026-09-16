"""Logical output generators."""

from Src.models import CommentCandidate
from Src.models.responsibility import ResponsibilityRow, ResponsibilityTable

from .call_graph import build_call_graph, build_call_graph_bundle
from .comment_backend import CommentTextBackend, RuleBasedCommentBackend
from .comment_generator import CommentGenerator, UnsupportedLanguageError
from .comments import RuleBasedCommentGenerator
from .flowchart import generate_flowchart
from .responsibility import build_responsibility_table_bundle, partitions, rows

__all__ = [
    "CommentCandidate",
    "CommentTextBackend",
    "CommentGenerator",
    "RuleBasedCommentBackend",
    "RuleBasedCommentGenerator",
    "ResponsibilityRow",
    "ResponsibilityTable",
    "rows",
    "partitions",
    "build_responsibility_table_bundle",
    "build_call_graph",
    "build_call_graph_bundle",
    "UnsupportedLanguageError",
    "generate_flowchart",
]
