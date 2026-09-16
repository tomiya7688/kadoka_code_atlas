from pathlib import Path

import pytest

from Src.generators.output_names import stable_output_name
from Src.process.application import ApplicationService, DiagramSetResult, GeneratedOutput


def test_stable_output_name_is_deterministic_and_collision_resistant() -> None:
    dotted = stable_output_name("series_1", "A.b")
    underscored = stable_output_name("series_1", "A_b")

    assert dotted == stable_output_name("series_1", "A.b")
    assert dotted != underscored
    assert dotted.startswith("series_1_")
    assert dotted.endswith("_A.b")
    assert underscored.endswith("_A_b")
    assert "/" not in stable_output_name("series_1", "A/b")
    assert "\\" not in stable_output_name("series_1", "A\\b")


def test_save_diagram_set_rejects_duplicate_paths(tmp_path: Path) -> None:
    result = DiagramSetResult(
        outputs=(
            GeneratedOutput("same", "first", "mermaid"),
            GeneratedOutput("same", "second", "mermaid"),
        ),
        statistics={},
    )

    with pytest.raises(ValueError, match="Duplicate generated output path"):
        ApplicationService().save_diagram_set(
            tmp_path,
            result,
            category="class_diagrams",
        )


def test_generated_output_names_are_safe_for_windows_case_insensitive_paths() -> None:
    upper = stable_output_name("series", "Service")
    lower = stable_output_name("series", "service")

    assert upper.casefold() != lower.casefold()
