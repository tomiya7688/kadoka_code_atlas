from Src.analyzers import CallGraph
from Src.generators import generate_call_graph_mermaid
from Src.renderers import render_call_graph


def test_call_graph_api_is_publicly_importable():
    assert CallGraph is not None
    assert callable(generate_call_graph_mermaid)
    assert callable(render_call_graph)
