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


def test_python_only_analysis_rejects_other_languages():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.cs"
        source.write_text("class Sample {}", encoding="utf-8")

        with pytest.raises(ValueError, match="Python"):
            ApplicationService().generate_call_graph(
                SourceAnalysisRequest(source, "csharp")
            )
