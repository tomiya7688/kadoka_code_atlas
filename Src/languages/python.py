"""Python AST adapter."""

from __future__ import annotations

import ast

from Src.analyzers.ir import CodeEntity, EntityKind, ModuleIR


class PythonLanguageAdapter:
    """Convert Python source into Kadoka Code Atlas' common IR."""

    language = "python"

    def parse(self, source: str) -> ModuleIR:
        tree = ast.parse(source)
        entities: list[CodeEntity] = []
        self._collect(tree.body, source, entities, parent=None)
        return ModuleIR(language=self.language, entities=entities)

    def _collect(
        self,
        nodes: list[ast.stmt],
        source: str,
        entities: list[CodeEntity],
        parent: str | None,
    ) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                entity = self._class_entity(node, source, parent)
                entities.append(entity)
                self._collect(node.body, source, entities, parent=entity.qualified_name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = EntityKind.METHOD if parent else EntityKind.FUNCTION
                entity = self._function_entity(node, source, parent, kind)
                entities.append(entity)
                self._collect(node.body, source, entities, parent=entity.qualified_name)

    def _class_entity(
        self, node: ast.ClassDef, source: str, parent: str | None
    ) -> CodeEntity:
        return CodeEntity(
            kind=EntityKind.CLASS,
            name=node.name,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            indent=node.col_offset,
            parent=parent,
            docstring=ast.get_docstring(node, clean=False),
            decorators=tuple(self._expr_text(item, source) for item in node.decorator_list),
        )

    def _function_entity(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source: str,
        parent: str | None,
        kind: EntityKind,
    ) -> CodeEntity:
        parameters = [argument.arg for argument in node.args.posonlyargs]
        parameters.extend(argument.arg for argument in node.args.args)
        if node.args.vararg:
            parameters.append(f"*{node.args.vararg.arg}")
        parameters.extend(argument.arg for argument in node.args.kwonlyargs)
        if node.args.kwarg:
            parameters.append(f"**{node.args.kwarg.arg}")

        calls = tuple(
            dict.fromkeys(
                self._call_name(call.func)
                for call in ast.walk(node)
                if isinstance(call, ast.Call) and self._call_name(call.func)
            )
        )
        return CodeEntity(
            kind=kind,
            name=node.name,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            indent=node.col_offset,
            parent=parent,
            docstring=ast.get_docstring(node, clean=False),
            parameters=tuple(parameters),
            decorators=tuple(self._expr_text(item, source) for item in node.decorator_list),
            calls=calls,
        )

    @staticmethod
    def _expr_text(node: ast.AST, source: str) -> str:
        return ast.get_source_segment(source, node) or ""

    @classmethod
    def _call_name(cls, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = cls._call_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""
