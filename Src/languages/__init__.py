"""Language-specific parsing adapters and backend contracts."""

from .backend import (
    PARSER_BACKEND_CONTRACT_VERSION,
    ParserBackend,
    ParserBackendDescriptor,
    ParserBackendError,
    ParserBackendFailure,
    ParserBackendFailureKind,
    ParserBackendKind,
    normalize_backend_exception,
)
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
    "PARSER_BACKEND_CONTRACT_VERSION",
    "ParserBackend",
    "ParserBackendDescriptor",
    "ParserBackendError",
    "ParserBackendFailure",
    "ParserBackendFailureKind",
    "ParserBackendKind",
    "PythonAdapter",
    "PythonLanguageAdapter",
    "normalize_backend_exception",
]
