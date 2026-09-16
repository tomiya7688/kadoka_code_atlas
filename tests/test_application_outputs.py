from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from Src.process.application import ApplicationService, SourceAnalysisRequest


def test_application_service_generates_python_call_graph():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text(
            "def main():\n    helper()\n\ndef helper():\n    return None\n",
            encoding="utf-8",
        )

        result = ApplicationService().generate_call_graph(
            SourceAnalysisRequest(source, "python")
        )

        assert result.format == "mermaid"
        assert "flowchart" in result.content
        assert "main" in result.content
        assert "helper" in result.content


def test_application_service_generates_responsibility_markdown():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text(
            "class ConfigStore:\n    def load(self):\n        return {}\n",
            encoding="utf-8",
        )

        result = ApplicationService().generate_responsibility_table(
            SourceAnalysisRequest(source, "python")
        )

        assert result.format == "markdown"
        assert "| Class | Responsibility |" in result.content
        assert "ConfigStore" in result.content


def test_application_service_generates_and_saves_partitioned_class_diagrams():
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
            fan_in_threshold=3,
        )
        paths = service.save_diagram_set(root / "output", result, category="class_diagrams")

        assert result.outputs
        assert all(output.format == "mermaid" for output in result.outputs)
        assert all(path.parent.name == "class_diagrams" for path in paths)
        assert all(path.suffix == ".mmd" and path.is_file() for path in paths)
        assert "classDiagram" in paths[0].read_text(encoding="utf-8")


def test_application_service_generates_and_saves_object_diagrams():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            "class Repo: pass\nclass Service: pass\n\ndef build():\n"
            "    repo = Repo()\n    service = Service(name='api')\n    service.repo = repo\n",
            encoding="utf-8",
        )
        service = ApplicationService()

        result = service.generate_object_diagrams(SourceAnalysisRequest(source, "python"))
        paths = service.save_diagram_set(root / "output", result, category="object_diagrams")

        assert result.outputs
        assert all(output.format == "mermaid" for output in result.outputs)
        assert all(path.parent.name == "object_diagrams" for path in paths)
        assert all(path.suffix == ".mmd" and path.is_file() for path in paths)
        content = paths[0].read_text(encoding="utf-8")
        assert "service : Service" in content
        assert "repo : Repo" in content


def test_application_service_generates_and_saves_sequence_diagrams():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            "def main():\n    helper()\n\ndef helper():\n    return None\n",
            encoding="utf-8",
        )
        service = ApplicationService()

        result = service.generate_sequence_diagrams(
            SourceAnalysisRequest(source, "python"),
            max_depth=4,
        )
        paths = service.save_diagram_set(root / "output", result, category="sequence_diagrams")

        assert result.outputs
        assert all(output.format == "mermaid" for output in result.outputs)
        assert all(path.parent.name == "sequence_diagrams" for path in paths)
        assert all(path.suffix == ".mmd" and path.is_file() for path in paths)
        assert "sequenceDiagram" in paths[0].read_text(encoding="utf-8")


def test_python_only_analysis_rejects_other_languages():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.cs"
        source.write_text("class Sample {}", encoding="utf-8")

        with pytest.raises(ValueError, match="Python"):
            ApplicationService().generate_call_graph(
                SourceAnalysisRequest(source, "csharp")
            )
