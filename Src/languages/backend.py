"""Versioned contracts for swappable parser backends inside language adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from Src.analyzers.ir import ModuleIR


PARSER_BACKEND_CONTRACT_VERSION = "1"


class ParserBackendKind(str, Enum):
    """How a parser backend is hosted behind the language-adapter boundary."""

    IN_PROCESS = "in_process"
    SUBPROCESS = "subprocess"
    NATIVE = "native"
    HELPER = "helper"


class ParserBackendFailureKind(str, Enum):
    """Stable error categories exposed by parser backends."""

    FAILURE = "failure"
    TIMEOUT = "timeout"
    UNSUPPORTED_SYNTAX = "unsupported_syntax"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    PROTOCOL_ERROR = "protocol_error"


@dataclass(frozen=True, slots=True)
class ParserBackendDescriptor:
    """Passive identity and compatibility metadata for one backend."""

    backend_id: str
    language: str
    kind: ParserBackendKind
    contract_version: str = PARSER_BACKEND_CONTRACT_VERSION


@dataclass(frozen=True, slots=True)
class ParserBackendFailure:
    """Normalized backend failure with no backend-library-specific exception type."""

    kind: ParserBackendFailureKind
    message: str
    backend_id: str
    retryable: bool = False


class ParserBackendError(RuntimeError):
    """Boundary exception carrying one normalized backend failure."""

    def __init__(self, failure: ParserBackendFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure


class ParserBackend(Protocol):
    """Produce Common IR without exposing parser/backend-specific types."""

    descriptor: ParserBackendDescriptor

    def parse(self, source: str, path: str | None = None) -> ModuleIR:
        """Return Common IR or raise ParserBackendError with a normalized failure."""


def normalize_backend_exception(
    descriptor: ParserBackendDescriptor,
    error: BaseException,
) -> ParserBackendError:
    """Convert generic host failures at the backend boundary into stable categories."""

    if isinstance(error, ParserBackendError):
        return error
    if isinstance(error, TimeoutError):
        failure = ParserBackendFailure(
            ParserBackendFailureKind.TIMEOUT,
            str(error) or "Parser backend timed out.",
            descriptor.backend_id,
            retryable=True,
        )
    else:
        failure = ParserBackendFailure(
            ParserBackendFailureKind.FAILURE,
            str(error) or error.__class__.__name__,
            descriptor.backend_id,
        )
    return ParserBackendError(failure)
