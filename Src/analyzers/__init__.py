"""Language-independent analysis models and analyzers."""

from .call_graph import CallEdge, CallGraph
from .ir import CodeEntity, EntityKind, ModuleIR
from .partition import GraphPartition, partition_graph

__all__ = ["CallEdge", "CallGraph", "CodeEntity", "EntityKind", "GraphPartition", "ModuleIR", "partition_graph"]
