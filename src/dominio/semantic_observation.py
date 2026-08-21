from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.dominio.semantic_knowledge import KnowledgeProvenance, SemanticContext


class SemanticObservationRole(Enum):
    SINGLE_SERVICE = "SINGLE_SERVICE"
    COMPOSITE_SERVICE = "COMPOSITE_SERVICE"
    SCOPE_DEVICE = "SCOPE_DEVICE"
    PRICE_CONTEXT = "PRICE_CONTEXT"
    NON_OBJECT = "NON_OBJECT"
    HARDWARE_PRODUCT = "HARDWARE_PRODUCT"
    LOGISTICS_CONTEXT = "LOGISTICS_CONTEXT"
    UNMAPPED = "UNMAPPED"


class ObservationUnderstandingStatus(Enum):
    FULLY_REPRESENTED = "FULLY_REPRESENTED"
    CLASSIFIED_ONLY = "CLASSIFIED_ONLY"
    PARTIALLY_UNDERSTOOD = "PARTIALLY_UNDERSTOOD"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"
    UNREPRESENTED = "UNREPRESENTED"


@dataclass(frozen=True)
class SemanticObservation:
    observation_id: str
    raw_expression: str
    semantic_role: SemanticObservationRole
    market_scope: str
    source: str
    provider: str
    province: str | None
    observation_provenance: KnowledgeProvenance
    interpretation_provenance: KnowledgeProvenance
    canonical_service: str | None = None
    matched_services: tuple[str, ...] = ()
    context: SemanticContext = SemanticContext.PROVIDER_OBSERVATION

    def __post_init__(self) -> None:
        if not self.observation_id or not self.observation_id.strip():
            raise ValueError("SemanticObservation requires observation_id.")
        if not self.raw_expression or not self.raw_expression.strip():
            raise ValueError("SemanticObservation requires raw_expression.")
        if self.observation_provenance is None:
            raise ValueError("SemanticObservation requires observation_provenance.")
        if self.interpretation_provenance is None:
            raise ValueError("SemanticObservation requires interpretation_provenance.")
        if self.canonical_service and self.semantic_role is not SemanticObservationRole.SINGLE_SERVICE:
            raise ValueError("Only SINGLE_SERVICE observations may carry canonical_service.")

    @property
    def understanding_status(self) -> ObservationUnderstandingStatus:
        if self.semantic_role is SemanticObservationRole.UNMAPPED:
            return ObservationUnderstandingStatus.UNKNOWN
        if self.semantic_role is SemanticObservationRole.SINGLE_SERVICE:
            if self.canonical_service:
                return ObservationUnderstandingStatus.FULLY_REPRESENTED
            return ObservationUnderstandingStatus.AMBIGUOUS
        if self.semantic_role is SemanticObservationRole.COMPOSITE_SERVICE:
            if self.matched_services:
                return ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD
            return ObservationUnderstandingStatus.CLASSIFIED_ONLY
        return ObservationUnderstandingStatus.CLASSIFIED_ONLY
