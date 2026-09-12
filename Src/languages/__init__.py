"""Language-specific parsing adapters."""

from .base import LanguageAdapter
from .csharp import CSharpAdapter
from .cpp import CppAdapter
from .gdscript import GDScriptAdapter
from .go import GoAdapter
from .java import JavaAdapter
from .python import PythonLanguageAdapter
from .python_comments_adapter import PythonAdapter

__all__ = [
    "CSharpAdapter",
    "CppAdapter",
    "GDScriptAdapter",
    "GoAdapter",
    "JavaAdapter",
    "LanguageAdapter",
    "PythonAdapter",
    "PythonLanguageAdapter",
]
