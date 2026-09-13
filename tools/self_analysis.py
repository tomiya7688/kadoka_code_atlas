"""Run a deterministic, compact self-analysis smoke summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Src.generators import CommentGenerator
from Src.process.config_service import default_capabilities

EXCLUDED_DIRS = {".git", ".codex", ".pytest-temp", "build", "dist", ".self-analysis-output"}


def source_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*.py")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts)
    )


def summarize(root: Path) -> dict[str, object]:
    generator = CommentGenerator()
    files = source_files(root)
    parsed = 0
    candidate_count = 0
    errors: list[dict[str, str]] = []
    for path in files:
        try:
            candidates = generator.candidates(path.read_text(encoding="utf-8"), "python")
        except (OSError, SyntaxError, ValueError) as error:
            errors.append({"path": path.relative_to(root).as_posix(), "error": type(error).__name__})
            continue
        parsed += 1
        candidate_count += len(candidates)
    capabilities = default_capabilities()
    return {
        "parsed_file_count": parsed,
        "source_file_count": len(files),
        "comment_candidate_count": candidate_count,
        "generator_count": sum(item.category == "generator" for item in capabilities),
        "evaluator_count": sum(item.category == "evaluator" for item in capabilities),
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(summarize(args.root.resolve()), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


