from __future__ import annotations

import ast
from pathlib import Path

from Src.generators import CommentCandidate as PublicCommentCandidate
from Src.generators.comments import RuleBasedCommentGenerator
from Src.languages.python import PythonLanguageAdapter
from Src.models import CommentCandidate, CommentTarget


ROOT = Path(__file__).resolve().parents[1]


def test_public_and_common_ir_paths_share_one_comment_candidate_type() -> None:
    module = PythonLanguageAdapter().parse(
        "class Worker:\n    def load_data(self):\n        return 1\n"
    )

    candidates = RuleBasedCommentGenerator().generate(module)

    assert PublicCommentCandidate is CommentCandidate
    assert all(type(candidate) is CommentCandidate for candidate in candidates)
    assert [(item.target, item.name) for item in candidates] == [
        (CommentTarget.CLASS, "Worker"),
        (CommentTarget.METHOD, "load_data"),
    ]


def test_comment_candidate_is_defined_only_in_models() -> None:
    offenders: list[str] = []
    canonical = ROOT / "Src" / "models" / "comments.py"
    for path in (ROOT / "Src").rglob("*.py"):
        if path == canonical:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(
            isinstance(node, ast.ClassDef) and node.name == "CommentCandidate"
            for node in tree.body
        ):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
