"""Presentation-layer user interfaces."""

from .tk_app import launch_gui
from .operation_compat import apply as _apply_operation_compat

_apply_operation_compat()

__all__ = ["launch_gui"]
