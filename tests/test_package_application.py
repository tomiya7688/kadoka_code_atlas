from pathlib import Path
from tempfile import TemporaryDirectory

from Src.process.application import ApplicationService, ProjectAnalysisRequest


def test_application_generates_and_saves_python_package_diagrams():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        package = root / "pkg"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "a.py").write_text("from . import b\n", encoding="utf-8")
        (package / "b.py").write_text("from . import a\n", encoding="utf-8")
        (package / "lone.py").write_text("VALUE = 1\n", encoding="utf-8")

        service = ApplicationService()
        result = service.generate_package_diagrams(ProjectAnalysisRequest(root))
        paths = service.save_diagram_set(
            root / "output",
            result,
            category="package_diagrams",
        )

        assert result.outputs
        assert result.statistics["cycle_count"] >= 1
        assert result.statistics["isolated_node_count"] >= 1
        assert all(output.format == "mermaid" for output in result.outputs)
        assert all(path.parent.parent.name == "package_diagrams" for path in paths)
        assert all(path.parent.name.startswith("series_") or path.parent.name == "shared" for path in paths)
        assert not list((root / "output" / "package_diagrams").glob("*.mmd"))
        assert all(path.suffix == ".mmd" and path.is_file() for path in paths)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        assert "pkg.a" in combined
        assert "pkg.b" in combined
        assert "pkg.lone" in combined
        assert "classDef cycle" in combined
        assert "classDef isolated" in combined
