import json
import subprocess
import sys
from pathlib import Path


def test_self_analysis_summary_is_deterministic_and_excludes_noise(tmp_path: Path) -> None:
    (tmp_path / "src.py").write_text("def load_config():\n    return {}\n", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "ignored.py").write_text("def ignored(:\n", encoding="utf-8")
    command = [sys.executable, "tools/self_analysis.py", str(tmp_path)]
    first = subprocess.check_output(command, text=True)
    second = subprocess.check_output(command, text=True)
    assert first == second
    summary = json.loads(first)
    assert summary["source_file_count"] == 1
    assert summary["parsed_file_count"] == 1
    assert summary["error_count"] == 0
    assert summary["generator_count"] > 0
