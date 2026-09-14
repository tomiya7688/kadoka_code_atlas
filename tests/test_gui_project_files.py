from pathlib import Path
from tempfile import TemporaryDirectory

from Src.ui.project_files import detect_language, discover_supported_files


def test_detect_language_for_primary_targets():
    assert detect_language(Path("main.py")) == "python"
    assert detect_language(Path("player.gd")) == "gdscript"
    assert detect_language(Path("Game.cs")) == "csharp"
    assert detect_language(Path("engine.cpp")) == "cpp"
    assert detect_language(Path("Main.java")) == "java"
    assert detect_language(Path("main.go")) == "go"
    assert detect_language(Path("build.yml")) == "yaml"


def test_discover_supported_files_skips_generated_and_tooling_directories():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
        (root / "src" / "game.cs").write_text("class Game {}\n", encoding="utf-8")
        (root / ".git").mkdir()
        (root / ".git" / "ignored.py").write_text("pass\n", encoding="utf-8")
        (root / "dist").mkdir()
        (root / "dist" / "generated.py").write_text("pass\n", encoding="utf-8")
        (root / "README.md").write_text("docs\n", encoding="utf-8")

        result = discover_supported_files(root)

        assert result == [root / "src" / "game.cs", root / "src" / "main.py"]
