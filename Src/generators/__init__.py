"""Logical output generators."""

from .call_graph import generate_call_graph_mermaid
from .comment_generator import CommentGenerator, UnsupportedLanguageError
from .comments import CommentCandidate, RuleBasedCommentGenerator

__all__ = [
    "CommentCandidate",
    "CommentGenerator",
    "RuleBasedCommentGenerator",
    "UnsupportedLanguageError",
    "generate_call_graph_mermaid",
]
