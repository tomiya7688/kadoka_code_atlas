from pathlib import Path
from tempfile import TemporaryDirectory

from Src.data.project_files import (
    detect_language,
    discover_deployment_files,
    discover_supported_files,
)


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


def test_discover_deployment_files_finds_docker_compose_and_manifests():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "Dockerfile").write_text("FROM python:3.13\n", encoding="utf-8")
        (root / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
        (root / "k8s").mkdir()
        (root / "k8s" / "deployment.yaml").write_text("kind: Deployment\n", encoding="utf-8")
        (root / "dist").mkdir()
        (root / "dist" / "compose.yaml").write_text("services: {}\n", encoding="utf-8")

        result = discover_deployment_files(root)

        assert set(result) == {
            root / "Dockerfile",
            root / "compose.yaml",
            root / "k8s" / "deployment.yaml",
        }
