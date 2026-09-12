from Src.generators import RuleBasedCommentBackend
from Src.models import CommentCandidate, CommentTarget

def test_default_backend_preserves_deterministic_comment_text():
    candidate=CommentCandidate(CommentTarget.CLASS,"Report",1,"","# Groups behavior related to report.")
    assert RuleBasedCommentBackend().generate(candidate)==candidate.text