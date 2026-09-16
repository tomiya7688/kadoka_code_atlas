from pathlib import Path
from tempfile import TemporaryDirectory

from Src.process.timing_service import TimingAnalysisRequest, TimingService


def test_timing_service_generates_and_saves_mermaid_files() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            """
async def load():
    await fetch()

def save():
    write_file()
""",
            encoding="utf-8",
        )

        service = TimingService()
        result = service.generate(TimingAnalysisRequest(source, "python"))

        assert [output.name for output in result.outputs] == ["load", "save"]
        assert result.statistics["chart_count"] == 2
        paths = service.save(root / "output", result)
        assert {path.name for path in paths} == {"load.mmd", "save.mmd"}
        assert all(path.parent.name == "timing_charts" for path in paths)
        assert "sequenceDiagram" in paths[0].read_text(encoding="utf-8")


def test_timing_service_rejects_non_python_source() -> None:
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.cs"
        source.write_text("class Sample {}\n", encoding="utf-8")

        service = TimingService()
        try:
            service.generate(TimingAnalysisRequest(source, "csharp"))
        except ValueError as error:
            assert "Python" in str(error)
        else:
            raise AssertionError("Expected timing analysis to reject non-Python input")
