from pathlib import Path


def test_upd_checker_dependency_is_pinned_and_development_only() -> None:
    requirement = Path("tools/requirements-upd.txt").read_text(encoding="utf-8").strip()
    assert "upd-commander-base-design@8c78a312a759107fafa3b55e6092a888e4cb6f7f" in requirement
    assert "tools/requirements-upd.txt" not in Path("pyproject.toml").read_text(encoding="utf-8")
