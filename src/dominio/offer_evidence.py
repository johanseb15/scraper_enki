from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SourceClaimMethod(Enum):
    SOURCE_TEXT_EXPLICIT = "SOURCE_TEXT_EXPLICIT"
    STRUCTURED_SOURCE_FIELD = "STRUCTURED_SOURCE_FIELD"
    DERIVED_FROM_SOURCE_TEXT = "DERIVED_FROM_SOURCE_TEXT"
    UNKNOWN = "UNKNOWN"


class SourceClaimStatus(Enum):
    OBSERVED = "OBSERVED"
    CONFLICTED = "CONFLICTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class ChargedUnit(Enum):
    HOUR = "HOUR"
    VISIT = "VISIT"
    UNIT = "UNIT"
    MONTH = "MONTH"
    PROJECT = "PROJECT"
    TOTAL = "TOTAL"


class PriceBound(Enum):
    EXACT = "EXACT"
    LOWER_BOUND = "LOWER_BOUND"
    MINIMUM = "MINIMUM"
    QUOTE_REQUIRED = "QUOTE_REQUIRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EvidenceLineage:
    observation_id: str
    source_id: str
    raw_document_id: str | None
    source_url: str | None
    acquired_at: str | None
    extractor_version: str
    provenance: str
    raw_document_path: str | None = None
    raw_document_hash: str | None = None
    linkage_status: str = "UNKNOWN"
    no_linkage_reason: str | None = None


@dataclass(frozen=True)
class SourceEconomicClaim:
    observation_id: str
    dimension: str
    value: str
    raw_basis: str
    raw_document_id: str
    extraction_method: SourceClaimMethod
    provenance: str
    status: SourceClaimStatus = SourceClaimStatus.OBSERVED
    version: str = "offer-reach-charged-scope-evidence-v1"
    qualifiers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.raw_basis.strip():
            raise ValueError("SourceEconomicClaim requires raw_basis.")
        if not self.raw_document_id.strip():
            raise ValueError(
                "SourceEconomicClaim requires a raw document reference."
            )


@dataclass(frozen=True)
class PageScopeEconomicClaim:
    dimension: str
    value: str
    raw_basis: str
    raw_document_id: str
    extraction_method: SourceClaimMethod
    provenance: str
    status: SourceClaimStatus = SourceClaimStatus.OBSERVED
    version: str = "page-service-scope-evidence-v1"
    qualifiers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.raw_basis.strip():
            raise ValueError("PageScopeEconomicClaim requires raw_basis.")
        if not self.raw_document_id.strip():
            raise ValueError(
                "PageScopeEconomicClaim requires a raw document reference."
            )


@dataclass(frozen=True)
class RawDocumentPageScopeEvidence:
    raw_document_id: str
    source_id: str
    source_url: str | None
    acquired_at: str | None
    claims: tuple[PageScopeEconomicClaim, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.raw_document_id.strip():
            raise ValueError(
                "RawDocumentPageScopeEvidence requires raw_document_id."
            )


@dataclass(frozen=True)
class OfferReachChargedScopeEvidence:
    observation_id: str
    lineage: EvidenceLineage
    claims: tuple[SourceEconomicClaim, ...] = field(default_factory=tuple)
