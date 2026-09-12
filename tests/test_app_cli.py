from pathlib import Path
from tempfile import TemporaryDirectory
from app import main

def test_comment_cli_writes_output_file():
    with TemporaryDirectory() as folder:
        source=Path(folder)/"sample.py"; output=Path(folder)/"annotated.py"
        source.write_text("def load_config():\n    return {}\n", encoding="utf-8")
        assert main(["comment", str(source), "--language", "python", "--output", str(output)]) == 0
        assert "# Retrieves config." in output.read_text(encoding="utf-8")

def test_comment_cli_in_place():
    with TemporaryDirectory() as folder:
        source=Path(folder)/"sample.py"
        source.write_text("def load_config():\n    return {}\n", encoding="utf-8")
        assert main(["comment", str(source), "--in-place"]) == 0
        assert "# Retrieves config." in source.read_text(encoding="utf-8")

def test_ci_cli_writes_mermaid_output_file():
    with TemporaryDirectory() as folder:
        source=Path(folder)/"build.yml"; output=Path(folder)/"ci.mmd"
        source.write_text("""jobs:\n  test:\n    steps:\n      - name: pytest\n        run: pytest\n""", encoding="utf-8")
        assert main(["ci", str(source), "--output", str(output)]) == 0
        assert "ci_test" in output.read_text(encoding="utf-8")
