"""Exercise the Roslyn helper directly against the shared C# fixture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


FIXTURE = Path("tests/fixtures/backend_conformance/csharp.cs")


def main(argv: list[str] | None = None) -> int:
    command = list(sys.argv[1:] if argv is None else argv)
    if not command:
        raise SystemExit("usage: csharp_backend_smoke.py <helper command...>")

    request = {
        "contract_version": "1",
        "request_id": "csharp-ci-smoke",
        "operation": "parse",
        "language": "csharp",
        "source": FIXTURE.read_text(encoding="utf-8"),
        "path": str(FIXTURE),
    }
    completed = subprocess.run(
        command,
        input=json.dumps(request),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode

    response = json.loads(completed.stdout)
    assert response["contract_version"] == "1"
    assert response["request_id"] == "csharp-ci-smoke"
    assert response["ok"] is True
    module = response["ir"]
    entities = module["entities"]

    worker = next(
        entity
        for entity in entities
        if entity["kind"] == "class" and entity["name"] == "Worker"
    )
    interface = next(
        entity
        for entity in entities
        if entity["kind"] == "class" and entity["name"] == "IWorker"
    )
    runs = [
        entity
        for entity in entities
        if entity["kind"] == "method"
        and entity["name"] == "run"
        and entity.get("parent") == "Worker"
    ]
    one_arg_run = next(entity for entity in runs if len(entity["parameters"]) == 1)

    assert worker["type_parameters"] == ["T"]
    assert "BaseWorker" in worker["bases"]
    assert "IWorker" in worker["bases"]
    assert interface["declaration_kind"] == "interface"
    assert len(runs) == 2
    assert one_arg_run["call_sequence"].count("helper") == 2
    assert len(one_arg_run["resolved_calls"]) >= 2
    assert all("helper" in target for target in one_arg_run["resolved_calls"][:2])
    assert module["diagnostics"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
