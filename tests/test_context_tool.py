from pathlib import Path

from tools import context_tool


def test_repo_profile_is_bounded_and_ignores_cache(tmp_path: Path) -> None:
    (tmp_path / "Src").mkdir()
    (tmp_path / "Src" / "sample.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# Guide\ntext\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignored.py").write_text("\n" * 100, encoding="utf-8")

    profile = context_tool.repo_profile(tmp_path)

    assert profile["files"] == 2
    assert profile["text_lines"] == 3
    assert profile["file_types"][".py"] == 1


def test_markdown_index_records_headings_only(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Top\ntext\n## Detail\nmore\n", encoding="utf-8")

    index = context_tool.markdown_index(tmp_path)

    assert index == [
        {
            "path": "docs/guide.md",
            "headings": [
                {"line": 1, "level": 1, "title": "Top"},
                {"line": 3, "level": 2, "title": "Detail"},
            ],
        }
    ]


def test_python_structure_index_finds_symbols_and_imports(tmp_path: Path) -> None:
    src = tmp_path / "Src"
    src.mkdir()
    (src / "sample.py").write_text(
        "import json\nfrom pathlib import Path\n\nclass Demo:\n    def run(self):\n        return Path('.')\n",
        encoding="utf-8",
    )

    index = context_tool.python_structure_index(tmp_path)

    assert index["parse_errors"] == []
    assert index["imports"]["Src/sample.py"] == ["json", "pathlib"]
    assert [(item["kind"], item["qualified_name"]) for item in index["symbols"]] == [
        ("class", "Demo"),
        ("method", "Demo.run"),
    ]


def test_validation_plan_routes_tools_architecture_and_build() -> None:
    plan = context_tool.validation_plan(
        ["tools/context_tool.py", "docs/architecture/upd_commander.md", "pyproject.toml"]
    )

    assert "python -m pytest tests/test_next_issue.py tests/test_context_tool.py" in plan
    assert "python tools/context_tool.py policy-check" in plan
    assert "python -m build" in plan
    assert plan[-1] == "python -m pytest"


def test_policy_check_separates_errors_and_warnings(tmp_path: Path) -> None:
    (tmp_path / "Src" / "renderers").mkdir(parents=True)
    (tmp_path / "Src" / "languages").mkdir(parents=True)
    (tmp_path / "Src" / "generators").mkdir(parents=True)
    (tmp_path / "Src" / "renderers" / "bad.py").write_text(
        "from Src.languages import python\nfrom Src.analyzers import call_graph\n",
        encoding="utf-8",
    )
    (tmp_path / "Src" / "generators" / "legacy.py").write_text(
        "from Src.languages import python\n",
        encoding="utf-8",
    )

    findings = context_tool.architecture_findings(tmp_path)

    assert any(item.rule == "KCA101" and item.severity == "error" for item in findings)
    assert any(item.rule == "KCA201" and item.severity == "warning" for item in findings)
