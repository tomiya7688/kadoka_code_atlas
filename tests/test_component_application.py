from pathlib import Path
from tempfile import TemporaryDirectory

from Src.process.application import ApplicationService, ProjectAnalysisRequest


def test_application_generates_and_saves_python_component_diagrams():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        ui = root / "ui"
        data = root / "data"
        ui.mkdir()
        data.mkdir()
        (ui / "__init__.py").write_text("", encoding="utf-8")
        (data / "__init__.py").write_text("", encoding="utf-8")
        (ui / "view.py").write_text(
            "from data import repo\nimport requests\n",
            encoding="utf-8",
        )
        (data / "repo.py").write_text(
            "from ui import view\n",
            encoding="utf-8",
        )

        service = ApplicationService()
        result = service.generate_component_diagrams(ProjectAnalysisRequest(root))
        paths = service.save_diagram_set(
            root / "output",
            result,
            category="component_diagrams",
        )

        assert result.outputs
        assert result.statistics["cycle_count"] >= 1
        assert result.statistics["external_node_count"] == 1
        assert all(output.format == "mermaid" for output in result.outputs)
        assert all(path.parent.parent.name == "component_diagrams" for path in paths)
        assert all(path.parent.name.startswith("series_") or path.parent.name == "shared" for path in paths)
        assert not list((root / "output" / "component_diagrams").glob("*.mmd"))
        assert all(path.suffix == ".mmd" and path.is_file() for path in paths)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        assert 'component_ui["ui"]' in combined
        assert 'component_data["data"]' in combined
        assert '(["requests"])' in combined
        assert "classDef cycle" in combined
