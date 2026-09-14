from pathlib import Path
from tempfile import TemporaryDirectory

from Src.generators.communication_diagram import build_communication_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.process.application import ApplicationService, SourceAnalysisRequest
from Src.renderers.mermaid_communication_diagram import render_communication_diagram


def _bundle(source: str, **kwargs):
    module = PythonLanguageAdapter().parse(source)
    return build_communication_diagram_bundle(module, **kwargs)


def test_communication_diagram_numbers_nested_messages():
    bundle = _bundle(
        """
class Controller:
    def run(self):
        self.load()
        helper()
        self.finish()

    def load(self):
        pass

    def finish(self):
        pass

def helper():
    leaf()
def leaf():
    pass
"""
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("Controller_run"))

    assert [(item.order, item.source, item.target) for item in diagram.messages] == [
        ("1", "Controller", "Controller"),
        ("2", "Controller", "helper"),
        ("2.1", "helper", "leaf"),
        ("3", "Controller", "Controller"),
    ]


def test_communication_diagram_reuses_duplicate_filter():
    bundle = _bundle(
        """
def main():
    helper()
    helper()
def helper():
    pass
""",
        show_duplicate_calls=False,
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("main"))

    assert [(item.order, item.label) for item in diagram.messages] == [("1", "helper")]


def test_communication_diagram_excludes_cycles_via_sequence_analysis():
    bundle = _bundle(
        """
def a(): b()
def b(): a()
"""
    )

    assert bundle.statistics["cycle_count"] == 1
    assert all(not diagram.messages for diagram in bundle.diagrams)


def test_mermaid_communication_renderer_uses_numbered_edges():
    bundle = _bundle(
        """
def main(): helper()
def helper(): pass
"""
    )
    rendered = render_communication_diagram(bundle.diagrams[0])

    assert rendered.startswith("flowchart LR\n")
    assert 'p0["main"]' in rendered
    assert '1: helper' in rendered


def test_application_service_saves_communication_diagrams():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            "def main():\n    helper()\n\ndef helper():\n    pass\n",
            encoding="utf-8",
        )
        service = ApplicationService()

        result = service.generate_communication_diagrams(
            SourceAnalysisRequest(source, "python")
        )
        paths = service.save_diagram_set(
            root / "output",
            result,
            category="communication_diagrams",
        )

        assert result.outputs
        assert all(path.parent.name == "communication_diagrams" for path in paths)
        assert all(path.suffix == ".mmd" and path.is_file() for path in paths)
        assert "flowchart LR" in paths[0].read_text(encoding="utf-8")
