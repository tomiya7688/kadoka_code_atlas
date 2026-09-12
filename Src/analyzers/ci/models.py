"""Language-neutral CI workflow models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CIStep:
    name: str
    command: str | None = None
    action: str | None = None


@dataclass(frozen=True, slots=True)
class CIJob:
    name: str
    needs: tuple[str, ...] = ()
    steps: tuple[CIStep, ...] = ()


@dataclass(frozen=True, slots=True)
class CIWorkflow:
    name: str | None
    trigger: tuple[str, ...]
    jobs: tuple[CIJob, ...] = field(default_factory=tuple)
