"""Bundled Go parser/type-checker helper backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from Src.analyzers.ir import ModuleIR
from Src.languages.backend import (
    ParserBackendDescriptor,
    ParserBackendKind,
)
from Src.languages.subprocess_backend import SubprocessParserBackend


@dataclass(frozen=True, slots=True)
class GoProjectSource:
    """One project-local Go package source supplied as semantic context."""

    import_path: str
    path: str
    source: str


class GoStdlibBackend(SubprocessParserBackend):
    """Primary Go backend selected by issue #137."""

    descriptor = ParserBackendDescriptor(
        backend_id="go-stdlib-types-helper",
        language="go",
        kind=ParserBackendKind.HELPER,
    )
    asset_path = (
        "go/kadoka-go-backend.exe"
        if os.name == "nt"
        else "go/kadoka-go-backend"
    )

    def parse_project(
        self,
        source: str,
        *,
        path: str | None = None,
        project_sources: tuple[GoProjectSource, ...] = (),
    ) -> ModuleIR:
        return self._parse_with_context(
            source,
            path=path,
            extra={
                "project_sources": [
                    {
                        "import_path": item.import_path,
                        "path": item.path,
                        "source": item.source,
                    }
                    for item in project_sources
                ]
            },
        )
