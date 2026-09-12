"""Conservative GitHub Actions workflow analyzer."""

from __future__ import annotations

import re

from .models import CIJob, CIStep, CIWorkflow

_JOB = re.compile(r"^  ([A-Za-z0-9_.-]+):\s*$")
_STEP_NAME = re.compile(r"^      - name:\s*(.+?)\s*$")
_STEP_RUN = re.compile(r"^        run:\s*(.+?)\s*$")
_STEP_USES = re.compile(r"^        uses:\s*(.+?)\s*$")


def parse_github_actions(source: str) -> CIWorkflow:
    """Extract workflow metadata without evaluating expressions or shell code."""
    lines = source.splitlines()
    name = None
    triggers: list[str] = []
    jobs: list[CIJob] = []
    current_job: str | None = None
    current_needs: list[str] = []
    current_steps: list[CIStep] = []
    pending_step: str | None = None

    def flush_step() -> None:
        nonlocal pending_step
        if pending_step is not None:
            current_steps.append(CIStep(pending_step))
            pending_step = None

    def flush_job() -> None:
        nonlocal current_job, current_needs, current_steps
        if current_job is not None:
            flush_step()
            jobs.append(CIJob(current_job, tuple(current_needs), tuple(current_steps)))
        current_job = None
        current_needs = []
        current_steps = []

    for line in lines:
        if line.startswith("name:"):
            name = line.partition(":")[2].strip() or None
        elif line.startswith("on:"):
            value = line.partition(":")[2].strip()
            if value and value not in ("{}", "[]"):
                triggers.extend(item.strip() for item in value.strip("[]").split(",") if item.strip())
        elif match := _JOB.match(line):
            flush_job()
            current_job = match.group(1)
        elif current_job is not None and line.startswith("    needs:"):
            value = line.partition(":")[2].strip().strip("[]")
            current_needs = [item.strip() for item in value.split(",") if item.strip()]
        elif current_job is not None and (match := _STEP_NAME.match(line)):
            flush_step()
            pending_step = match.group(1).strip().strip("\"'")
        elif current_job is not None and (match := _STEP_RUN.match(line)):
            if pending_step is not None:
                current_steps.append(CIStep(pending_step, command=match.group(1).strip()))
                pending_step = None
            else:
                current_steps.append(CIStep("run", command=match.group(1).strip()))
        elif current_job is not None and (match := _STEP_USES.match(line)):
            if pending_step is not None:
                current_steps.append(CIStep(pending_step, action=match.group(1).strip()))
                pending_step = None
            else:
                current_steps.append(CIStep("uses", action=match.group(1).strip()))
    flush_job()
    return CIWorkflow(name, tuple(triggers), tuple(jobs))
