"""Language adapters for extracting comment candidates."""

from .base import LanguageAdapter
from .csharp import CSharpAdapter
from .python import PythonAdapter

__all__ = ["CSharpAdapter", "LanguageAdapter", "PythonAdapter"]
