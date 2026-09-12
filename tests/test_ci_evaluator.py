from Src.analyzers.ci import parse_github_actions
from Src.evaluators import evaluate_ci


def test_ci_evaluator_accepts_test_before_build() -> None:
    workflow = parse_github_actions("""
jobs:
  test:
    steps:
      - name: pytest
        run: pytest
  build:
    needs: [test]
    steps:
      - name: build
        run: python -m build
""")

    assert evaluate_ci(workflow) == ()


def test_ci_evaluator_reports_missing_test_and_duplicate_commands() -> None:
    workflow = parse_github_actions("""
jobs:
  lint:
    steps:
      - name: check
        run: python -m ruff check .
  package:
    steps:
      - name: package
        run: python -m build
  release:
    steps:
      - name: package
        run: python -m build
""")

    findings = evaluate_ci(workflow)
    assert {finding.code for finding in findings} == {"missing-test", "duplicate-command"}


def test_ci_evaluator_reports_build_without_test_dependency() -> None:
    workflow = parse_github_actions("""
jobs:
  test:
    steps:
      - name: test
        run: pytest
  build:
    steps:
      - name: build
        run: python -m build
""")

    assert [finding.code for finding in evaluate_ci(workflow)] == ["build-without-test-dependency"]
