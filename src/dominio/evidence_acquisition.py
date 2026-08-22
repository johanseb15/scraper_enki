from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcquisitionUnlockPotential:
    observation_id: str
    missing_dimensions: tuple[str, ...]
    candidate_count: int
    potentially_unlocked_pairs: int
    potentially_unlocked_independent_providers: int
    remaining_blockers: tuple[str, ...]
    max_possible_readiness: str
    explanation: str


@dataclass(frozen=True)
class OfferEvidenceIdentity:
    observation_id: str
    source: str
    raw_document_id: str
    offer_key: str | None
    extraction_path: str | None
    status: str
    reason: str


@dataclass(frozen=True)
class AcquisitionOutcome:
    action_id: str
    observation_id: str
    source: str
    requested_dimension: str
    expected_unlock: int
    status: str
    evidence_found: tuple[str, ...]
    actual_unlock: int
    unlock_delta: int
    new_conflicts: tuple[str, ...]
    remaining_gaps: tuple[str, ...]
    raw_document_reference: str | None
    provenance: str
    reason: str
