"""Optional comment-text backend contract."""
from __future__ import annotations
from typing import Protocol
from Src.models import CommentCandidate
class CommentTextBackend(Protocol):
    def generate(self, candidate: CommentCandidate) -> str:
        """Return comment text for a deterministic candidate."""
class RuleBasedCommentBackend:
    """Default local backend that preserves adapter-generated text."""
    def generate(self, candidate: CommentCandidate) -> str:
        return candidate.text