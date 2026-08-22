from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservationRole,
)


class EconomicObjectKind(Enum):
    SERVICE = "SERVICE"
    COMPOSITE_SERVICE = "COMPOSITE_SERVICE"
    HARDWARE = "HARDWARE"
    CONTEXT = "CONTEXT"
    NON_ECONOMIC = "NON_ECONOMIC"
    UNKNOWN = "UNKNOWN"


class EconomicReadiness(Enum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class EvidenceExclusionReason(Enum):
    SELF_OBSERVATION_NOT_INDEPENDENT = "SELF_OBSERVATION_NOT_INDEPENDENT"
    CANONICAL_SERVICE_MISMATCH = "CANONICAL_SERVICE_MISMATCH"
    GEOGRAPHY_MISMATCH = "GEOGRAPHY_MISMATCH"
    MARKET_SCOPE_MISMATCH = "MARKET_SCOPE_MISMATCH"
    PRICE_SCOPE_MISMATCH = "PRICE_SCOPE_MISMATCH"
    CADENCE_MISMATCH = "CADENCE_MISMATCH"
    COMMERCIAL_CONTEXT_MISMATCH = "COMMERCIAL_CONTEXT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    HARDWARE_SERVICE_BOUNDARY = "HARDWARE_SERVICE_BOUNDARY"
    HARDWARE_FAMILY_MISMATCH = "HARDWARE_FAMILY_MISMATCH"
    BUNDLE_NOT_COMPARABLE = "BUNDLE_NOT_COMPARABLE"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    INVALID_PRICE = "INVALID_PRICE"
    UNKNOWN_SEMANTICS = "UNKNOWN_SEMANTICS"
    AMBIGUOUS_OBJECT = "AMBIGUOUS_OBJECT"
    NON_ECONOMIC_OBJECT = "NON_ECONOMIC_OBJECT"
    LOGISTICS_ONLY = "LOGISTICS_ONLY"
    PRICE_CONTEXT_ONLY = "PRICE_CONTEXT_ONLY"
    SCOPE_ONLY = "SCOPE_ONLY"


@dataclass(frozen=True)
class EconomicEvidenceRecord:
    evidence_id: str
    raw_expression: str
    semantic_role: SemanticObservationRole
    understanding_status: ObservationUnderstandingStatus
    market_scope: str
    provider: str
    province: str | None
    canonical_service: str | None
    matched_services: tuple[str, ...]
    currency: str
    price_value: Decimal | None
    price_scope: str
    commercial_context: str
    provenance: KnowledgeProvenance
    meaning: object | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("EconomicEvidenceRecord requires evidence_id.")
        if self.provenance is None:
            raise ValueError("EconomicEvidenceRecord requires provenance.")


@dataclass(frozen=True)
class ExcludedEconomicEvidence:
    evidence: EconomicEvidenceRecord
    reasons: tuple[EvidenceExclusionReason, ...]

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("Excluded evidence requires at least one reason.")


@dataclass(frozen=True)
class EconomicEvidenceContext:
    observation_id: str
    economic_object_kind: EconomicObjectKind
    semantic_role: SemanticObservationRole
    understanding_status: ObservationUnderstandingStatus
    canonical_service: str | None
    matched_services: tuple[str, ...]
    candidate_evidence: tuple[EconomicEvidenceRecord, ...]
    comparable_evidence: tuple[EconomicEvidenceRecord, ...]
    excluded_evidence: tuple[ExcludedEconomicEvidence, ...]
    missing_dimensions: tuple[str, ...]
    readiness: EconomicReadiness
    evidence_count: int
    independent_provider_count: int
    geography_scope: str
    price_scope: str
    provenance: tuple[KnowledgeProvenance, ...]
    uncertainty: tuple[str, ...] = ()

    @property
    def exclusion_reasons(self) -> tuple[EvidenceExclusionReason, ...]:
        present = {reason for item in self.excluded_evidence for reason in item.reasons}
        return tuple(reason for reason in EvidenceExclusionReason if reason in present)
