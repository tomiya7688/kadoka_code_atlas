"""Language adapters for extracting comment candidates."""

from .base import LanguageAdapter
from .python import PythonAdapter

__all__ = ["LanguageAdapter", "PythonAdapter"]
