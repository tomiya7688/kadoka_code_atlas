"""Wire Operation input requirements into the Tk GUI without editing tk_app body.

Keeps analysis out of the presentation layer: only selection-state resolution.
"""

from __future__ import annotations

from Src.process.operation_requirements import (
    ALL_OPERATIONS,
    compatible_operations,
    resolve_operation_after_selection,
)


def _patched_select_file(self, index: int) -> None:
    self.current_file = self.files[index]
    language = self.service.detect_language(self.current_file)
    self.language_var.set(f"Language: {language}")
    has_project_folder = self.base_path is not None and self.base_path.is_dir()
    allowed = compatible_operations(
        language=language,
        has_project_folder=has_project_folder,
    )
    # Optional: when combobox is exposed as operation_combo, narrow choices.
    combo = getattr(self, "operation_combo", None)
    if combo is not None:
        combo.configure(values=allowed or ALL_OPERATIONS)
    resolved = resolve_operation_after_selection(
        self.operation_var.get(),
        language=language,
        has_project_folder=has_project_folder,
    )
    self.operation_var.set(resolved)


def apply() -> None:
    """Replace AtlasTkApp._select_file with the compatibility-aware implementation."""
    from .tk_app import AtlasTkApp

    AtlasTkApp._select_file = _patched_select_file  # type: ignore[method-assign]
