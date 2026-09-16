"""Language-neutral package/module dependency graph analysis."""

from __future__ import annotations

from dataclasses import dataclass

from Src.analyzers.call_graph import CallEdge, CallGraph


@dataclass(frozen=True, slots=True)
class ModuleDependencyUnit:
    name: str
    imports: tuple[str, ...]
    is_package: bool = False


@dataclass(frozen=True, slots=True)
class PackageDependencyEdge:
    caller: str
    callee: str


@dataclass(slots=True)
class PackageDependencyGraph:
    nodes: set[str]
    edges: list[PackageDependencyEdge]

    def _plain_graph(self) -> CallGraph:
        return CallGraph([CallEdge(item.caller, item.callee) for item in self.edges])

    def fan_in(self) -> dict[str, int]:
        counts = self._plain_graph().fan_in()
        return {node: counts.get(node, 0) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        counts = self._plain_graph().fan_out()
        return {node: counts.get(node, 0) for node in self.nodes}

    def cycles(self) -> list[tuple[str, ...]]:
        return self._plain_graph().cycles()

    def isolated_nodes(self) -> tuple[str, ...]:
        connected = {item.caller for item in self.edges} | {item.callee for item in self.edges}
        return tuple(sorted(self.nodes - connected))


def _resolve_relative(unit: ModuleDependencyUnit, reference: str) -> str:
    level = len(reference) - len(reference.lstrip("."))
    tail = reference[level:]
    base = unit.name.split(".") if unit.is_package else unit.name.split(".")[:-1]
    remove = max(level - 1, 0)
    if remove:
        base = base[:-remove] if remove <= len(base) else []
    if tail:
        base.extend(part for part in tail.split(".") if part)
    return ".".join(base)


def resolve_module_reference(
    unit: ModuleDependencyUnit,
    reference: str,
    known_names: set[str],
) -> str | None:
    """Resolve one normalized import reference against project module names."""

    candidate = _resolve_relative(unit, reference) if reference.startswith(".") else reference
    if candidate in known_names:
        return candidate
    parts = candidate.split(".")
    for end in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:end])
        if prefix in known_names:
            return prefix
    return None


def build_package_dependency_graph(
    units: list[ModuleDependencyUnit],
) -> PackageDependencyGraph:
    """Resolve normalized import references against modules present in one project."""

    known = {item.name: item for item in units}
    known_names = set(known)
    edges: list[PackageDependencyEdge] = []
    seen: set[tuple[str, str]] = set()

    for unit in units:
        for reference in unit.imports:
            target = resolve_module_reference(unit, reference, known_names)
            if not target or target == unit.name:
                continue
            key = (unit.name, target)
            if key in seen:
                continue
            seen.add(key)
            edges.append(PackageDependencyEdge(*key))

    return PackageDependencyGraph(known_names, edges)
