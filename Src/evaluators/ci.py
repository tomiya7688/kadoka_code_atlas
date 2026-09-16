"""Deterministic quality checks for normalized CI workflows."""

from __future__ import annotations

from dataclasses import dataclass

from Src.models.ci import CIJob, CIStep, CIWorkflow


@dataclass(frozen=True, slots=True)
class CIEvaluationFinding:
    code: str
    severity: str
    message: str


def _step_text_value(step: CIStep) -> str:
    return " ".join(filter(None, (step.name, step.command, step.action))).lower()


def _step_text(workflow: CIWorkflow) -> list[tuple[str, str]]:
    return [
        (job.name, _step_text_value(step))
        for job in workflow.jobs
        for step in job.steps
    ]


def _is_test_step(step: CIStep) -> bool:
    text = _step_text_value(step)
    return any(token in text for token in ("test", "pytest", "unittest"))


def _is_build_step(step: CIStep) -> bool:
    text = _step_text_value(step)
    return any(token in text for token in ("build", "package", "compile"))


def _has_test_before_build(job: CIJob) -> bool:
    seen_test = False
    for step in job.steps:
        if _is_test_step(step):
            seen_test = True
        if _is_build_step(step):
            return seen_test
    return False


def evaluate_ci(workflow: CIWorkflow) -> tuple[CIEvaluationFinding, ...]:
    """Return review findings without depending on a CI provider syntax."""
    findings: list[CIEvaluationFinding] = []
    steps = _step_text(workflow)
    test_jobs = {job for job, text in steps if any(token in text for token in ("test", "pytest", "unittest"))}
    if not test_jobs:
        findings.append(CIEvaluationFinding("missing-test", "error", "No CI step appears to run tests."))

    build_jobs = {job for job, text in steps if any(token in text for token in ("build", "package", "compile"))}
    for job in workflow.jobs:
        if job.name not in build_jobs or not test_jobs:
            continue
        depends_on_test_job = bool(set(job.needs) & test_jobs)
        if not depends_on_test_job and not _has_test_before_build(job):
            findings.append(CIEvaluationFinding(
                "build-without-test-dependency",
                "warning",
                f"Build job '{job.name}' is not preceded by tests in the same job and does not depend on a test job.",
            ))

    commands: dict[str, list[str]] = {}
    for job in workflow.jobs:
        for step in job.steps:
            if step.command:
                commands.setdefault(step.command.strip(), []).append(job.name)
    for command, jobs in sorted(commands.items()):
        if len(jobs) > 1:
            findings.append(CIEvaluationFinding(
                "duplicate-command",
                "warning",
                f"Command '{command}' is repeated in jobs: {', '.join(sorted(jobs))}.",
            ))
    return tuple(findings)
