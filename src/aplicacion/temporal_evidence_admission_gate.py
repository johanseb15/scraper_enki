from __future__ import annotations

from dataclasses import dataclass

from src.dominio.temporal_evidence import TemporalEvidence, TemporalEvidenceState


TEMPORAL_GATE_VERSION = "temporal-evidence-admissibility-v1"
CURRENT_PRICING_CONTRACT = "CURRENT_PRICING"
EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE = "MISSING_TEMPORAL_PROVENANCE"
EXCLUSION_REASON_TEMPORAL_MISMATCH = "TEMPORAL_MISMATCH"
EXCLUSION_REASON_TEMPORAL_CONFLICT = "TEMPORAL_CONFLICT"


@dataclass(frozen=True)
class TemporalAdmissionDecision:
    observation_id: str
    runtime_contract: str
    temporal_state: TemporalEvidenceState
    acquired_at: str | None
    published_at: str | None
    price_validity_time_raw: str | None
    temporal_identity_known: bool
    freshness_policy_known: bool
    admitted: bool
    exclusion_reason: str | None
    exclusion_detail: str | None


def _excluded(
    observation_id: str,
    evidence: TemporalEvidence | None,
    *,
    runtime_contract: str,
    reason: str,
    detail: str,
) -> TemporalAdmissionDecision:
    return TemporalAdmissionDecision(
        observation_id=observation_id,
        runtime_contract=runtime_contract,
        temporal_state=(
            evidence.temporal_state
            if evidence is not None
            else TemporalEvidenceState.TEMPORAL_UNKNOWN
        ),
        acquired_at=evidence.acquired_at if evidence else None,
        published_at=evidence.published_at if evidence else None,
        price_validity_time_raw=(
            evidence.price_validity_time_raw if evidence else None
        ),
        temporal_identity_known=(
            evidence.temporal_identity_known if evidence else False
        ),
        freshness_policy_known=(
            evidence.freshness_policy_known if evidence else False
        ),
        admitted=False,
        exclusion_reason=reason,
        exclusion_detail=detail,
    )


def evaluate_temporal_admission(
    *,
    observation_id: str,
    evidence: TemporalEvidence | None,
    runtime_contract: str = CURRENT_PRICING_CONTRACT,
) -> TemporalAdmissionDecision:
    """Fail closed unless temporal identity and runtime compatibility are explicit."""
    if evidence is None or not evidence.acquired_at:
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE,
            detail="ACQUIRED_AT_UNKNOWN",
        )
    if not evidence.source_id or not evidence.extractor_version:
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE,
            detail="SOURCE_OR_EXTRACTOR_PROVENANCE_UNKNOWN",
        )
    if evidence.filesystem_dates_used_as_evidence:
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE,
            detail="FILESYSTEM_TIMESTAMP_NOT_ADMISSIBLE",
        )
    if evidence.temporal_state is TemporalEvidenceState.TEMPORAL_CONFLICT:
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_TEMPORAL_CONFLICT,
            detail="CONFLICTING_TEMPORAL_CLAIMS",
        )
    if evidence.temporal_state is TemporalEvidenceState.TEMPORAL_MISMATCH:
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_TEMPORAL_MISMATCH,
            detail="TEMPORAL_IDENTITY_MISMATCH",
        )
    if not evidence.temporal_identity_known:
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE,
            detail="TEMPORAL_IDENTITY_UNKNOWN",
        )
    if runtime_contract == CURRENT_PRICING_CONTRACT and (
        evidence.temporal_state is not TemporalEvidenceState.CURRENT_REPRODUCIBLE
        or not evidence.freshness_policy_known
    ):
        return _excluded(
            observation_id,
            evidence,
            runtime_contract=runtime_contract,
            reason=EXCLUSION_REASON_TEMPORAL_MISMATCH,
            detail=(
                "FRESHNESS_POLICY_UNKNOWN"
                if not evidence.freshness_policy_known
                else "HISTORICAL_EVIDENCE_NOT_CURRENT"
            ),
        )

    return TemporalAdmissionDecision(
        observation_id=observation_id,
        runtime_contract=runtime_contract,
        temporal_state=evidence.temporal_state,
        acquired_at=evidence.acquired_at,
        published_at=evidence.published_at,
        price_validity_time_raw=evidence.price_validity_time_raw,
        temporal_identity_known=evidence.temporal_identity_known,
        freshness_policy_known=evidence.freshness_policy_known,
        admitted=True,
        exclusion_reason=None,
        exclusion_detail=None,
    )
