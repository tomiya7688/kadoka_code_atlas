"""Python AST adapter."""

from __future__ import annotations

import ast

from Src.analyzers.ir import CodeEntity, EntityKind, ModuleIR
from Src.analyzers.ir_queries import qualified_name


class PythonLanguageAdapter:
    """Convert Python source into Kadoka Code Atlas' common IR."""

    language = "python"

    def parse(self, source: str) -> ModuleIR:
        tree = ast.parse(source)
        entities: list[CodeEntity] = []
        self._collect(tree.body, source, entities, parent=None, parent_kind=None)
        return ModuleIR(language=self.language, entities=entities)

    def _collect(
        self,
        nodes: list[ast.stmt],
        source: str,
        entities: list[CodeEntity],
        parent: str | None,
        parent_kind: EntityKind | None,
    ) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                entity = self._class_entity(node, source, parent)
                entities.append(entity)
                self._collect(
                    node.body,
                    source,
                    entities,
                    parent=qualified_name(entity),
                    parent_kind=EntityKind.CLASS,
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = (
                    EntityKind.METHOD
                    if parent_kind is EntityKind.CLASS
                    else EntityKind.FUNCTION
                )
                entity = self._function_entity(node, source, parent, kind)
                entities.append(entity)
                self._collect(
                    node.body,
                    source,
                    entities,
                    parent=qualified_name(entity),
                    parent_kind=kind,
                )

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
            calls=self._function_calls(node),
        )

    @classmethod
    def _function_calls(
        cls, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> tuple[str, ...]:
        """Collect calls owned by one lexical function scope only."""

        calls: list[str] = []

        class ScopeVisitor(ast.NodeVisitor):
            def visit_Call(self, call: ast.Call) -> None:
                name = cls._call_name(call.func)
                if name:
                    calls.append(name)
                self.generic_visit(call)

            def visit_FunctionDef(self, nested: ast.FunctionDef) -> None:
                return None

            def visit_AsyncFunctionDef(self, nested: ast.AsyncFunctionDef) -> None:
                return None

            def visit_ClassDef(self, nested: ast.ClassDef) -> None:
                return None

            def visit_Lambda(self, nested: ast.Lambda) -> None:
                return None

        visitor = ScopeVisitor()
        for statement in node.body:
            visitor.visit(statement)
        return tuple(dict.fromkeys(calls))

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
