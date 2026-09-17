"""Bridge normalized CI steps to later source/project analysis without resolving files here."""

from __future__ import annotations

from Src.models.ci import CIPathHint, CIWorkflow


def collect_ci_path_hints(workflow: CIWorkflow) -> tuple[CIPathHint, ...]:
    """Collect conservative path hints while preserving job/step provenance.

    This function deliberately does not touch the filesystem. Project discovery and
    language adapters remain responsible for deciding whether a hint resolves to an
    actual source, test, script, project file, or directory.
    """

    hints: list[CIPathHint] = []
    seen: set[tuple[str, str, str]] = set()
    for job in workflow.jobs:
        for step in job.steps:
            for path in step.path_hints:
                key = (job.name, step.name, path)
                if key in seen:
                    continue
                seen.add(key)
                hints.append(CIPathHint(job.name, step.name, path))
    return tuple(hints)
