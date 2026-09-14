import json

import pytest

from Src.models.config import AtlasConfig
from Src.process.application import ApplicationService
from Src.process.config_service import ConfigError, load_config, resolve_config


def test_missing_config_enables_all_default_capabilities() -> None:
    resolved = resolve_config(AtlasConfig())
    assert "activity_diagram" in resolved.generators
    assert "class_diagram" in resolved.generators
    assert "sequence_diagram" in resolved.generators
    assert "communication_diagram" in resolved.generators
    assert "ci_quality" in resolved.evaluators


def test_config_excludes_capabilities_and_cli_overrides() -> None:
    config = AtlasConfig(disabled_generators=("activity_diagram",), renderer="mermaid")
    resolved = resolve_config(config, cli_disabled_generators=("ci",))
    assert "activity_diagram" not in resolved.generators
    assert "ci" not in resolved.generators


def test_unknown_capability_and_incompatible_renderer_are_rejected() -> None:
    with pytest.raises(ConfigError, match="unknown capability"):
        resolve_config(AtlasConfig(disabled_generators=("missing",)))
    with pytest.raises(ConfigError, match="not supported"):
        resolve_config(AtlasConfig(renderer="plantuml"))


def test_json_config_round_trip(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "disabled_generators": ["ci"],
                "renderer": "mermaid",
                "generator_options": {
                    "sequence_diagram": {
                        "show_duplicate_calls": False,
                        "show_returns": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.disabled_generators == ("ci",)
    assert config.to_dict()["renderer"] == "mermaid"
    assert ApplicationService(config).sequence_diagram_settings() == {
        "show_duplicate_calls": False,
        "show_returns": True,
    }
