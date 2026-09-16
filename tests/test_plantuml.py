from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from Src.generators.class_diagram import build_class_diagram_bundle
from Src.generators.sequence_diagram import (
    SequenceDiagramOptions,
    build_sequence_diagram_bundle,
)
from Src.languages.python import PythonLanguageAdapter
from Src.models.config import AtlasConfig
from Src.process.application import ApplicationService, SourceAnalysisRequest
from Src.process.config_service import default_capabilities
from Src.renderers.plantuml_class_diagram import render_class_diagram
from Src.renderers.plantuml_sequence_diagram import render_sequence_diagram


def _module(source: str):
    return PythonLanguageAdapter().parse(source)


def test_plantuml_class_renderer_uses_renderer_neutral_model() -> None:
    bundle = build_class_diagram_bundle(
        _module(
            """
class Base: pass
class Child(Base):
    def run(self): pass
"""
        )
    )

    rendered = render_class_diagram(bundle.diagrams[0])

    assert rendered.startswith("@startuml\n")
    assert 'class "Base" as ' in rendered
    assert 'class "Child" as ' in rendered
    assert "<|--" in rendered
    assert rendered.endswith("@enduml\n")


def test_plantuml_sequence_renderer_preserves_calls_and_returns() -> None:
    bundle = build_sequence_diagram_bundle(
        _module(
            """
def main(): helper()
def helper(): pass
"""
        ),
        options=SequenceDiagramOptions(show_returns=True),
    )

    rendered = render_sequence_diagram(bundle.diagrams[0])

    assert rendered.startswith("@startuml\n")
    assert 'participant "main" as ' in rendered
    assert 'participant "helper" as ' in rendered
    assert " -> " in rendered
    assert " --> " in rendered
    assert rendered.endswith("@enduml\n")


def test_application_service_can_select_plantuml_and_save_puml() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            "class Helper: pass\nclass Service:\n    def run(self): Helper()\n",
            encoding="utf-8",
        )
        service = ApplicationService()

        result = service.generate_class_diagrams(
            SourceAnalysisRequest(source, "python"),
            renderer="plantuml",
        )
        paths = service.save_diagram_set(root / "output", result, category="class_diagrams")

        assert result.outputs
        assert all(output.format == "plantuml" for output in result.outputs)
        assert all(path.suffix == ".puml" for path in paths)
        assert paths[0].read_text(encoding="utf-8").startswith("@startuml\n")


def test_application_service_uses_configured_renderer_by_default() -> None:
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text(
            "def main(): helper()\ndef helper(): pass\n",
            encoding="utf-8",
        )
        service = ApplicationService(AtlasConfig(renderer="plantuml"))

        result = service.generate_sequence_diagrams(
            SourceAnalysisRequest(source, "python")
        )

        assert result.outputs
        assert all(output.format == "plantuml" for output in result.outputs)
        assert result.outputs[0].content.startswith("@startuml\n")


def test_application_service_rejects_unknown_diagram_renderer() -> None:
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text("class Sample: pass\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported diagram renderer"):
            ApplicationService().generate_class_diagrams(
                SourceAnalysisRequest(source, "python"),
                renderer="graphviz",
            )


def test_capabilities_advertise_plantuml_only_for_supported_generators() -> None:
    capabilities = {item.id: item for item in default_capabilities()}

    assert capabilities["class_diagram"].renderers == ("mermaid", "plantuml")
    assert capabilities["sequence_diagram"].renderers == ("mermaid", "plantuml")
    assert capabilities["object_diagram"].renderers == ("mermaid",)
