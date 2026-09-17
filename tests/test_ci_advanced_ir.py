from pathlib import Path

from Src.analyzers.ci import parse_github_actions
from Src.models.ci import CIMatrixAxis


FIXTURE = Path("tests/fixtures/ci/github_actions_advanced.yml")


def test_github_actions_preserves_advanced_job_metadata() -> None:
    workflow = parse_github_actions(FIXTURE.read_text(encoding="utf-8"))

    assert workflow.env_names == ("BASE_URL", "GLOBAL_TOKEN", "HARDCODED_SECRET")
    assert workflow.secret_refs == ("GLOBAL_TOKEN",)
    assert workflow.env_refs == ()
    assert "do-not-store-this-value" not in repr(workflow)

    job = workflow.jobs[0]
    assert job.display_name == "Test matrix"
    assert job.condition == "${{ github.event_name == 'pull_request' }}"
    assert job.timeout_minutes == 20
    assert job.continue_on_error is False
    assert job.env_names == ("SERVICE_URL", "JOB_TOKEN")
    assert job.env_refs == ("BASE_URL",)
    assert job.secret_refs == ("JOB_TOKEN",)
    assert job.retry is None

    assert job.strategy is not None
    assert job.strategy.fail_fast is False
    assert job.strategy.max_parallel == 2
    assert job.strategy.matrix is not None
    assert job.strategy.matrix.axes == (
        CIMatrixAxis("python", ("3.11", "3.12")),
        CIMatrixAxis("os", ("ubuntu-latest", "windows-latest")),
    )
    assert job.strategy.matrix.include == (
        (("python", "3.13"), ("os", "ubuntu-latest"), ("experimental", True)),
    )
    assert job.strategy.matrix.exclude == (
        (("python", "3.11"), ("os", "windows-latest")),
    )


def test_github_actions_normalizes_cache_artifacts_and_step_policy() -> None:
    workflow = parse_github_actions(FIXTURE.read_text(encoding="utf-8"))
    cache, tests, upload, download = workflow.jobs[0].steps

    assert cache.resources[0].kind == "cache"
    assert cache.resources[0].paths == ("~/.cache/pip", ".venv")
    assert cache.resources[0].key == "pip-${{ runner.os }}-${{ matrix.python }}"

    assert tests.condition == "${{ env.RUN_TESTS != '0' }}"
    assert tests.timeout_minutes == 8
    assert tests.continue_on_error == "${{ matrix.experimental || false }}"
    assert tests.env_names == ("STEP_TOKEN", "LOCAL_FLAG")
    assert tests.env_refs == ("RUN_TESTS",)
    assert tests.secret_refs == ("STEP_TOKEN",)
    # GitHub Actions has no native retry field. Unknown YAML must not become valid IR.
    assert tests.retry is None
    assert "enabled" not in repr(tests)

    assert upload.resources[0].kind == "artifact-upload"
    assert upload.resources[0].name == "reports-${{ matrix.python }}"
    assert upload.resources[0].paths == ("reports/", "coverage.xml")

    assert download.resources[0].kind == "artifact-download"
    assert download.resources[0].name == "seed-data"
    assert download.resources[0].paths == (".cache/seed",)


def test_expression_matrix_is_preserved_without_inventing_axes() -> None:
    workflow = parse_github_actions("""
jobs:
  test:
    strategy:
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}
    steps:
      - run: pytest
""")

    matrix = workflow.jobs[0].strategy.matrix
    assert matrix is not None
    assert matrix.expression == "${{ fromJSON(needs.prepare.outputs.matrix) }}"
    assert matrix.axes == ()
    assert matrix.include == ()
    assert matrix.exclude == ()
