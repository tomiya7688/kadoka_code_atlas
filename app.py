"""Kadoka Code Atlas application entry point."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from Src.process.application import ApplicationService, CIRequest, CommentRequest
from Src.process.config_service import load_config
from Src.process.deployment_service import DeploymentAnalysisRequest, DeploymentService
from Src.process.timing_service import TimingAnalysisRequest, TimingService
from Src.process.use_case_service import UseCaseAnalysisRequest, UseCaseService
from Src.data.files import write_text
PROJECT_NAME = "Kadoka Code Atlas"
PROJECT_VERSION = "0.1.0"
CONFIG_FILE_NAME = "kadoka-code-atlas.json"


def _runtime_root() -> Path:
    """Return the source/package root or the PyInstaller onedir root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _default_config_path() -> Path:
    return _runtime_root() / "config" / CONFIG_FILE_NAME


def _application_service() -> ApplicationService:
    return ApplicationService(load_config(_default_config_path()))


def _launch_gui() -> int:
    from Src.ui import launch_gui

    launch_gui(_application_service())
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        return _launch_gui()

    parser = argparse.ArgumentParser(description=PROJECT_NAME)
    parser.add_argument("--version", action="store_true", help="Show version and exit.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("gui", help="Open the desktop GUI.")
    comment = sub.add_parser("comment", help="Generate deterministic source comments.")
    comment.add_argument("source")
    comment.add_argument("--language", help="Adapter name; inferred from the extension.")
    comment.add_argument("--output")
    comment.add_argument("--in-place", action="store_true")
    ci = sub.add_parser("ci", help="Analyze a GitHub Actions workflow.")
    ci.add_argument("source")
    ci.add_argument("--output")
    ci.add_argument("--check", action="store_true", help="Report quality findings and fail on errors.")
    deployment = sub.add_parser("deployment", help="Generate project deployment diagrams.")
    deployment.add_argument("root")
    deployment.add_argument("--mode", choices=("simple", "full"), default="full")
    deployment.add_argument("--output-dir")
    timing = sub.add_parser("timing", help="Generate logical timing charts from source.")
    timing.add_argument("source")
    timing.add_argument("--language", help="Adapter name; inferred from the extension.")
    timing.add_argument("--output-dir")
    use_cases = sub.add_parser("use-cases", help="Generate GUI-originated use case diagrams.")
    use_cases.add_argument("source")
    use_cases.add_argument("--language", help="Adapter name; inferred from the extension.")
    use_cases.add_argument("--output-dir")
    use_cases.add_argument("--max-depth", type=int, default=5)
    args = parser.parse_args(arguments)

    if args.version:
        print(f"{PROJECT_NAME} {PROJECT_VERSION}")
        return 0
    if args.command == "gui":
        return _launch_gui()
    if args.command not in {"comment", "ci", "deployment", "timing", "use-cases"}:
        parser.print_help()
        return 0

    if args.command == "deployment":
        deployment_service = DeploymentService()
        result = deployment_service.generate(
            DeploymentAnalysisRequest(Path(args.root), args.mode)
        )
        if args.output_dir:
            paths = deployment_service.save(Path(args.output_dir), result)
            for path in paths:
                print(path)
        else:
            for output in result.outputs:
                print(f"%% {output.name}")
                print(output.content, end="")
        return 0

    service = _application_service()
    if args.command == "timing":
        path = Path(args.source)
        language = args.language or service.detect_language(path)
        if language == "unknown":
            parser.error(f"unsupported source file type: {path.suffix or path.name}")
        timing_service = TimingService()
        result = timing_service.generate(TimingAnalysisRequest(path, language))
        if args.output_dir:
            paths = timing_service.save(Path(args.output_dir), result)
            for output_path in paths:
                print(output_path)
        else:
            for output in result.outputs:
                print(f"%% {output.name}")
                print(output.content, end="")
        return 0

    if args.command == "use-cases":
        path = Path(args.source)
        language = args.language or service.detect_language(path)
        if language == "unknown":
            parser.error(f"unsupported source file type: {path.suffix or path.name}")
        use_case_service = UseCaseService()
        result = use_case_service.generate(
            UseCaseAnalysisRequest(path, language),
            max_depth=args.max_depth,
        )
        if args.output_dir:
            paths = use_case_service.save(Path(args.output_dir), result)
            for output_path in paths:
                print(output_path)
        else:
            for output in result.outputs:
                print(f"%% {output.name}")
                print(output.content, end="")
        return 0

    if args.command == "ci":
        result = service.analyze_ci(CIRequest(Path(args.source)))
        if args.output:
            write_text(Path(args.output), result.content)
        else:
            print(result.content, end="")
        if args.check:
            for finding in result.findings:
                print(f"{finding.severity}: {finding.code}: {finding.message}", file=sys.stderr)
            return 1 if any(finding.severity == "error" for finding in result.findings) else 0
        return 0
    if args.output and args.in_place:
        parser.error("--output and --in-place cannot be combined")
    path = Path(args.source)
    language = args.language or service.detect_language(path)
    if language == "unknown":
        parser.error(f"unsupported source file type: {path.suffix or path.name}")
    result = service.generate_comments(CommentRequest(path, language))
    if args.in_place:
        write_text(path, result.content)
    elif args.output:
        write_text(Path(args.output), result.content)
    else:
        print(result.content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
