from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TemporalEvidenceState(Enum):
    CURRENT_REPRODUCIBLE = "CURRENT_REPRODUCIBLE"
    HISTORICAL_REPRODUCIBLE = "HISTORICAL_REPRODUCIBLE"
    TEMPORAL_UNKNOWN = "TEMPORAL_UNKNOWN"
    TEMPORAL_CONFLICT = "TEMPORAL_CONFLICT"
    TEMPORAL_MISMATCH = "TEMPORAL_MISMATCH"


@dataclass(frozen=True)
class TemporalEvidence:
    observation_id: str
    source_id: str | None = None
    extractor_version: str | None = None
    raw_document_id: str | None = None
    acquired_at: str | None = None
    published_at: str | None = None
    observed_at: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    price_validity_time_raw: str | None = None
    extractor_run_at: str | None = None
    temporal_state: TemporalEvidenceState = TemporalEvidenceState.TEMPORAL_UNKNOWN
    temporal_identity_known: bool = False
    freshness_policy_known: bool = False
    freshness_policy_version: str | None = None
    provenance: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    filesystem_dates_used_as_evidence: bool = False
