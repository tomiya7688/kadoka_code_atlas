from pathlib import Path
from tempfile import TemporaryDirectory

from app import main


def test_call_graph_cli_writes_partitioned_output_folder() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        output = root / "output"
        source.write_text(
            """
def A():
    B()
    X()

def B():
    C()
    D()

def C():
    E()
    F()

def D(): pass
def E(): pass
def F(): pass
def X(): pass
""",
            encoding="utf-8",
        )

        assert main(
            [
                "call-graph",
                str(source),
                "--fan-in-threshold",
                "10",
                "--output-dir",
                str(output),
            ]
        ) == 0

        diagrams = sorted((output / "call_graphs").glob("*.mmd"))
        assert len(diagrams) == 3
        assert all("flowchart LR" in path.read_text(encoding="utf-8") for path in diagrams)


def test_call_graph_cli_root_and_depth_bound_output() -> None:
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        output = root / "output"
        source.write_text(
            "def a(): b()\ndef b(): c()\ndef c(): d()\ndef d(): pass\n",
            encoding="utf-8",
        )

        assert main(
            [
                "call-graph",
                str(source),
                "--root",
                "a",
                "--max-depth",
                "2",
                "--output-dir",
                str(output),
            ]
        ) == 0

        diagrams = list((output / "call_graphs").glob("*.mmd"))
        assert len(diagrams) == 1
        content = diagrams[0].read_text(encoding="utf-8")
        assert '"a"' in content
        assert '"b"' in content
        assert '"c"' in content
        assert '"d"' not in content
