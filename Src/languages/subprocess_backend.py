"""Reusable host for versioned subprocess parser backends."""

from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

from Src.analyzers.ir import ModuleIR
from Src.data.backend_assets import resolve_backend_asset
from Src.languages.backend import (
    PARSER_BACKEND_CONTRACT_VERSION,
    ParserBackendDescriptor,
    ParserBackendError,
    ParserBackendFailure,
    ParserBackendFailureKind,
)
from Src.languages.common_ir_codec import module_ir_from_wire


class SubprocessParserBackend:
    """Run a bundled helper through Parser Backend Contract v1."""

    descriptor: ParserBackendDescriptor
    asset_path: str

    def __init__(
        self,
        *,
        app_root: Path | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._app_root = app_root
        self.timeout_seconds = timeout_seconds

    def parse(self, source: str, path: str | None = None) -> ModuleIR:
        return self._parse_with_context(source, path=path)

    def _parse_with_context(
        self,
        source: str,
        *,
        path: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> ModuleIR:
        request_id = uuid.uuid4().hex
        request: dict[str, Any] = {
            "contract_version": PARSER_BACKEND_CONTRACT_VERSION,
            "request_id": request_id,
            "operation": "parse",
            "language": self.descriptor.language,
            "source": source,
        }
        if path is not None:
            request["path"] = path
        if extra:
            request.update(extra)

        executable = resolve_backend_asset(self.asset_path, self._app_root)
        if not executable.is_file():
            raise ParserBackendError(
                ParserBackendFailure(
                    ParserBackendFailureKind.FAILURE,
                    f"Bundled parser backend is missing: {executable.name}",
                    self.descriptor.backend_id,
                )
            )

        try:
            completed = subprocess.run(
                [str(executable)],
                input=json.dumps(request, ensure_ascii=False),
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ParserBackendError(
                ParserBackendFailure(
                    ParserBackendFailureKind.TIMEOUT,
                    f"Parser backend timed out after {self.timeout_seconds:g} seconds.",
                    self.descriptor.backend_id,
                    retryable=True,
                )
            ) from error
        except OSError as error:
            raise ParserBackendError(
                ParserBackendFailure(
                    ParserBackendFailureKind.FAILURE,
                    str(error) or "Parser backend could not be started.",
                    self.descriptor.backend_id,
                )
            ) from error

        response = self._decode_response(completed.stdout, request_id)
        if completed.returncode != 0 and response.get("ok") is True:
            raise self._protocol_error("Backend returned success with a non-zero exit code.")

        if response["ok"] is False:
            error = response.get("error")
            if not isinstance(error, dict):
                raise self._protocol_error("Failure response is missing an error object.")
            try:
                kind = ParserBackendFailureKind(str(error["kind"]))
                backend_id = str(error["backend_id"])
                message = str(error["message"])
            except (KeyError, ValueError, TypeError) as exc:
                raise self._protocol_error("Failure response contains an invalid error.") from exc
            raise ParserBackendError(
                ParserBackendFailure(
                    kind,
                    message,
                    backend_id,
                    retryable=bool(error.get("retryable", False)),
                )
            )

        if "error" in response:
            raise self._protocol_error("Success response must not contain error.")
        if "ir" not in response:
            raise self._protocol_error("Success response is missing ir.")

        try:
            return module_ir_from_wire(response["ir"])
        except (KeyError, TypeError, ValueError) as error:
            raise self._protocol_error(f"Invalid Common IR payload: {error}") from error

    def _decode_response(self, stdout: str, request_id: str) -> dict[str, Any]:
        if not stdout.strip():
            raise self._protocol_error("Parser backend returned no protocol response.")
        try:
            response = json.loads(stdout)
        except json.JSONDecodeError as error:
            raise self._protocol_error("Parser backend returned invalid JSON.") from error
        if not isinstance(response, dict):
            raise self._protocol_error("Parser backend response must be an object.")
        if response.get("contract_version") != PARSER_BACKEND_CONTRACT_VERSION:
            raise self._protocol_error("Parser backend contract version mismatch.")
        if response.get("request_id") != request_id:
            raise self._protocol_error("Parser backend request_id mismatch.")
        if not isinstance(response.get("ok"), bool):
            raise self._protocol_error("Parser backend response is missing boolean ok.")
        return response

    def _protocol_error(self, message: str) -> ParserBackendError:
        return ParserBackendError(
            ParserBackendFailure(
                ParserBackendFailureKind.PROTOCOL_ERROR,
                message,
                self.descriptor.backend_id,
            )
        )
