"""Python AST to logical activity-flow adapter."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from Src.models.activity import ActivityEdge, ActivityFlow, ActivityNode


@dataclass
class _Builder:
    nodes: list[ActivityNode] = field(default_factory=list)
    edges: list[ActivityEdge] = field(default_factory=list)
    counter: int = 0

    def node(self, label: str, kind: str = "activity") -> str:
        self.counter += 1
        ident = f"a{self.counter}"
        self.nodes.append(ActivityNode(ident, label, kind))
        return ident

    def link(self, source: str, target: str, label: str | None = None) -> None:
        self.edges.append(ActivityEdge(source, target, label))


def _expr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_expr(node.value)}.{node.attr}"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ast.unparse(node) if hasattr(ast, "unparse") else type(node).__name__


def _statement(builder: _Builder, node: ast.stmt) -> tuple[str, list[str]]:
    if isinstance(node, ast.If):
        decision = builder.node(f"if {_expr(node.test)}", "decision")
        then_entry, then_exits = _sequence(builder, node.body)
        builder.link(decision, then_entry, "Yes")
        exits = list(then_exits)
        if node.orelse:
            else_entry, else_exits = _sequence(builder, node.orelse)
            builder.link(decision, else_entry, "No")
            exits.extend(else_exits)
        else:
            exits.append(decision)
        join = builder.node("endif", "merge")
        for exit_node in exits:
            builder.link(exit_node, join)
        return decision, [join]
    if isinstance(node, (ast.For, ast.While)):
        condition = _expr(node.iter if isinstance(node, ast.For) else node.test)
        decision = builder.node(f"loop {condition}", "decision")
        body_entry, body_exits = _sequence(builder, node.body)
        builder.link(decision, body_entry, "Yes")
        for exit_node in body_exits:
            builder.link(exit_node, decision)
        after = builder.node("end loop", "merge")
        builder.link(decision, after, "No")
        return decision, [after]
    if isinstance(node, ast.Return):
        return builder.node("return" if node.value is None else f"return {_expr(node.value)}", "return"), []
    if isinstance(node, (ast.Break, ast.Continue)):
        return builder.node(type(node).__name__.lower(), "control"), []
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        return builder.node(f"call {_expr(node.value.func)}"), []
    return builder.node(type(node).__name__.lower()), []


def _sequence(builder: _Builder, statements: list[ast.stmt]) -> tuple[str, list[str]]:
    if not statements:
        empty = builder.node("empty")
        return empty, [empty]
    first = ""
    exits: list[str] = []
    for statement in statements:
        entry, statement_exits = _statement(builder, statement)
        if not first:
            first = entry
        if exits:
            for previous in exits:
                builder.link(previous, entry)
        exits = statement_exits or [entry]
    return first, exits


def analyze_python_activity(source: str, function: str | None = None) -> ActivityFlow:
    tree = ast.parse(source)
    body: list[ast.stmt] = tree.body
    if function is not None:
        match = next((node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function), None)
        if match is None:
            raise ValueError(f"Function not found: {function}")
        body = match.body
    builder = _Builder()
    entry, _ = _sequence(builder, body)
    return ActivityFlow(entry, tuple(builder.nodes), tuple(builder.edges))
