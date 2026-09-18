"""Version-1 wire codec for language-neutral Common IR payloads."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

from Src.analyzers.ir import (
    CodeEntity,
    DependencyIR,
    DiagnosticIR,
    EntityKind,
    InputEventIR,
    ModuleIR,
    ObjectInstanceIR,
    SignalIR,
    StateMachineIR,
    StateTransitionIR,
    SymbolReferenceIR,
    TimingEventIR,
    TimingFlowIR,
    Visibility,
)


def module_ir_to_wire(module: ModuleIR) -> dict[str, Any]:
    """Serialize Common IR without backend-specific object identities."""

    return _plain(asdict(module))


def module_ir_from_wire(payload: object) -> ModuleIR:
    """Decode a version-1 Common IR payload from a helper process."""

    data = _mapping(payload, "ir")
    entities = [
        CodeEntity(
            kind=EntityKind(str(item["kind"])),
            name=str(item["name"]),
            line=int(item["line"]),
            end_line=int(item["end_line"]),
            indent=int(item.get("indent", 0)),
            parent=_optional_str(item.get("parent")),
            docstring=_optional_str(item.get("docstring")),
            parameters=_strings(item.get("parameters")),
            decorators=_strings(item.get("decorators")),
            calls=_strings(item.get("calls")),
            call_sequence=_strings(item.get("call_sequence")),
            visibility=Visibility(str(item.get("visibility", Visibility.UNSPECIFIED.value))),
            bases=_strings(item.get("bases")),
            type_parameters=_strings(item.get("type_parameters")),
            interfaces=_strings(item.get("interfaces")),
        )
        for item in _mappings(data.get("entities"), "entities")
    ]
    objects = [
        ObjectInstanceIR(
            name=str(item["name"]),
            type_name=str(item["type_name"]),
            line=int(item["line"]),
            scope=_optional_str(item.get("scope")),
            values=_pairs(item.get("values")),
            references=_pairs(item.get("references")),
        )
        for item in _mappings(data.get("objects"), "objects")
    ]
    state_machines = [
        StateMachineIR(
            owner=str(item["owner"]),
            state_type=str(item["state_type"]),
            state_variable=str(item["state_variable"]),
            states=_strings(item.get("states")),
            transitions=tuple(
                StateTransitionIR(
                    source=str(edge["source"]),
                    target=str(edge["target"]),
                    line=int(edge["line"]),
                    event=_optional_str(edge.get("event")),
                    condition=_optional_str(edge.get("condition")),
                )
                for edge in _mappings(item.get("transitions"), "state transitions")
            ),
            initial_state=_optional_str(item.get("initial_state")),
            terminal_states=_strings(item.get("terminal_states")),
        )
        for item in _mappings(data.get("state_machines"), "state_machines")
    ]
    timing_flows = [
        TimingFlowIR(
            owner=str(item["owner"]),
            is_async=bool(item["is_async"]),
            events=tuple(
                TimingEventIR(
                    order=int(event["order"]),
                    kind=str(event["kind"]),
                    line=int(event["line"]),
                    target=_optional_str(event.get("target")),
                    detail=_optional_str(event.get("detail")),
                )
                for event in _mappings(item.get("events"), "timing events")
            ),
        )
        for item in _mappings(data.get("timing_flows"), "timing_flows")
    ]
    input_events = [
        InputEventIR(
            actor=str(item["actor"]),
            component=str(item["component"]),
            event=str(item["event"]),
            handler=str(item["handler"]),
            line=int(item["line"]),
            label=_optional_str(item.get("label")),
            scope=_optional_str(item.get("scope")),
        )
        for item in _mappings(data.get("input_events"), "input_events")
    ]
    signals = [
        SignalIR(
            name=str(item["name"]),
            line=int(item["line"]),
            owner=_optional_str(item.get("owner")),
            parameters=_strings(item.get("parameters")),
        )
        for item in _mappings(data.get("signals"), "signals")
    ]
    diagnostics = [
        DiagnosticIR(
            kind=str(item["kind"]),
            message=str(item["message"]),
            line=_optional_int(item.get("line")),
        )
        for item in _mappings(data.get("diagnostics"), "diagnostics")
    ]
    dependencies = [
        DependencyIR(
            reference=str(item["reference"]),
            kind=str(item["kind"]),
            line=_optional_int(item.get("line")),
            resolved=bool(item.get("resolved", False)),
            target=_optional_str(item.get("target")),
        )
        for item in _mappings(data.get("dependencies"), "dependencies")
    ]
    references = [
        SymbolReferenceIR(
            kind=str(item["kind"]),
            name=str(item["name"]),
            line=int(item["line"]),
            owner=_optional_str(item.get("owner")),
            resolved=bool(item.get("resolved", False)),
            target=_optional_str(item.get("target")),
        )
        for item in _mappings(data.get("references"), "references")
    ]
    return ModuleIR(
        language=str(data["language"]),
        entities=entities,
        objects=objects,
        state_machines=state_machines,
        timing_flows=timing_flows,
        input_events=input_events,
        signals=signals,
        diagnostics=diagnostics,
        dependencies=dependencies,
        references=references,
        imports=_strings(data.get("imports")),
    )


def _plain(value: object) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object.")
    return value


def _mappings(value: object, label: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array.")
    return [_mapping(item, label) for item in value]


def _strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("Expected an array of strings.")
    return tuple(str(item) for item in value)


def _pairs(value: object) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("Expected an array of pairs.")
    result: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Expected a two-value pair.")
        result.append((str(item[0]), str(item[1])))
    return tuple(result)


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)
