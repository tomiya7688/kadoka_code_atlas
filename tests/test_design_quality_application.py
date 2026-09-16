from pathlib import Path
from tempfile import TemporaryDirectory

from Src.models.config import AtlasConfig
from Src.process.application import ApplicationService, SourceAnalysisRequest
from Src.process.config_service import resolve_config


def test_design_quality_capability_is_enabled_by_default():
    resolved = resolve_config(AtlasConfig())
    assert "design_quality" in resolved.evaluators


def test_application_service_renders_design_quality_markdown():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text(
            "def first(): shared()\n"
            "def second(): shared()\n"
            "def shared(): pass\n",
            encoding="utf-8",
        )

        result = ApplicationService().evaluate_design_quality(
            SourceAnalysisRequest(source, "python"),
            high_fan_in=2,
        )

        assert result.format == "markdown"
        assert "# Design quality report" in result.content
        assert "high-fan-in" in result.content
        assert "shared" in result.content
