from pathlib import Path
from tempfile import TemporaryDirectory
from app import main


def test_comment_cli_writes_output_file():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        output = Path(folder) / "annotated.py"
        source.write_text("def load_config():\n    return {}\n", encoding="utf-8")
        assert main(["comment", str(source), "--language", "python", "--output", str(output)]) == 0
        assert "# Retrieves config." in output.read_text(encoding="utf-8")


def test_comment_cli_in_place():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "sample.py"
        source.write_text("def load_config():\n    return {}\n", encoding="utf-8")
        assert main(["comment", str(source), "--in-place"]) == 0
        assert "# Retrieves config." in source.read_text(encoding="utf-8")


def test_ci_cli_writes_mermaid_output_file():
    with TemporaryDirectory() as folder:
        source = Path(folder) / "build.yml"
        output = Path(folder) / "ci.mmd"
        source.write_text(
            """jobs:\n  test:\n    steps:\n      - name: pytest\n        run: pytest\n""",
            encoding="utf-8",
        )
        assert main(["ci", str(source), "--output", str(output)]) == 0
        assert "ci_test" in output.read_text(encoding="utf-8")


def test_deployment_cli_writes_diagram_folder():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        output = root / "output"
        (root / "app.py").write_text("import requests\n", encoding="utf-8")
        (root / "compose.yaml").write_text(
            "services:\n  app:\n    depends_on: [db]\n  db:\n    image: postgres:17\n",
            encoding="utf-8",
        )
        assert main(["deployment", str(root), "--mode", "full", "--output-dir", str(output)]) == 0
        diagrams = list((output / "deployment_diagrams").glob("*.mmd"))
        assert diagrams
        assert any("postgres" in path.read_text(encoding="utf-8") for path in diagrams)
