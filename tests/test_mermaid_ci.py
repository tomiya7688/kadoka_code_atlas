from Src.analyzers.ci import parse_github_actions
from Src.renderers import render_ci_workflow


def test_mermaid_ci_renders_jobs_and_needs_edges() -> None:
    workflow = parse_github_actions("""
name: Build
on: [push]
jobs:
  test:
    steps:
      - name: Test
        run: pytest
  build:
    needs: [test]
    steps:
      - name: Package
        run: python -m build
""")

    rendered = render_ci_workflow(workflow)
    assert rendered.startswith("flowchart LR\n")
    assert 'ci_test["test<br/>Test"]' in rendered
    assert 'ci_build["build<br/>Package"]' in rendered
    assert "ci_test --> ci_build" in rendered
    assert "ci_trigger --> ci_test" in rendered
