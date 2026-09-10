"""Language-independent analysis models and analyzers."""

from .call_graph import CallEdge, CallGraph
from .ir import CodeEntity, EntityKind, ModuleIR

__all__ = ["CallEdge", "CallGraph", "CodeEntity", "EntityKind", "ModuleIR"]
