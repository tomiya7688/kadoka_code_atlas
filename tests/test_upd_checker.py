from pathlib import Path


def test_upd_checker_dependency_tracks_latest_main_and_is_development_only() -> None:
    requirement = Path("tools/requirements-upd.txt").read_text(encoding="utf-8").strip()
    assert "upd-commander-base-design@main" in requirement
    assert "tools/requirements-upd.txt" not in Path("pyproject.toml").read_text(encoding="utf-8")


def test_oop_design_checker_ci_tracks_latest_main() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "git clone --depth 1 --branch main https://github.com/tomiya7688/oop-design-checker.git" in workflow
    assert "--fail-on danger" in workflow
