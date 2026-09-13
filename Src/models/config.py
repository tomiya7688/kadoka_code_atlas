"""Portable, JSON-shaped generation configuration data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AtlasConfig:
    input: str = "."
    output_dir: str = "output"
    disabled_generators: tuple[str, ...] = ()
    disabled_evaluators: tuple[str, ...] = ()
    renderer: str = "mermaid"
    generator_options: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AtlasConfig":
        def strings(name: str) -> tuple[str, ...]:
            raw = value.get(name, [])
            if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
                raise ValueError(f"{name} must be an array of strings")
            return tuple(raw)

        options = value.get("generator_options", {})
        if not isinstance(options, dict) or not all(isinstance(item, dict) for item in options.values()):
            raise ValueError("generator_options must be an object of objects")
        input_path = value.get("input", ".")
        output_dir = value.get("output_dir", "output")
        renderer = value.get("renderer", "mermaid")
        if not all(isinstance(item, str) for item in (input_path, output_dir, renderer)):
            raise ValueError("input, output_dir, and renderer must be strings")
        return cls(input_path, output_dir, strings("disabled_generators"), strings("disabled_evaluators"), renderer, options)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "output_dir": self.output_dir,
            "disabled_generators": list(self.disabled_generators),
            "disabled_evaluators": list(self.disabled_evaluators),
            "renderer": self.renderer,
            "generator_options": self.generator_options,
        }
