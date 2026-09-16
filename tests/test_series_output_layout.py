from pathlib import Path
from tempfile import TemporaryDirectory

from Src.generators.call_graph import build_call_graph_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.process.application import ApplicationService, SourceAnalysisRequest


def test_recursive_partition_exposes_series_output_placement_metadata() -> None:
    module = PythonLanguageAdapter().parse(
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
"""
    )

    bundle = build_call_graph_bundle(module, fan_in_threshold=10)

    assert [item.series_root for item in bundle.placements] == ["A", "B", "C"]
    assert [item.parent_series_root for item in bundle.placements] == [None, "A", "B"]
    assert [item.depth for item in bundle.placements] == [0, 1, 2]
    assert all(item.relative_dir[0].startswith("series_") for item in bundle.placements)
    assert len({item.relative_dir for item in bundle.placements}) == 3


def test_shared_high_fan_in_output_uses_fixed_shared_folder() -> None:
    module = PythonLanguageAdapter().parse(
        """
def first(): shared()
def second(): shared()
def shared(): pass
"""
    )

    bundle = build_call_graph_bundle(module, fan_in_threshold=2)
    shared = next(item for item in bundle.placements if item.shared)

    assert shared.series_root == "shared"
    assert shared.relative_dir == ("shared",)


def test_renderer_choice_does_not_change_class_series_folder() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            "class Repo: pass\nclass Service:\n    def run(self): Repo()\n",
            encoding="utf-8",
        )
        service = ApplicationService()
        request = SourceAnalysisRequest(source, "python")

        mermaid = service.generate_class_diagrams(request, renderer="mermaid")
        plantuml = service.generate_class_diagrams(request, renderer="plantuml")

        assert [item.relative_dir for item in mermaid.outputs] == [
            item.relative_dir for item in plantuml.outputs
        ]
        assert all(item.relative_dir for item in mermaid.outputs)


def test_renderer_choice_does_not_change_sequence_series_folder() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            "def main(): helper()\ndef helper(): pass\n",
            encoding="utf-8",
        )
        service = ApplicationService()
        request = SourceAnalysisRequest(source, "python")

        mermaid = service.generate_sequence_diagrams(request, renderer="mermaid")
        plantuml = service.generate_sequence_diagrams(request, renderer="plantuml")

        assert [item.relative_dir for item in mermaid.outputs] == [
            item.relative_dir for item in plantuml.outputs
        ]
        assert all(item.relative_dir for item in mermaid.outputs)
