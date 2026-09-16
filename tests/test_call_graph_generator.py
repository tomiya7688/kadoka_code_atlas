from Src.generators.call_graph import build_call_graph
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_call_graph import render_call_graph


def test_build_call_graph_from_root_with_depth():
    module = PythonLanguageAdapter().parse(
        """
def main(): helper()
def helper(): leaf()
def leaf(): pass
"""
    )

    graph = build_call_graph(module, root="main", max_depth=1)
    rendered = render_call_graph(graph)

    assert "n_main --> n_helper" in rendered
    assert "n_helper --> n_leaf" not in rendered
