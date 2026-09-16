"""Python project dependency adapter layered over the core Python adapter."""

from __future__ import annotations

import ast

from Src.analyzers.ir import ModuleIR
from Src.languages.python import PythonLanguageAdapter


class PythonProjectLanguageAdapter(PythonLanguageAdapter):
    """Add normalized import references needed for project-level dependency analysis."""

    def parse(self, source: str) -> ModuleIR:
        module = super().parse(source)
        tree = ast.parse(source)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                prefix = "." * node.level
                if node.module:
                    imports.append(prefix + node.module)
                else:
                    imports.extend(prefix + alias.name for alias in node.names)
        module.imports = tuple(dict.fromkeys(imports))
        return module
