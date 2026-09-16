"""Process-side construction of the comment adapter registry."""

from __future__ import annotations

from Src.languages import CSharpAdapter, CppAdapter, GDScriptAdapter, GoAdapter, JavaAdapter
from Src.languages.python_comments_adapter import PythonAdapter
from Src.process.contracts import CommentAdapter


def default_comment_adapters() -> dict[str, CommentAdapter]:
    python = PythonAdapter()
    csharp = CSharpAdapter()
    cpp = CppAdapter()
    gdscript = GDScriptAdapter()
    java = JavaAdapter()
    go = GoAdapter()
    return {
        "python": python,
        "py": python,
        "csharp": csharp,
        "cs": csharp,
        "cpp": cpp,
        "cxx": cpp,
        "gdscript": gdscript,
        "gd": gdscript,
        "java": java,
        "go": go,
    }
