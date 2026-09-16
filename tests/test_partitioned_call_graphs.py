from pathlib import Path
from tempfile import TemporaryDirectory

from Src.generators.call_graph import build_call_graph_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.process.call_graph_service import CallGraphAnalysisRequest, CallGraphService


def _bundle(source: str, **kwargs):
    return build_call_graph_bundle(PythonLanguageAdapter().parse(source), **kwargs)


def test_call_graph_bundle_uses_recursive_shared_partitioner() -> None:
    bundle = _bundle(
        """
def A():
    B()
    X()

def B():
    C()
    D()

def C():
    E()
    F()

def D(): pass
def E(): pass
def F(): pass
def X(): pass
""",
        fan_in_threshold=10,
    )

    assert bundle.statistics["series_count"] == 3
    assert bundle.statistics["max_partition_depth"] == 2

    parent = next(item for item in bundle.diagrams if item.name.endswith("_A"))
    child = next(item for item in bundle.diagrams if item.name.endswith("_B"))
    nested = next(item for item in bundle.diagrams if item.name.endswith("_C"))

    assert parent.graph.nodes == {"A", "X", "B"}
    assert {(edge.caller, edge.callee) for edge in parent.graph.edges} == {
        ("A", "B"),
        ("A", "X"),
    }
    assert child.graph.nodes == {"B", "C", "D"}
    assert nested.graph.nodes == {"C", "E", "F"}


def test_call_graph_bundle_separates_shared_hub() -> None:
    bundle = _bundle(
        """
def first(): shared()
def second(): shared()
def shared(): sink()
def sink(): pass
""",
        fan_in_threshold=2,
    )

    shared = next(item for item in bundle.diagrams if item.name.startswith("shared_"))
    assert shared.graph.nodes == {"first", "second", "shared", "sink"}
    assert {(edge.caller, edge.callee) for edge in shared.graph.edges} == {
        ("first", "shared"),
        ("second", "shared"),
        ("shared", "sink"),
    }
    assert bundle.statistics["shared_node_count"] == 1


def test_call_graph_bundle_can_be_bounded_from_root() -> None:
    bundle = _bundle(
        """
def a(): b()
def b(): c()
def c(): d()
def d(): pass
""",
        root="a",
        max_depth=2,
        fan_in_threshold=10,
    )

    assert len(bundle.diagrams) == 1
    assert bundle.diagrams[0].graph.nodes == {"a", "b", "c"}
    assert {(edge.caller, edge.callee) for edge in bundle.diagrams[0].graph.edges} == {
        ("a", "b"),
        ("b", "c"),
    }


def test_call_graph_service_saves_all_outputs_under_call_graphs_folder() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        output = root / "output"
        source.write_text(
            "def main():\n    helper()\n\ndef helper():\n    pass\n",
            encoding="utf-8",
        )
        service = CallGraphService()

        result = service.generate(CallGraphAnalysisRequest(source, "python"))
        paths = service.save(output, result)

        assert paths
        assert all(path.parent.parent == output / "call_graphs" for path in paths)
        assert all(path.parent.name.startswith("series_") for path in paths)
        assert not list((output / "call_graphs").glob("*.mmd"))
        assert all(path.suffix == ".mmd" for path in paths)
        assert "flowchart LR" in paths[0].read_text(encoding="utf-8")
