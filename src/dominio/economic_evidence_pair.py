from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PairCompatibilityState(Enum):
    HARD_BLOCKED = "HARD_BLOCKED"
    EXPLICIT_MISMATCH = "EXPLICIT_MISMATCH"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    COMPARABLE = "COMPARABLE"


@dataclass(frozen=True, order=True)
class PairClaimRequirement:
    observation_id: str
    side: str
    dimension: str

    @property
    def claim_id(self) -> str:
        return f"{self.observation_id}:{self.dimension}"


@dataclass(frozen=True)
class MinimalPairUnlockSet:
    pair_id: str
    required_claims: tuple[PairClaimRequirement, ...]
    hard_blockers: tuple[str, ...]
    explicit_mismatches: tuple[str, ...]
    unresolved_after_hypothetical_success: tuple[str, ...]
    could_be_comparable: bool
    could_contribute_to_partial: bool
    could_contribute_to_ready: bool


@dataclass(frozen=True)
class EconomicEvidencePair:
    pair_id: str
    observation_a: str
    observation_b: str
    canonical: str
    provider_a: str
    provider_b: str
    hard_blockers: tuple[str, ...]
    missing_evidence: tuple[PairClaimRequirement, ...]
    explicit_mismatches: tuple[str, ...]
    compatibility_state: PairCompatibilityState
    temporal_compatibility: str
    score: int
    score_breakdown: tuple[tuple[str, int], ...]
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class AcquisitionActionImpact:
    action_id: str
    source: str
    source_url: str
    claims_potentially_resolved: tuple[str, ...]
    pairs_potentially_affected: tuple[str, ...]
    expected_pairs_unlocked: int
    expected_independent_providers_gained: int
    acquisition_cost: str
    attribution_risk: str
    temporal_risk: str
