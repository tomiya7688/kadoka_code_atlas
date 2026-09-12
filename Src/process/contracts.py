"""Process-level contracts for language-independent orchestration."""
from typing import Protocol
class CommentAdapter(Protocol):
    language: str
    def parse(self, source: str): ...