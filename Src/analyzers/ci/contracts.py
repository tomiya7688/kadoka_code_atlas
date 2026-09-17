"""Provider-neutral contracts for CI configuration adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from Src.models.ci import CIWorkflow


@runtime_checkable
class CIProviderAdapter(Protocol):
    """Convert one provider's configuration text into the common CI model."""

    provider_id: str

    def parse(self, source: str) -> CIWorkflow:
        """Return normalized CI data without leaking provider parser/YAML types."""
