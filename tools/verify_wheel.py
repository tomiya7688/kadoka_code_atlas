"""Install a built wheel in a clean venv and smoke test its public API."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_wheel.py PATH_TO_WHEEL")
    wheel = Path(sys.argv[1]).resolve()
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise SystemExit(f"wheel not found: {wheel}")
    with tempfile.TemporaryDirectory(prefix="kca-wheel-") as temp:
        venv = Path(temp) / "venv"
        run([sys.executable, "-m", "venv", str(venv)])
        python = venv / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
        run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)])
        run([str(python), "-c", "from Src.analyzers import CallGraph; from Src.generators import CommentGenerator; print('artifact imports passed')"])
        run([str(python), "-m", "app"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
