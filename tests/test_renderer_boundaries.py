import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_FOLDERS = ("analyzers", "generators", "evaluators")
LANGUAGE_PARSER_ROOTS = {
    "ast",
    "_ast",
    "tree_sitter",
    "tree_sitter_languages",
    "clang",
    "javalang",
    "libcst",
    "parso",
    "typed_ast",
    "clr",
    "Microsoft",
}


def _python_sources(folder: str):
    yield from (ROOT / "Src" / folder).rglob("*.py")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_generators_do_not_import_renderers() -> None:
    offenders = []
    for path in _python_sources("generators"):
        if any(name == "Src.renderers" or name.startswith("Src.renderers.") for name in _imports(path)):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_renderers_do_not_import_language_adapters() -> None:
    offenders = []
    for path in _python_sources("renderers"):
        if any(name == "Src.languages" or name.startswith("Src.languages.") for name in _imports(path)):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_core_processing_does_not_import_language_adapters() -> None:
    offenders = []
    for folder in CORE_FOLDERS:
        for path in _python_sources(folder):
            if any(name == "Src.languages" or name.startswith("Src.languages.") for name in _imports(path)):
                offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_core_processing_does_not_import_language_specific_parser_backends() -> None:
    offenders: list[tuple[str, str]] = []
    for folder in CORE_FOLDERS:
        for path in _python_sources(folder):
            for name in _imports(path):
                root = name.split(".", 1)[0]
                if root in LANGUAGE_PARSER_ROOTS:
                    offenders.append((path.relative_to(ROOT).as_posix(), name))
    assert offenders == []
