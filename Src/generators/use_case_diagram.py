"""Renderer-neutral use case diagrams built from explicit GUI input events."""

from __future__ import annotations

from dataclasses import dataclass
import re

from Src.analyzers.call_sequence import resolve_call_sequences, resolve_callable_reference
from Src.analyzers.ir import InputEventIR, ModuleIR


@dataclass(frozen=True, slots=True)
class UseCase:
    name: str
    actor: str
    component: str
    event: str
    handler: str
    call_chain: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UseCaseDiagram:
    name: str
    scope: str
    use_cases: tuple[UseCase, ...]


@dataclass(frozen=True, slots=True)
class UseCaseDiagramBundle:
    diagrams: tuple[UseCaseDiagram, ...]
    statistics: dict[str, int]


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.-")
    return normalized or "use_cases"


def _humanize_handler(handler: str) -> str:
    name = handler.rsplit(".", 1)[-1]
    for prefix in ("on_", "handle_", "handle", "do_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    for suffix in ("_clicked", "_click", "_pressed", "_press", "_triggered", "_changed"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    words = [item for item in name.strip("_").split("_") if item]
    return " ".join(words).capitalize() if words else "User action"


def _use_case_name(event: InputEventIR) -> str:
    if event.label and event.label.strip():
        return event.label.strip()
    return _humanize_handler(event.handler)


def _call_chain(
    module: ModuleIR,
    event: InputEventIR,
    *,
    max_depth: int,
) -> tuple[str, tuple[str, ...]]:
    sequences = resolve_call_sequences(module)
    root = resolve_callable_reference(module, event.handler, parent=event.scope)
    if root not in sequences:
        return root, ()

    result: list[str] = []
    visited: set[str] = {root}

    def walk(node: str, depth: int) -> None:
        if depth >= max_depth:
            return
        for call in sequences.get(node, ()):
            target = call.target
            if target not in sequences or target in visited:
                continue
            visited.add(target)
            result.append(target)
            walk(target, depth + 1)

    walk(root, 0)
    return root, tuple(result)


def build_use_case_diagram_bundle(
    module: ModuleIR,
    input_events: tuple[InputEventIR, ...] | list[InputEventIR] | None = None,
    *,
    max_depth: int = 5,
) -> UseCaseDiagramBundle:
    """Create GUI-originated use cases and bounded handler call chains."""

    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    events = tuple(module.input_events if input_events is None else input_events)
    grouped: dict[str, list[UseCase]] = {}
    unresolved_handlers = 0

    for event in events:
        handler, chain = _call_chain(module, event, max_depth=max_depth)
        if not chain and handler == event.handler:
            unresolved_handlers += 1
        scope = event.scope or "module"
        grouped.setdefault(scope, []).append(
            UseCase(
                name=_use_case_name(event),
                actor=event.actor,
                component=event.component,
                event=event.event,
                handler=handler,
                call_chain=chain,
            )
        )

    diagrams = tuple(
        UseCaseDiagram(
            name=_safe_name(scope),
            scope=scope,
            use_cases=tuple(items),
        )
        for scope, items in sorted(grouped.items())
    )
    return UseCaseDiagramBundle(
        diagrams,
        {
            "diagram_count": len(diagrams),
            "use_case_count": sum(len(item.use_cases) for item in diagrams),
            "unresolved_handler_count": unresolved_handlers,
        },
    )
