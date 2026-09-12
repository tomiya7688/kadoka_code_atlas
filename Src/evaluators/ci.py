"""Deterministic quality checks for normalized CI workflows."""

from __future__ import annotations

from dataclasses import dataclass

from Src.models.ci import CIWorkflow


@dataclass(frozen=True, slots=True)
class CIEvaluationFinding:
    code: str
    severity: str
    message: str


def _step_text(workflow: CIWorkflow) -> list[tuple[str, str]]:
    return [
        (job.name, " ".join(filter(None, (step.name, step.command, step.action))).lower())
        for job in workflow.jobs
        for step in job.steps
    ]


def evaluate_ci(workflow: CIWorkflow) -> tuple[CIEvaluationFinding, ...]:
    """Return review findings without depending on a CI provider syntax."""
    findings: list[CIEvaluationFinding] = []
    steps = _step_text(workflow)
    test_jobs = {job for job, text in steps if any(token in text for token in ("test", "pytest", "unittest"))}
    if not test_jobs:
        findings.append(CIEvaluationFinding("missing-test", "error", "No CI step appears to run tests."))

    build_jobs = {job for job, text in steps if any(token in text for token in ("build", "package", "compile"))}
    for job in workflow.jobs:
        if job.name in build_jobs and test_jobs and not set(job.needs) & test_jobs:
            findings.append(CIEvaluationFinding(
                "build-without-test-dependency",
                "warning",
                f"Build job '{job.name}' does not depend on a test job.",
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
