"""Python AST adapter for explicit GUI input registrations."""

from __future__ import annotations

import ast

from Src.analyzers.ir import InputEventIR, ModuleIR


_WIDGET_NAMES = {
    "Button",
    "Checkbutton",
    "Radiobutton",
    "Scale",
    "Spinbox",
    "Entry",
    "Combobox",
    "Listbox",
    "Menu",
}


def _expr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expr(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def _literal(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _keyword(call: ast.Call, name: str) -> ast.AST | None:
    for item in call.keywords:
        if item.arg == name:
            return item.value
    return None


def _scope_name(parent: str | None, name: str) -> str:
    return f"{parent}.{name}" if parent else name


class PythonUseCaseLanguageAdapter:
    """Extract GUI input component -> event handler facts from Python syntax."""

    language = "python"

    def parse(self, source: str) -> ModuleIR:
        tree = ast.parse(source)
        events: list[InputEventIR] = []
        seen: set[tuple[int, str, str, str]] = set()

        def add(
            *,
            component: str,
            event: str,
            handler: str,
            line: int,
            label: str | None,
            scope: str | None,
        ) -> None:
            key = (line, component, event, handler)
            if key in seen:
                return
            seen.add(key)
            events.append(
                InputEventIR(
                    actor="User",
                    component=component,
                    event=event,
                    handler=handler,
                    line=line,
                    label=label,
                    scope=scope,
                )
            )

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.class_scope: str | None = None

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                previous = self.class_scope
                self.class_scope = _scope_name(previous, node.name)
                for statement in node.body:
                    self.visit(statement)
                self.class_scope = previous

            def visit_Assign(self, node: ast.Assign) -> None:
                handled = False
                if isinstance(node.value, ast.Call):
                    for target in node.targets:
                        handled = self._widget_call(node.value, _expr(target)) or handled
                if not handled:
                    self.generic_visit(node)

            def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
                handled = False
                if isinstance(node.value, ast.Call):
                    handled = self._widget_call(node.value, _expr(node.target))
                if not handled:
                    self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                self._connect_call(node)
                self._bind_call(node)
                self._widget_call(node, _expr(node.func).rsplit(".", 1)[-1])
                self.generic_visit(node)

            def _widget_call(self, call: ast.Call, component: str) -> bool:
                widget = _expr(call.func).rsplit(".", 1)[-1]
                if widget not in _WIDGET_NAMES:
                    return False
                command = _keyword(call, "command")
                if command is None:
                    return False
                handler = _expr(command)
                if not handler:
                    return False
                add(
                    component=component,
                    event="command",
                    handler=handler,
                    line=call.lineno,
                    label=_literal(_keyword(call, "text")),
                    scope=self.class_scope,
                )
                return True

            def _bind_call(self, call: ast.Call) -> None:
                if not isinstance(call.func, ast.Attribute) or call.func.attr != "bind":
                    return
                component = _expr(call.func.value)
                if len(call.args) >= 2:
                    event_name = _literal(call.args[0]) or _expr(call.args[0])
                    handler = _expr(call.args[1])
                    add(
                        component=component,
                        event=event_name,
                        handler=handler,
                        line=call.lineno,
                        label=None,
                        scope=self.class_scope,
                    )
                for keyword in call.keywords:
                    if keyword.arg and keyword.arg.startswith("on_"):
                        add(
                            component=component,
                            event=keyword.arg,
                            handler=_expr(keyword.value),
                            line=call.lineno,
                            label=None,
                            scope=self.class_scope,
                        )

            def _connect_call(self, call: ast.Call) -> None:
                if not isinstance(call.func, ast.Attribute) or call.func.attr != "connect":
                    return
                signal = call.func.value
                if not isinstance(signal, ast.Attribute) or not call.args:
                    return
                add(
                    component=_expr(signal.value),
                    event=signal.attr,
                    handler=_expr(call.args[0]),
                    line=call.lineno,
                    label=None,
                    scope=self.class_scope,
                )

        Visitor().visit(tree)
        events.sort(key=lambda item: (item.line, item.component, item.event, item.handler))
        return ModuleIR(language=self.language, input_events=events)
