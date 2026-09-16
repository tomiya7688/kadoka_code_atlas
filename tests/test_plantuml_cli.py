from pathlib import Path
from tempfile import TemporaryDirectory

from app import main


def test_class_diagram_cli_writes_plantuml_files() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        output = root / "output"
        source.write_text(
            "class Repo: pass\nclass Service:\n    def run(self): Repo()\n",
            encoding="utf-8",
        )

        assert main(
            [
                "class-diagram",
                str(source),
                "--renderer",
                "plantuml",
                "--output-dir",
                str(output),
            ]
        ) == 0

        diagrams = list((output / "class_diagrams").glob("*.puml"))
        assert diagrams
        assert "@startuml" in diagrams[0].read_text(encoding="utf-8")


def test_sequence_diagram_cli_writes_plantuml_files() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        output = root / "output"
        source.write_text(
            "def main():\n    helper()\n\ndef helper():\n    return None\n",
            encoding="utf-8",
        )

        assert main(
            [
                "sequence-diagram",
                str(source),
                "--renderer",
                "plantuml",
                "--show-returns",
                "--output-dir",
                str(output),
            ]
        ) == 0

        diagrams = list((output / "sequence_diagrams").glob("*.puml"))
        assert diagrams
        content = diagrams[0].read_text(encoding="utf-8")
        assert "@startuml" in content
        assert "-->" in content


def test_class_diagram_cli_defaults_to_mermaid() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        output = root / "output"
        source.write_text("class Sample: pass\n", encoding="utf-8")

        assert main(["class-diagram", str(source), "--output-dir", str(output)]) == 0

        diagrams = list((output / "class_diagrams").glob("*.mmd"))
        assert diagrams
        assert "classDiagram" in diagrams[0].read_text(encoding="utf-8")
