"""Mermaid renderer for logical CI workflow models."""

from __future__ import annotations

import re

from Src.models.ci import CIWorkflow


def _node_id(name: str) -> str:
    return "ci_" + re.sub(r"[^0-9A-Za-z_]", "_", name)


def _label(job_name: str, steps: tuple[str, ...]) -> str:
    if not steps:
        return job_name
    return job_name + "<br/>" + "<br/>".join(steps)


def render_ci_workflow(workflow: CIWorkflow, direction: str = "LR") -> str:
    """Render jobs and ``needs`` edges without inspecting CI syntax."""
    lines = [f"flowchart {direction}"]
    trigger = ", ".join(workflow.trigger) if workflow.trigger else "workflow"
    lines.append(f'    ci_trigger["{trigger}"]')
    for job in workflow.jobs:
        steps = tuple(step.name for step in job.steps)
        lines.append(f'    {_node_id(job.name)}["{_label(job.name, steps)}"]')
    known = {job.name for job in workflow.jobs}
    for job in workflow.jobs:
        dependencies = tuple(item for item in job.needs if item in known)
        if dependencies:
            for dependency in dependencies:
                lines.append(f"    {_node_id(dependency)} --> {_node_id(job.name)}")
        else:
            lines.append(f"    ci_trigger --> {_node_id(job.name)}")
    return "\n".join(lines) + "\n"
