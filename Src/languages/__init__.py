"""Language-specific parsing adapters."""

from .base import LanguageAdapter
from .csharp import CSharpAdapter
from .gdscript import GDScriptAdapter
from .python import PythonLanguageAdapter
from .python_comments_adapter import PythonAdapter

__all__ = [
    "CSharpAdapter",
    "GDScriptAdapter",
    "LanguageAdapter",
    "PythonAdapter",
    "PythonLanguageAdapter",
]
