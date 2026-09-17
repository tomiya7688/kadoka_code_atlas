"""GitHub Actions implementation of the provider-neutral CI adapter contract."""

from __future__ import annotations

from Src.models.ci import CIWorkflow

from .github_actions import parse_github_actions


class GitHubActionsAdapter:
    provider_id = "github-actions"

    def parse(self, source: str) -> CIWorkflow:
        return parse_github_actions(source)
