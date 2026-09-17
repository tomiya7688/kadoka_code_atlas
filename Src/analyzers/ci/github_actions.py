"""Conservative GitHub Actions workflow analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
import re

import yaml

from Src.models.ci import (
    CIJob,
    CIMatrix,
    CIMatrixAxis,
    CIPrimitive,
    CIResourceOperation,
    CIStep,
    CIStrategy,
    CIWorkflow,
)


_TOKEN_PATTERN = re.compile(r'''"[^"]*"|'[^']*'|\S+''')
_SECRET_PATTERNS = (
    re.compile(r"\bsecrets\.([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bsecrets\[['\"]([^'\"]+)['\"]\]"),
)
_ENV_PATTERNS = (
    re.compile(r"\benv\.([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\benv\[['\"]([^'\"]+)['\"]\]"),
)
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


def _as_mapping(value: object) -> Mapping[object, object] | None:
    return value if isinstance(value, Mapping) else None


def _normalize_conditional(value: object) -> str | bool | None:
    if isinstance(value, bool):
        return value
    return value if isinstance(value, str) else None


def _normalize_int_or_expression(value: object) -> str | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return value if isinstance(value, str) else None


def _is_primitive(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


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


def _env_names(value: object) -> tuple[str, ...]:
    if not isinstance(value, Mapping):
        return ()
    return tuple(key for key in value if isinstance(key, str))


def _collect_references(value: object, patterns: tuple[re.Pattern[str], ...]) -> tuple[str, ...]:
    found: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, str):
            for pattern in patterns:
                found.update(pattern.findall(item))
        elif isinstance(item, Mapping):
            for nested in item.values():
                visit(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                visit(nested)

    visit(value)
    return tuple(sorted(found))


def _without_key(mapping: Mapping[object, object], excluded: str) -> dict[object, object]:
    return {key: value for key, value in mapping.items() if key != excluded}


def _normalize_matrix_row(value: object) -> tuple[tuple[str, CIPrimitive], ...] | None:
    if not isinstance(value, Mapping):
        return None
    entries: list[tuple[str, CIPrimitive]] = []
    for key, item in value.items():
        if isinstance(key, str) and _is_primitive(item):
            entries.append((key, item))
    return tuple(entries)


def _normalize_matrix_rows(value: object) -> tuple[tuple[tuple[str, CIPrimitive], ...], ...]:
    if not isinstance(value, list):
        return ()
    rows: list[tuple[tuple[str, CIPrimitive], ...]] = []
    for item in value:
        row = _normalize_matrix_row(item)
        if row is not None:
            rows.append(row)
    return tuple(rows)


def _normalize_matrix(value: object) -> CIMatrix | None:
    if isinstance(value, str):
        return CIMatrix(expression=value)
    if not isinstance(value, Mapping):
        return None

    axes: list[CIMatrixAxis] = []
    for key, raw_values in value.items():
        if not isinstance(key, str) or key in {"include", "exclude"}:
            continue
        if not isinstance(raw_values, list):
            continue
        values = tuple(item for item in raw_values if _is_primitive(item))
        axes.append(CIMatrixAxis(key, values))

    return CIMatrix(
        axes=tuple(axes),
        include=_normalize_matrix_rows(value.get("include")),
        exclude=_normalize_matrix_rows(value.get("exclude")),
    )


def _normalize_strategy(value: object) -> CIStrategy | None:
    if not isinstance(value, Mapping):
        return None
    matrix = _normalize_matrix(value.get("matrix"))
    fail_fast = _normalize_conditional(value.get("fail-fast"))
    max_parallel = _normalize_int_or_expression(value.get("max-parallel"))
    if matrix is None and fail_fast is None and max_parallel is None:
        return None
    return CIStrategy(matrix, fail_fast, max_parallel)


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


def _normalize_resource_paths(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(line.strip() for line in value.splitlines() if line.strip())
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str) and item.strip())
    return ()


def _resource_operations(action: str | None, raw_with: object) -> tuple[CIResourceOperation, ...]:
    if not action:
        return ()
    with_values = _as_mapping(raw_with) or {}
    action_id = action.casefold().split("@", 1)[0]
    paths = _normalize_resource_paths(with_values.get("path"))

    if action_id in {"actions/cache", "actions/cache/restore", "actions/cache/save"}:
        kind = {
            "actions/cache": "cache",
            "actions/cache/restore": "cache-restore",
            "actions/cache/save": "cache-save",
        }[action_id]
        return (
            CIResourceOperation(
                kind=kind,
                paths=paths,
                key=_as_string(with_values.get("key")),
            ),
        )

    if action_id in {"actions/upload-artifact", "actions/download-artifact"}:
        kind = "artifact-upload" if action_id.endswith("upload-artifact") else "artifact-download"
        return (
            CIResourceOperation(
                kind=kind,
                name=_as_string(with_values.get("name")),
                paths=paths,
            ),
        )
    return ()


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
                condition=_as_string(raw_step.get("if")),
                continue_on_error=_normalize_conditional(raw_step.get("continue-on-error")),
                timeout_minutes=_normalize_int_or_expression(raw_step.get("timeout-minutes")),
                env_names=_env_names(raw_step.get("env")),
                env_refs=_collect_references(raw_step, _ENV_PATTERNS),
                secret_refs=_collect_references(raw_step, _SECRET_PATTERNS),
                resources=_resource_operations(action, raw_step.get("with")),
                retry=None,
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
        raw_jobs = {}
    if not isinstance(raw_jobs, Mapping):
        raise ValueError("GitHub Actions jobs must be a mapping")

    jobs: list[CIJob] = []
    for raw_name, raw_job in raw_jobs.items():
        if not isinstance(raw_name, str) or not isinstance(raw_job, Mapping):
            continue
        job_context = _without_key(raw_job, "steps")
        jobs.append(
            CIJob(
                raw_name,
                _normalize_needs(raw_job.get("needs")),
                _normalize_steps(
                    raw_job.get("steps"),
                    default_working_directory=_working_directory(raw_job.get("defaults")),
                ),
                display_name=_as_string(raw_job.get("name")),
                condition=_as_string(raw_job.get("if")),
                continue_on_error=_normalize_conditional(raw_job.get("continue-on-error")),
                timeout_minutes=_normalize_int_or_expression(raw_job.get("timeout-minutes")),
                env_names=_env_names(raw_job.get("env")),
                env_refs=_collect_references(job_context, _ENV_PATTERNS),
                secret_refs=_collect_references(job_context, _SECRET_PATTERNS),
                strategy=_normalize_strategy(raw_job.get("strategy")),
                retry=None,
            )
        )

    workflow_context = _without_key(document, "jobs")
    return CIWorkflow(
        name,
        triggers,
        tuple(jobs),
        env_names=_env_names(document.get("env")),
        env_refs=_collect_references(workflow_context, _ENV_PATTERNS),
        secret_refs=_collect_references(workflow_context, _SECRET_PATTERNS),
    )
