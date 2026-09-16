"""Stable, filesystem-safe logical output names."""

from __future__ import annotations

from hashlib import sha256
import re


def stable_output_name(prefix: str, logical_name: str, *, fallback: str = "diagram") -> str:
    """Return a readable deterministic filename stem with collision resistance."""

    readable = re.sub(r"[^A-Za-z0-9_-]+", "_", logical_name).strip("_-")
    if not readable:
        readable = fallback
    readable = readable[:80].rstrip("_-") or fallback
    digest = sha256(logical_name.encode("utf-8")).hexdigest()[:10]
    safe_prefix = re.sub(r"[^A-Za-z0-9_-]+", "_", prefix).strip("_-") or "output"
    return f"{safe_prefix}_{digest}_{readable}"
