"""Language adapters for extracting comment candidates."""

from .base import LanguageAdapter
from .csharp import CSharpAdapter
from .gdscript import GDScriptAdapter
from .python import PythonAdapter

__all__ = ["CSharpAdapter", "GDScriptAdapter", "LanguageAdapter", "PythonAdapter"]
