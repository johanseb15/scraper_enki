from __future__ import annotations

from dataclasses import dataclass

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservation,
)


@dataclass(frozen=True)
class SemanticUnderstandingEnvelope:
    observation: SemanticObservation
    status: ObservationUnderstandingStatus
    meaning: object | None = None

    @property
    def observation_provenance(self) -> KnowledgeProvenance:
        return self.observation.observation_provenance

    @property
    def interpretation_provenance(self) -> KnowledgeProvenance:
        return self.observation.interpretation_provenance
