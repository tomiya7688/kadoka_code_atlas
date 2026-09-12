"""Kadoka Code Atlas command-line entry point."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from Src.analyzers.ci import parse_github_actions
from Src.evaluators import evaluate_ci
from Src.generators import CommentGenerator
from Src.renderers import render_ci_workflow
PROJECT_NAME = "Kadoka Code Atlas"

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PROJECT_NAME)
    sub = parser.add_subparsers(dest="command")
    comment = sub.add_parser("comment", help="Generate deterministic source comments.")
    comment.add_argument("source")
    comment.add_argument("--language", help="Adapter name; inferred from the extension.")
    comment.add_argument("--output")
    comment.add_argument("--in-place", action="store_true")
    ci = sub.add_parser("ci", help="Analyze a GitHub Actions workflow.")
    ci.add_argument("source")
    ci.add_argument("--output")
    ci.add_argument("--check", action="store_true", help="Report quality findings and fail on errors.")
    args = parser.parse_args(argv)
    if args.command not in {"comment", "ci"}:
        print(PROJECT_NAME)
        return 0
    if args.command == "ci":
        path = Path(args.source)
        workflow = parse_github_actions(path.read_text(encoding="utf-8"))
        result = render_ci_workflow(workflow)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
        else:
            print(result, end="")
        if args.check:
            findings = evaluate_ci(workflow)
            for finding in findings:
                print(f"{finding.severity}: {finding.code}: {finding.message}", file=sys.stderr)
            return 1 if any(finding.severity == "error" for finding in findings) else 0
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