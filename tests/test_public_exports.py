from Src.analyzers import CallGraph
from Src.generators import build_call_graph
from Src.renderers import render_call_graph


def test_call_graph_api_is_publicly_importable():
    assert CallGraph is not None
    assert callable(build_call_graph)
    assert callable(render_call_graph)
