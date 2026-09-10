"""Logical output generators."""

from .call_graph import generate_call_graph_mermaid
from .comments import CommentCandidate, RuleBasedCommentGenerator

__all__ = [
    "CommentCandidate",
    "RuleBasedCommentGenerator",
    "generate_call_graph_mermaid",
]
