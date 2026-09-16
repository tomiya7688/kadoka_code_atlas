from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _python_sources(folder: str):
    yield from (ROOT / "Src" / folder).glob("*.py")


def test_generators_do_not_import_renderers() -> None:
    offenders = []
    for path in _python_sources("generators"):
        text = path.read_text(encoding="utf-8")
        if "Src.renderers" in text or "from ..renderers" in text:
            offenders.append(path.name)
    assert offenders == []


def test_renderers_do_not_import_language_adapters() -> None:
    offenders = []
    for path in _python_sources("renderers"):
        text = path.read_text(encoding="utf-8")
        if "Src.languages" in text or "from ..languages" in text:
            offenders.append(path.name)
    assert offenders == []
