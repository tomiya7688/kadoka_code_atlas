from Src.analyzers.call_graph import CallGraph
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_call_graph import render_call_graph


def _graph(source: str) -> CallGraph:
    module = PythonLanguageAdapter().parse(source)
    return CallGraph.from_module(module)


def test_builds_edges_and_metrics():
    graph = _graph(
        """
def main():
    helper()
    shared()

def helper():
    shared()

def shared():
    return 1
"""
    )

    assert {(edge.caller, edge.callee) for edge in graph.edges} == {
        ("main", "helper"),
        ("main", "shared"),
        ("helper", "shared"),
    }
    assert graph.fan_in()["shared"] == 2
    assert graph.fan_out()["main"] == 2
    assert graph.high_fan_in_nodes(threshold=2) == {"shared"}


def test_reachable_respects_depth():
    graph = _graph(
        """
def a(): b()
def b(): c()
def c(): d()
def d(): pass
"""
    )
    depth_two = graph.reachable_from("a", max_depth=2)
    assert {(edge.caller, edge.callee) for edge in depth_two.edges} == {
        ("a", "b"),
        ("b", "c"),
    }


def test_detects_cycles_without_infinite_walk():
    graph = _graph(
        """
def a(): b()
def b(): c()
def c(): a()
"""
    )
    assert graph.cycles() == [("a", "b", "c", "a")]


def test_mermaid_renderer_outputs_edges():
    graph = _graph(
        """
def main(): helper()
def helper(): pass
"""
    )
    rendered = render_call_graph(graph)
    assert rendered.startswith("flowchart LR\n")
    assert 'n_main["main"]' in rendered
    assert "n_main --> n_helper" in rendered
