from Src.analyzers.ci import parse_github_actions


def test_github_actions_extracts_jobs_dependencies_and_steps() -> None:
    workflow = parse_github_actions("""
name: Build
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Install
        run: python -m pip install -e .
      - name: Lint
        uses: astral-sh/ruff-action@v3
  build:
    needs: [test]
    steps:
      - name: Package
        run: python -m build
""")

    assert workflow.name == "Build"
    assert workflow.trigger == ("push", "pull_request")
    assert workflow.jobs[0].name == "test"
    assert [step.name for step in workflow.jobs[0].steps] == ["Install", "Lint"]
    assert workflow.jobs[0].steps[0].command == "python -m pip install -e ."
    assert workflow.jobs[0].steps[1].action == "astral-sh/ruff-action@v3"
    assert workflow.jobs[1].needs == ("test",)
