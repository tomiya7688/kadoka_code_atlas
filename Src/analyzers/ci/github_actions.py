"""Conservative GitHub Actions workflow analyzer."""

from __future__ import annotations

from collections.abc import Mapping

import yaml

from Src.models.ci import CIJob, CIStep, CIWorkflow


def _as_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _trigger_value(document: Mapping[object, object]) -> object:
    """Return the workflow trigger value, including PyYAML's YAML 1.1 `on` quirk."""
    if "on" in document:
        return document["on"]
    # PyYAML's SafeLoader treats the plain scalar `on` as boolean true.
    if True in document:
        return document[True]
    return None


def _normalize_triggers(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str))
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value if isinstance(key, str))
    return ()


def _normalize_needs(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str))
    return ()


def _normalize_steps(value: object) -> tuple[CIStep, ...]:
    if not isinstance(value, list):
        return ()

    steps: list[CIStep] = []
    for raw_step in value:
        if not isinstance(raw_step, Mapping):
            continue
        command = _as_string(raw_step.get("run"))
        action = _as_string(raw_step.get("uses"))
        explicit_name = _as_string(raw_step.get("name"))
        if explicit_name is not None:
            name = explicit_name
        elif command is not None:
            name = "run"
        elif action is not None:
            name = "uses"
        else:
            # Unknown step shapes are intentionally ignored instead of inventing data.
            continue
        steps.append(CIStep(name, command=command, action=action))
    return tuple(steps)


def parse_github_actions(source: str) -> CIWorkflow:
    """Parse GitHub Actions YAML without evaluating expressions or shell code."""
    document = yaml.safe_load(source)
    if document is None:
        document = {}
    if not isinstance(document, Mapping):
        raise ValueError("GitHub Actions workflow root must be a mapping")

    name = _as_string(document.get("name"))
    triggers = _normalize_triggers(_trigger_value(document))
    raw_jobs = document.get("jobs")
    if raw_jobs is None:
        return CIWorkflow(name, triggers, ())
    if not isinstance(raw_jobs, Mapping):
        raise ValueError("GitHub Actions jobs must be a mapping")

    jobs: list[CIJob] = []
    for raw_name, raw_job in raw_jobs.items():
        if not isinstance(raw_name, str) or not isinstance(raw_job, Mapping):
            continue
        jobs.append(
            CIJob(
                raw_name,
                _normalize_needs(raw_job.get("needs")),
                _normalize_steps(raw_job.get("steps")),
            )
        )
    return CIWorkflow(name, triggers, tuple(jobs))
