"""Data-only deployment topology contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeploymentNode:
    id: str
    label: str
    kind: str
    confidence: str = "unknown"
    environment: str = ""
    source: str = ""
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class DeploymentConnection:
    source: str
    target: str
    relation: str
    confidence: str = "unknown"


@dataclass(frozen=True, slots=True)
class DeploymentTopology:
    nodes: tuple[DeploymentNode, ...] = ()
    connections: tuple[DeploymentConnection, ...] = ()
