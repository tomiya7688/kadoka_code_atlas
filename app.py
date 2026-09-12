"""Kadoka Code Atlas command-line entry point."""
from __future__ import annotations
import argparse
from pathlib import Path
from Src.generators import CommentGenerator
PROJECT_NAME = "Kadoka Code Atlas"

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PROJECT_NAME)
    sub = parser.add_subparsers(dest="command")
    comment = sub.add_parser("comment", help="Generate deterministic source comments.")
    comment.add_argument("source")
    comment.add_argument("--language", help="Adapter name; inferred from the extension.")
    comment.add_argument("--output")
    comment.add_argument("--in-place", action="store_true")
    args = parser.parse_args(argv)
    if args.command != "comment":
        print(PROJECT_NAME)
        return 0
    if args.output and args.in_place:
        parser.error("--output and --in-place cannot be combined")
    path = Path(args.source)
    source = path.read_text(encoding="utf-8")
    result = CommentGenerator().generate(source, args.language or path.suffix)
    if args.in_place:
        path.write_text(result, encoding="utf-8")
    elif args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())