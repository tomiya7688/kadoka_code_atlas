"""Config loading and capability-based selection for application services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from Src.models.config import AtlasConfig


class ConfigError(ValueError):
    """Raised when a config references an unavailable capability."""


@dataclass(frozen=True, slots=True)
class Capability:
    id: str
    category: str
    renderers: tuple[str, ...] = ("mermaid",)
    default_enabled: bool = True


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    config: AtlasConfig
    generators: tuple[str, ...]
    evaluators: tuple[str, ...]


def default_capabilities() -> tuple[Capability, ...]:
    return (
        Capability("comment", "generator", ()),
        Capability("call_graph", "generator"),
        Capability("class_diagram", "generator"),
        Capability("object_diagram", "generator"),
        Capability("sequence_diagram", "generator"),
        Capability("communication_diagram", "generator"),
        Capability("activity_diagram", "generator"),
        Capability("ci", "generator"),
        Capability("responsibility", "generator", ()),
        Capability("ci_quality", "evaluator", ()),
        Capability("design_quality", "evaluator", ()),
    )


def load_config(path: Path | None = None) -> AtlasConfig:
    if path is None or not path.exists():
        return AtlasConfig()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"invalid JSON: {error.msg}") from error
    if not isinstance(value, dict):
        raise ConfigError("config root must be an object")
    try:
        return AtlasConfig.from_dict(value)
    except ValueError as error:
        raise ConfigError(str(error)) from error


def resolve_config(
    config: AtlasConfig,
    *,
    capabilities: tuple[Capability, ...] | None = None,
    cli_disabled_generators: tuple[str, ...] = (),
    renderer_override: str | None = None,
) -> ResolvedConfig:
    available = capabilities or default_capabilities()
    disabled_generators = set(config.disabled_generators) | set(cli_disabled_generators)
    unknown = disabled_generators - {item.id for item in available if item.category == "generator"}
    unknown |= set(config.disabled_evaluators) - {item.id for item in available if item.category == "evaluator"}
    if unknown:
        raise ConfigError(f"unknown capability: {', '.join(sorted(unknown))}")
    renderer = renderer_override or config.renderer
    enabled_generators = tuple(
        item.id for item in available
        if item.category == "generator" and item.default_enabled and item.id not in disabled_generators
    )
    enabled_evaluators = tuple(
        item.id for item in available
        if item.category == "evaluator" and item.default_enabled and item.id not in set(config.disabled_evaluators)
    )
    incompatible = [
        item.id for item in available
        if item.id in enabled_generators and item.renderers and renderer not in item.renderers
    ]
    if incompatible:
        raise ConfigError(f"renderer '{renderer}' is not supported by: {', '.join(incompatible)}")
    resolved = AtlasConfig(
        config.input,
        config.output_dir,
        tuple(sorted(disabled_generators)),
        config.disabled_evaluators,
        renderer,
        config.generator_options,
    )
    return ResolvedConfig(resolved, enabled_generators, enabled_evaluators)
