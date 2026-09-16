"""Renderer-neutral state diagram models built from Common IR."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.ir import ModuleIR
from Src.generators.output_names import stable_output_name


@dataclass(frozen=True, slots=True)
class StateDiagramTransition:
    source: str
    target: str
    event: str | None = None
    condition: str | None = None


@dataclass(frozen=True, slots=True)
class StateDiagram:
    name: str
    owner: str
    state_type: str
    state_variable: str
    states: tuple[str, ...]
    transitions: tuple[StateDiagramTransition, ...]
    initial_state: str | None
    terminal_states: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StateDiagramBundle:
    diagrams: tuple[StateDiagram, ...]
    statistics: dict[str, int | tuple[int, ...]]


def build_state_diagram_bundle(module: ModuleIR) -> StateDiagramBundle:
    """Convert passive state-machine IR into logical diagrams, one per owner/variable."""

    diagrams = tuple(
        StateDiagram(
            name=stable_output_name(
                "state",
                f"{machine.owner}.{machine.state_variable}",
                fallback="state_machine",
            ),
            owner=machine.owner,
            state_type=machine.state_type,
            state_variable=machine.state_variable,
            states=machine.states,
            transitions=tuple(
                StateDiagramTransition(
                    source=item.source,
                    target=item.target,
                    event=item.event,
                    condition=item.condition,
                )
                for item in machine.transitions
            ),
            initial_state=machine.initial_state,
            terminal_states=machine.terminal_states,
        )
        for machine in module.state_machines
    )
    return StateDiagramBundle(
        diagrams=diagrams,
        statistics={
            "machine_count": len(diagrams),
            "state_count": sum(len(item.states) for item in diagrams),
            "transition_count": sum(len(item.transitions) for item in diagrams),
        },
    )
