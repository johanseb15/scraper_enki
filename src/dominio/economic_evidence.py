from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Generic, TypeVar

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservationRole,
)


T = TypeVar("T")


class DimensionOrigin(Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"


class DimensionStatus(Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class DimensionClaim(Generic[T]):
    value: T
    origin: DimensionOrigin
    provenance: KnowledgeProvenance
    raw_basis: str

    def __post_init__(self) -> None:
        if self.value is None:
            raise ValueError("DimensionClaim requires a value.")
        if self.provenance is None:
            raise ValueError("DimensionClaim requires provenance.")
        if not self.raw_basis or not self.raw_basis.strip():
            raise ValueError("DimensionClaim requires raw_basis.")


@dataclass(frozen=True)
class DimensionValue(Generic[T]):
    value: T | None
    status: DimensionStatus
    claims: tuple[DimensionClaim[T], ...] = ()

    def __post_init__(self) -> None:
        if self.status is DimensionStatus.UNKNOWN:
            if self.value is not None or self.claims:
                raise ValueError("UNKNOWN dimensions cannot carry a value or claims.")
        elif self.status in {DimensionStatus.CONFLICTED, DimensionStatus.AMBIGUOUS}:
            if self.value is not None or not self.claims:
                raise ValueError("Unresolved dimensions require claims and no selected value.")
        elif self.value is None or not self.claims:
            raise ValueError("Resolved dimensions require value and claims.")

    @property
    def is_usable(self) -> bool:
        return self.status in {DimensionStatus.OBSERVED, DimensionStatus.INFERRED}


def unknown_dimension() -> DimensionValue[object]:
    return DimensionValue(value=None, status=DimensionStatus.UNKNOWN)


def resolve_dimension(*claims: DimensionClaim[T]) -> DimensionValue[T]:
    if not claims:
        return DimensionValue(value=None, status=DimensionStatus.UNKNOWN)
    distinct_values = []
    for claim in claims:
        if claim.value not in distinct_values:
            distinct_values.append(claim.value)
    if len(distinct_values) > 1:
        return DimensionValue(
            value=None,
            status=DimensionStatus.CONFLICTED,
            claims=tuple(claims),
        )
    observed = any(claim.origin is DimensionOrigin.OBSERVED for claim in claims)
    return DimensionValue(
        value=distinct_values[0],
        status=DimensionStatus.OBSERVED if observed else DimensionStatus.INFERRED,
        claims=tuple(claims),
    )


@dataclass(frozen=True)
class ProviderIdentity:
    provider_id: str
    provider_name: str
    source: str


@dataclass(frozen=True)
class GeographyDimension:
    province: str | None = None
    city: str | None = None
    coverage: str | None = None


@dataclass(frozen=True)
class EconomicEvidenceDimensions:
    provider_identity: DimensionValue[ProviderIdentity] = field(default_factory=unknown_dimension)
    price_scope: DimensionValue[str] = field(default_factory=unknown_dimension)
    geography: DimensionValue[GeographyDimension] = field(default_factory=unknown_dimension)
    market_scope: DimensionValue[str] = field(default_factory=unknown_dimension)
    commercial_context: DimensionValue[str] = field(default_factory=unknown_dimension)
    bundle_status: DimensionValue[str] = field(default_factory=unknown_dimension)
    hardware_included: DimensionValue[bool] = field(default_factory=unknown_dimension)
    materials_included: DimensionValue[bool] = field(default_factory=unknown_dimension)
    device_scope: DimensionValue[str] = field(default_factory=unknown_dimension)
    currency: DimensionValue[str] = field(default_factory=unknown_dimension)

    def all_dimensions(self) -> dict[str, DimensionValue[object]]:
        return {
            "provider_identity": self.provider_identity,
            "price_scope": self.price_scope,
            "geography": self.geography,
            "market_scope": self.market_scope,
            "commercial_context": self.commercial_context,
            "bundle_status": self.bundle_status,
            "hardware_included": self.hardware_included,
            "materials_included": self.materials_included,
            "device_scope": self.device_scope,
            "currency": self.currency,
        }


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
    DIMENSION_CONFLICT = "DIMENSION_CONFLICT"
    DEVICE_SCOPE_MISMATCH = "DEVICE_SCOPE_MISMATCH"
    HARDWARE_INCLUDED_MISMATCH = "HARDWARE_INCLUDED_MISMATCH"
    MATERIALS_INCLUDED_MISMATCH = "MATERIALS_INCLUDED_MISMATCH"


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
    dimensions: EconomicEvidenceDimensions | None = None

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
    conflicted_dimensions: tuple[str, ...] = ()

    @property
    def exclusion_reasons(self) -> tuple[EvidenceExclusionReason, ...]:
        present = {reason for item in self.excluded_evidence for reason in item.reasons}
        return tuple(reason for reason in EvidenceExclusionReason if reason in present)
