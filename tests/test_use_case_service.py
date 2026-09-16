from pathlib import Path
from tempfile import TemporaryDirectory

from Src.process.use_case_service import UseCaseAnalysisRequest, UseCaseService


def test_use_case_service_generates_and_saves_gui_originated_diagrams() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "ui.py"
        source.write_text(
            """
class Window:
    def __init__(self):
        self.save = Button(text="Save", command=self.on_save)
    def on_save(self):
        self.persist()
    def persist(self):
        pass
""",
            encoding="utf-8",
        )

        service = UseCaseService()
        result = service.generate(UseCaseAnalysisRequest(source, "python"))

        assert len(result.outputs) == 1
        assert result.statistics["use_case_count"] == 1
        paths = service.save(root / "output", result)
        assert len(paths) == 1
        assert paths[0].parent.name == "use_case_diagrams"
        assert "Save" in paths[0].read_text(encoding="utf-8")


def test_use_case_service_returns_no_outputs_without_gui_input() -> None:
    with TemporaryDirectory() as folder:
        source = Path(folder) / "service.py"
        source.write_text("def run():\n    work()\n", encoding="utf-8")

        result = UseCaseService().generate(UseCaseAnalysisRequest(source, "python"))
        assert result.outputs == ()
        assert result.statistics["use_case_count"] == 0
