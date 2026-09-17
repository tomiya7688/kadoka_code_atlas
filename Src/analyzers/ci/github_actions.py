"""Conservative GitHub Actions workflow analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
import re

import yaml

from Src.models.ci import CIJob, CIStep, CIWorkflow


_TOKEN_PATTERN = re.compile(r'''"[^"]*"|'[^']*'|\S+''')
_PATH_SUFFIXES = {
    ".py",
    ".pyi",
    ".cs",
    ".csproj",
    ".sln",
    ".cpp",
    ".cc",
    ".cxx",
    ".c",
    ".h",
    ".hpp",
    ".hxx",
    ".gd",
    ".java",
    ".go",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".sh",
    ".bat",
    ".ps1",
}
_COMMON_PROJECT_PATHS = {
    "src",
    "source",
    "test",
    "tests",
    "app",
    "apps",
    "lib",
    "libs",
    "script",
    "scripts",
    "tool",
    "tools",
}


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


def _clean_path_text(value: str) -> str | None:
    token = value.strip().strip("\"'").strip("(),;")
    if not token or token.startswith(("-", "$", "${{")) or "://" in token:
        return None
    token = token.replace("\\", "/")
    if token.startswith("./"):
        token = token[2:]
    return token.rstrip("/") or "."


def _normalize_explicit_path(value: str) -> str | None:
    """Accept an explicitly configured working/local-action path conservatively."""
    return _clean_path_text(value)


def _normalize_path_hint(value: str) -> str | None:
    raw = value.strip().strip("\"'").strip("(),;")
    explicit_relative = raw.startswith(("./", "../"))
    token = _clean_path_text(value)
    if token is None:
        return None
    lowered = token.casefold()
    suffix = PurePosixPath(token).suffix.casefold()
    is_common_directory = lowered in _COMMON_PROJECT_PATHS
    is_nested_path = "/" in token and ":" not in token
    is_known_file = suffix in _PATH_SUFFIXES
    is_glob = any(marker in token for marker in ("*", "?", "["))
    if (
        token == "."
        or explicit_relative
        or is_common_directory
        or is_nested_path
        or is_known_file
        or is_glob
    ):
        return token
    return None


def _command_path_hints(command: str | None) -> tuple[str, ...]:
    if not command:
        return ()
    hints: list[str] = []
    for raw_token in _TOKEN_PATTERN.findall(command):
        hint = _normalize_path_hint(raw_token)
        if hint is not None and hint not in hints:
            hints.append(hint)
    return tuple(hints)


def _working_directory(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    run_defaults = value.get("run")
    if not isinstance(run_defaults, Mapping):
        return None
    return _as_string(run_defaults.get("working-directory"))


def _step_path_hints(
    raw_step: Mapping[object, object],
    command: str | None,
    action: str | None,
    default_working_directory: str | None,
) -> tuple[str, ...]:
    hints: list[str] = []
    working_directory = _as_string(raw_step.get("working-directory")) or default_working_directory
    if working_directory:
        normalized = _normalize_explicit_path(working_directory)
        if normalized is not None:
            hints.append(normalized)
    if action and action.startswith("./"):
        normalized = _normalize_explicit_path(action)
        if normalized is not None and normalized not in hints:
            hints.append(normalized)
    for hint in _command_path_hints(command):
        if hint not in hints:
            hints.append(hint)
    return tuple(hints)


def _normalize_steps(
    value: object,
    *,
    default_working_directory: str | None = None,
) -> tuple[CIStep, ...]:
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
        steps.append(
            CIStep(
                name,
                command=command,
                action=action,
                path_hints=_step_path_hints(
                    raw_step,
                    command,
                    action,
                    default_working_directory,
                ),
            )
        )
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
                _normalize_steps(
                    raw_job.get("steps"),
                    default_working_directory=_working_directory(raw_job.get("defaults")),
                ),
            )
        )
    return CIWorkflow(name, triggers, tuple(jobs))
