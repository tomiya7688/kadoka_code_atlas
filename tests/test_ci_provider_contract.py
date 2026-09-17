from __future__ import annotations

import ast
from dataclasses import asdict
import json
from pathlib import Path

from Src.analyzers.ci import CIProviderAdapter, GitHubActionsAdapter
from Src.models.ci import CIWorkflow


FIXTURE_ROOT = Path("tests/fixtures/ci")


def _json_shape(value: object) -> object:
    return json.loads(json.dumps(value))


def test_github_actions_adapter_satisfies_provider_contract() -> None:
    adapter = GitHubActionsAdapter()

    assert isinstance(adapter, CIProviderAdapter)
    assert adapter.provider_id == "github-actions"
    assert isinstance(adapter.parse("jobs: {}\n"), CIWorkflow)


def test_normalized_ci_contract_matches_golden_fixture() -> None:
    source = (FIXTURE_ROOT / "github_actions_contract.yml").read_text(encoding="utf-8")
    expected = json.loads(
        (FIXTURE_ROOT / "normalized_contract_v1.json").read_text(encoding="utf-8")
    )

    workflow = GitHubActionsAdapter().parse(source)

    assert _json_shape(asdict(workflow)) == expected


def test_renderer_and_evaluator_do_not_import_provider_implementations() -> None:
    forbidden = {
        "Src.analyzers.ci.github_actions",
        "Src.analyzers.ci.github_actions_adapter",
    }
    violations: list[str] = []

    for root in (Path("Src/renderers"), Path("Src/evaluators")):
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = {alias.name for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    modules = {node.module or ""}
                else:
                    continue
                if modules & forbidden:
                    violations.append(str(path))

    assert violations == []
