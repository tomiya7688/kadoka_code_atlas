"""Runtime discovery for bundled parser backend assets."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BACKEND_ASSET_DIRECTORY = "backends"
BACKEND_MANIFEST_NAME = "manifest.json"
BACKEND_MANIFEST_VERSION = "1"


def runtime_root() -> Path:
    """Return the application root for source and frozen onedir execution."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def backend_asset_root(app_root: Path | None = None) -> Path:
    """Return the directory reserved for bundled helper/native parser assets."""
    return (app_root or runtime_root()) / BACKEND_ASSET_DIRECTORY


def load_backend_manifest(app_root: Path | None = None) -> dict[str, Any]:
    """Read and minimally validate the bundled backend manifest."""
    path = backend_asset_root(app_root) / BACKEND_MANIFEST_NAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("manifest_version") != BACKEND_MANIFEST_VERSION:
        raise ValueError("Unsupported bundled backend manifest version.")
    if not isinstance(payload.get("backends"), list):
        raise ValueError("Bundled backend manifest must contain a backends list.")
    return payload


def resolve_backend_asset(relative_path: str, app_root: Path | None = None) -> Path:
    """Resolve one manifest-owned backend asset without allowing path escape."""
    root = backend_asset_root(app_root).resolve()
    path = (root / relative_path).resolve()
    if path != root and root not in path.parents:
        raise ValueError("Backend asset path escapes the bundled backend directory.")
    return path
