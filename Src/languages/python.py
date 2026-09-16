"""Python AST adapter."""

from __future__ import annotations

import ast

from Src.analyzers.ir import (
    CodeEntity,
    EntityKind,
    ModuleIR,
    ObjectInstanceIR,
    Visibility,
)
from Src.analyzers.ir_queries import qualified_name


class PythonLanguageAdapter:
    """Convert Python source into Kadoka Code Atlas' common IR."""

    language = "python"

    def parse(self, source: str) -> ModuleIR:
        tree = ast.parse(source)
        entities: list[CodeEntity] = []
        self._collect(tree.body, source, entities, parent=None, parent_kind=None)
        objects = self._collect_objects(tree, source)
        return ModuleIR(language=self.language, entities=entities, objects=objects)

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
            visibility=self._visibility(node.name),
            bases=tuple(self._expr_text(item, source) for item in node.bases),
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

        call_sequence = self._function_call_sequence(node)
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
            calls=tuple(dict.fromkeys(call_sequence)),
            call_sequence=call_sequence,
            visibility=self._visibility(node.name),
        )

    @classmethod
    def _function_call_sequence(
        cls, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> tuple[str, ...]:
        """Collect calls in source order for one lexical function scope only."""

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
        return tuple(calls)

    @classmethod
    def _collect_objects(cls, tree: ast.Module, source: str) -> list[ObjectInstanceIR]:
        """Collect deterministic static object construction/value/reference facts."""

        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        result: list[ObjectInstanceIR] = []

        def scan_scope(nodes: list[ast.stmt], scope: str | None) -> None:
            builders: dict[str, dict[str, object]] = {}

            def ensure(name: str, type_name: str, line: int) -> dict[str, object]:
                existing = builders.get(name)
                if existing is not None:
                    return existing
                created: dict[str, object] = {
                    "name": name,
                    "type_name": type_name,
                    "line": line,
                    "values": {},
                    "references": {},
                }
                builders[name] = created
                return created

            def construct(target: ast.AST, value: ast.AST, line: int) -> bool:
                target_name = cls._call_name(target)
                type_name = cls._constructor_name(value, class_names)
                if not target_name or not type_name:
                    return False
                item = ensure(target_name, type_name, line)
                if isinstance(value, ast.Call):
                    values = item["values"]
                    assert isinstance(values, dict)
                    for index, argument in enumerate(value.args, start=1):
                        literal = cls._literal_text(argument)
                        if literal is not None:
                            values[f"arg{index}"] = literal
                    for keyword in value.keywords:
                        if keyword.arg is None:
                            continue
                        literal = cls._literal_text(keyword.value)
                        if literal is not None:
                            values[keyword.arg] = literal
                if isinstance(target, ast.Attribute):
                    owner = cls._call_name(target.value)
                    if owner in builders:
                        references = builders[owner]["references"]
                        assert isinstance(references, dict)
                        references[target.attr] = target_name
                return True

            def assign_attribute(target: ast.Attribute, value: ast.AST) -> None:
                owner = cls._call_name(target.value)
                if owner not in builders:
                    return
                item = builders[owner]
                literal = cls._literal_text(value)
                if literal is not None:
                    values = item["values"]
                    assert isinstance(values, dict)
                    values[target.attr] = literal
                    return
                reference = cls._call_name(value)
                if reference:
                    references = item["references"]
                    assert isinstance(references, dict)
                    references[target.attr] = reference

            class ObjectVisitor(ast.NodeVisitor):
                def visit_Assign(self, node: ast.Assign) -> None:
                    for target in node.targets:
                        if construct(target, node.value, node.lineno):
                            continue
                        if isinstance(target, ast.Attribute):
                            assign_attribute(target, node.value)

                def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
                    if node.value is None:
                        return
                    if construct(node.target, node.value, node.lineno):
                        return
                    if isinstance(node.target, ast.Attribute):
                        assign_attribute(node.target, node.value)

                def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                    return None

                def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                    return None

                def visit_ClassDef(self, node: ast.ClassDef) -> None:
                    return None

                def visit_Lambda(self, node: ast.Lambda) -> None:
                    return None

            visitor = ObjectVisitor()
            for statement in nodes:
                visitor.visit(statement)

            for item in builders.values():
                values = item["values"]
                references = item["references"]
                assert isinstance(values, dict) and isinstance(references, dict)
                result.append(
                    ObjectInstanceIR(
                        name=str(item["name"]),
                        type_name=str(item["type_name"]),
                        line=int(item["line"]),
                        scope=scope,
                        values=tuple((str(key), str(value)) for key, value in values.items()),
                        references=tuple(
                            (str(key), str(value)) for key, value in references.items()
                        ),
                    )
                )

        def recurse(nodes: list[ast.stmt], parent: str | None) -> None:
            scan_scope(nodes, parent)
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    class_scope = cls._join_scope(parent, node.name)
                    recurse(node.body, class_scope)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_scope = cls._join_scope(parent, node.name)
                    recurse(node.body, function_scope)

        recurse(tree.body, None)
        return result

    @classmethod
    def _constructor_name(cls, node: ast.AST, class_names: set[str]) -> str:
        if not isinstance(node, ast.Call):
            return ""
        name = cls._call_name(node.func)
        if not name:
            return ""
        tail = name.rsplit(".", 1)[-1]
        if tail in class_names or (tail and tail[0].isupper()):
            return name
        return ""

    @staticmethod
    def _literal_text(node: ast.AST) -> str | None:
        try:
            value = ast.literal_eval(node)
        except (ValueError, TypeError, SyntaxError):
            return None
        rendered = repr(value)
        return rendered if len(rendered) <= 80 else rendered[:77] + "..."

    @staticmethod
    def _join_scope(parent: str | None, name: str) -> str:
        return f"{parent}.{name}" if parent else name

    @staticmethod
    def _visibility(name: str) -> Visibility:
        if name.startswith("__") and not name.endswith("__"):
            return Visibility.PRIVATE
        if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
            return Visibility.PROTECTED
        return Visibility.PUBLIC

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
