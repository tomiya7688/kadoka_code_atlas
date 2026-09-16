from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from Src.models.class_diagram import ClassDiagram, ClassMember, ClassNode, ClassRelation
from Src.models.config import AtlasConfig
from Src.models.sequence_diagram import SequenceDiagram, SequenceMessage
from Src.process.application import ApplicationService, SourceAnalysisRequest
from Src.renderers.plantuml_class_diagram import render_class_diagram
from Src.renderers.plantuml_sequence_diagram import render_sequence_diagram


def test_plantuml_class_renderer_uses_renderer_neutral_model() -> None:
    diagram = ClassDiagram(
        name="sample",
        nodes=(
            ClassNode("Base"),
            ClassNode("Service", (ClassMember("run", ("value",), "public"),)),
            ClassNode("Repo", external=True),
        ),
        relations=(
            ClassRelation("Service", "Base", "inheritance"),
            ClassRelation("Service", "Repo", "uses"),
        ),
    )

    content = render_class_diagram(diagram)

    assert content.startswith("@startuml\n")
    assert 'class "Service"' in content
    assert "+run(value)" in content
    assert "<|--" in content
    assert ": uses" in content
    assert content.endswith("@enduml\n")


def test_plantuml_sequence_renderer_uses_renderer_neutral_model() -> None:
    diagram = SequenceDiagram(
        name="sample",
        participants=("main", "helper"),
        messages=(
            SequenceMessage("main", "helper", "load", 0, "call"),
            SequenceMessage("helper", "main", "return", 0, "return"),
        ),
    )

    content = render_sequence_diagram(diagram)

    assert content.startswith("@startuml\n")
    assert 'participant "main"' in content
    assert 'participant "helper"' in content
    assert " : load" in content
    assert "-->" in content
    assert content.endswith("@enduml\n")


def test_application_service_generates_and_saves_plantuml_class_diagrams() -> None:
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
        assert "@startuml" in paths[0].read_text(encoding="utf-8")


def test_application_service_config_selects_plantuml_sequence_renderer() -> None:
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text(
            "def main():\n    helper()\n\ndef helper():\n    return None\n",
            encoding="utf-8",
        )
        service = ApplicationService(AtlasConfig(renderer="plantuml"))

        result = service.generate_sequence_diagrams(
            SourceAnalysisRequest(source, "python"),
            max_depth=4,
        )

        assert result.outputs
        assert all(output.format == "plantuml" for output in result.outputs)
        assert all("@startuml" in output.content for output in result.outputs)


def test_application_service_rejects_unknown_diagram_renderer() -> None:
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text("class Sample: pass\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported diagram renderer"):
            ApplicationService().generate_class_diagrams(
                SourceAnalysisRequest(source, "python"),
                renderer="graphviz",
            )
