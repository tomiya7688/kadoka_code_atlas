from Src.languages.backend import (
    PARSER_BACKEND_CONTRACT_VERSION,
    ParserBackendDescriptor,
    ParserBackendError,
    ParserBackendFailure,
    ParserBackendFailureKind,
    ParserBackendKind,
    normalize_backend_exception,
)


def test_parser_backend_contract_version_is_stable_v1() -> None:
    descriptor = ParserBackendDescriptor(
        backend_id="python-stdlib",
        language="python",
        kind=ParserBackendKind.IN_PROCESS,
    )

    assert PARSER_BACKEND_CONTRACT_VERSION == "1"
    assert descriptor.contract_version == "1"


def test_parser_backend_failure_kinds_match_wire_contract() -> None:
    assert {item.value for item in ParserBackendFailureKind} == {
        "failure",
        "timeout",
        "unsupported_syntax",
        "unsupported_language",
        "protocol_error",
    }


def test_timeout_is_normalized_at_backend_boundary() -> None:
    descriptor = ParserBackendDescriptor(
        backend_id="helper-python",
        language="python",
        kind=ParserBackendKind.SUBPROCESS,
    )

    error = normalize_backend_exception(descriptor, TimeoutError("deadline exceeded"))

    assert isinstance(error, ParserBackendError)
    assert error.failure.kind is ParserBackendFailureKind.TIMEOUT
    assert error.failure.backend_id == "helper-python"
    assert error.failure.retryable is True
    assert str(error) == "deadline exceeded"


def test_unknown_backend_exception_is_normalized_without_leaking_type() -> None:
    descriptor = ParserBackendDescriptor(
        backend_id="native-cpp",
        language="cpp",
        kind=ParserBackendKind.NATIVE,
    )

    error = normalize_backend_exception(descriptor, ValueError("native parser failed"))

    assert type(error) is ParserBackendError
    assert error.failure == ParserBackendFailure(
        kind=ParserBackendFailureKind.FAILURE,
        message="native parser failed",
        backend_id="native-cpp",
        retryable=False,
    )


def test_already_normalized_backend_error_is_preserved() -> None:
    descriptor = ParserBackendDescriptor(
        backend_id="java-helper",
        language="java",
        kind=ParserBackendKind.HELPER,
    )
    original = ParserBackendError(
        ParserBackendFailure(
            ParserBackendFailureKind.UNSUPPORTED_SYNTAX,
            "preview syntax is not supported",
            descriptor.backend_id,
        )
    )

    assert normalize_backend_exception(descriptor, original) is original
