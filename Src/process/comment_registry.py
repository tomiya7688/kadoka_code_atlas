"""Process-side construction of the comment adapter registry."""
from Src.languages import CSharpAdapter, CppAdapter, GDScriptAdapter, GoAdapter, JavaAdapter, LanguageAdapter
from Src.languages.python_comments_adapter import PythonAdapter

def default_comment_adapters():
    return {"python": PythonAdapter(), "py": PythonAdapter(), "csharp": CSharpAdapter(), "cs": CSharpAdapter(), "cpp": CppAdapter(), "cxx": CppAdapter(), "gdscript": GDScriptAdapter(), "gd": GDScriptAdapter(), "java": JavaAdapter(), "go": GoAdapter()}
