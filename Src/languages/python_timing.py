"""Python AST adapter for logical timing relations."""

from __future__ import annotations

import ast

from Src.analyzers.ir import ModuleIR, TimingEventIR, TimingFlowIR


_PARALLEL_START_CALLS = {
    "asyncio.create_task",
    "create_task",
    "asyncio.ensure_future",
    "ensure_future",
}
_PARALLEL_JOIN_CALLS = {"asyncio.gather", "gather", "asyncio.wait", "wait"}
_SLEEP_CALLS = {"asyncio.sleep", "sleep", "time.sleep"}
_TIMER_SUFFIXES = (".call_later", ".call_at")
_CALLBACK_SUFFIXES = (".call_soon", ".add_done_callback")
_SYNC_WAIT_SUFFIXES = (".acquire", ".wait")


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


def _call_target(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _expr(node.func)
    return None


def _qualified(parent: str | None, name: str) -> str:
    return f"{parent}.{name}" if parent else name


class _TimingVisitor(ast.NodeVisitor):
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.events: list[TimingEventIR] = []

    def emit(
        self,
        kind: str,
        line: int,
        *,
        target: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.events.append(
            TimingEventIR(
                order=len(self.events) + 1,
                kind=kind,
                line=line,
                target=target,
                detail=detail,
            )
        )

    def visit_Await(self, node: ast.Await) -> None:
        if not isinstance(node.value, ast.Call):
            self.emit("await", node.lineno, detail=_expr(node.value))
            return

        call = node.value
        target = _expr(call.func)
        if target in _PARALLEL_JOIN_CALLS:
            for argument in call.args:
                child = _call_target(argument)
                if child:
                    self.emit("parallel_start", argument.lineno, target=child)
            self.emit("parallel_join", node.lineno, target=target)
            return
        if target in _SLEEP_CALLS:
            self.emit("wait", node.lineno, target=target, detail=_expr(call))
            return
        if target.endswith(_SYNC_WAIT_SUFFIXES):
            self.emit("sync_wait", node.lineno, target=target)
            return
        self.emit("await", node.lineno, target=target)

    def visit_Call(self, node: ast.Call) -> None:
        target = _expr(node.func)
        if target in _PARALLEL_START_CALLS:
            child = _call_target(node.args[0]) if node.args else None
            self.emit(
                "parallel_start",
                node.lineno,
                target=child or target,
                detail=target,
            )
            return
        if target in _SLEEP_CALLS:
            self.emit("wait", node.lineno, target=target, detail=_expr(node))
            return
        if target.endswith(_TIMER_SUFFIXES):
            callback_index = 1
            callback = _expr(node.args[callback_index]) if len(node.args) > callback_index else None
            delay = _expr(node.args[0]) if node.args else None
            self.emit("timer", node.lineno, target=callback, detail=delay)
            return
        if target.endswith(_CALLBACK_SUFFIXES):
            callback_index = 0
            callback = _expr(node.args[callback_index]) if node.args else None
            self.emit("callback", node.lineno, target=callback, detail=target)
            return
        if target.endswith(_SYNC_WAIT_SUFFIXES):
            self.emit("sync_wait", node.lineno, target=target)
            return

        self.emit("call", node.lineno, target=target)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            self.emit("sync", node.lineno, detail=f"async with {_expr(item.context_expr)}")
        for statement in node.body:
            self.visit(statement)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            context = _expr(item.context_expr)
            if any(token in context.lower() for token in ("lock", "semaphore", "condition")):
                self.emit("sync", node.lineno, detail=f"with {context}")
        for statement in node.body:
            self.visit(statement)

    def visit_While(self, node: ast.While) -> None:
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            self.emit("periodic", node.lineno, detail="while True")
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None


class PythonTimingLanguageAdapter:
    """Convert Python temporal syntax into passive Common IR timing flows."""

    language = "python"

    def parse(self, source: str) -> ModuleIR:
        tree = ast.parse(source)
        flows: list[TimingFlowIR] = []

        def collect(nodes: list[ast.stmt], parent: str | None = None) -> None:
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    collect(node.body, _qualified(parent, node.name))
                    continue
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                owner = _qualified(parent, node.name)
                visitor = _TimingVisitor(owner)
                for statement in node.body:
                    visitor.visit(statement)
                flows.append(
                    TimingFlowIR(
                        owner=owner,
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        events=tuple(visitor.events),
                    )
                )
                collect(node.body, owner)

        collect(tree.body)
        return ModuleIR(language=self.language, timing_flows=flows)
