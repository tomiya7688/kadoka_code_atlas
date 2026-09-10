from Src.generators.call_graph import generate_call_graph_mermaid
from Src.languages.python import PythonLanguageAdapter


def test_generate_mermaid_from_root_with_depth():
    module = PythonLanguageAdapter().parse(
        """
def main(): helper()
def helper(): leaf()
def leaf(): pass
"""
    )

    rendered = generate_call_graph_mermaid(module, root="main", max_depth=1)

    assert "n_main --> n_helper" in rendered
    assert "n_helper --> n_leaf" not in rendered
