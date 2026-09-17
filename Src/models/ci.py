"""Language-neutral CI workflow models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias


CIPrimitive: TypeAlias = str | int | float | bool | None
CIConditionalValue: TypeAlias = str | bool | None
CITimeoutValue: TypeAlias = str | int | None


@dataclass(frozen=True, slots=True)
class CIMatrixAxis:
    name: str
    values: tuple[CIPrimitive, ...] = ()


@dataclass(frozen=True, slots=True)
class CIMatrix:
    axes: tuple[CIMatrixAxis, ...] = ()
    include: tuple[tuple[tuple[str, CIPrimitive], ...], ...] = ()
    exclude: tuple[tuple[tuple[str, CIPrimitive], ...], ...] = ()
    expression: str | None = None


@dataclass(frozen=True, slots=True)
class CIStrategy:
    matrix: CIMatrix | None = None
    fail_fast: CIConditionalValue = None
    max_parallel: str | int | None = None


@dataclass(frozen=True, slots=True)
class CIRetryPolicy:
    """Provider-neutral retry information when a provider exposes it explicitly."""

    max_attempts: str | int | None = None
    delay_seconds: str | int | None = None


@dataclass(frozen=True, slots=True)
class CIResourceOperation:
    """Normalized cache/artifact operation extracted from one CI step."""

    kind: str
    name: str | None = None
    paths: tuple[str, ...] = ()
    key: str | None = None


@dataclass(frozen=True, slots=True)
class CIStep:
    name: str
    command: str | None = None
    action: str | None = None
    path_hints: tuple[str, ...] = ()
    condition: str | None = None
    continue_on_error: CIConditionalValue = None
    timeout_minutes: CITimeoutValue = None
    env_names: tuple[str, ...] = ()
    env_refs: tuple[str, ...] = ()
    secret_refs: tuple[str, ...] = ()
    resources: tuple[CIResourceOperation, ...] = ()
    retry: CIRetryPolicy | None = None


@dataclass(frozen=True, slots=True)
class CIPathHint:
    job: str
    step: str
    path: str


@dataclass(frozen=True, slots=True)
class CIJob:
    name: str
    needs: tuple[str, ...] = ()
    steps: tuple[CIStep, ...] = ()
    display_name: str | None = None
    condition: str | None = None
    continue_on_error: CIConditionalValue = None
    timeout_minutes: CITimeoutValue = None
    env_names: tuple[str, ...] = ()
    env_refs: tuple[str, ...] = ()
    secret_refs: tuple[str, ...] = ()
    strategy: CIStrategy | None = None
    retry: CIRetryPolicy | None = None


@dataclass(frozen=True, slots=True)
class CIWorkflow:
    name: str | None
    trigger: tuple[str, ...]
    jobs: tuple[CIJob, ...] = field(default_factory=tuple)
    env_names: tuple[str, ...] = ()
    env_refs: tuple[str, ...] = ()
    secret_refs: tuple[str, ...] = ()
