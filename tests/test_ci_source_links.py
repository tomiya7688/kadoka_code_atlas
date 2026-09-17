from Src.analyzers.ci import collect_ci_path_hints, parse_github_actions


def test_ci_step_collects_explicit_and_command_path_hints() -> None:
    workflow = parse_github_actions("""
jobs:
  verify:
    defaults:
      run:
        working-directory: ./backend
    steps:
      - name: Unit tests
        run: python -m pytest tests/unit/test_service.py Src
      - name: Local action
        uses: ./.github/actions/setup-python
      - name: Override directory
        working-directory: tools/checker
        run: python verify.py ./fixtures/sample.py
""")

    steps = workflow.jobs[0].steps
    assert steps[0].path_hints == ("backend", "tests/unit/test_service.py", "Src")
    assert steps[1].path_hints == ("backend", ".github/actions/setup-python")
    assert steps[2].path_hints == (
        "tools/checker",
        "verify.py",
        "fixtures/sample.py",
    )


def test_ci_path_hint_collector_preserves_job_and_step_provenance() -> None:
    workflow = parse_github_actions("""
jobs:
  test:
    steps:
      - name: Tests
        run: pytest tests/test_app.py
  lint:
    steps:
      - name: Lint
        run: ruff check Src tests
""")

    hints = collect_ci_path_hints(workflow)

    assert [(hint.job, hint.step, hint.path) for hint in hints] == [
        ("test", "Tests", "tests/test_app.py"),
        ("lint", "Lint", "Src"),
        ("lint", "Lint", "tests"),
    ]


def test_ci_path_hints_ignore_urls_flags_and_package_names() -> None:
    workflow = parse_github_actions("""
jobs:
  verify:
    steps:
      - run: python -m pip install requests https://example.com/archive.whl --quiet
""")

    assert workflow.jobs[0].steps[0].path_hints == ()
