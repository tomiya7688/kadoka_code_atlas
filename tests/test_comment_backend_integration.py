from Src.generators import CommentGenerator
from Src.models import CommentCandidate
class PrefixBackend:
    def generate(self, candidate: CommentCandidate) -> str:
        return "# Custom comment"

def test_custom_backend_replaces_comment_text():
    result=CommentGenerator(backend=PrefixBackend()).generate("def run_task():\n    pass\n", "python")
    assert "# Custom comment" in result