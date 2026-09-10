"""Language-independent data models shared by analyzers and generators."""

from .comments import CommentCandidate, CommentTarget, ParsedSource

__all__ = ["CommentCandidate", "CommentTarget", "ParsedSource"]
