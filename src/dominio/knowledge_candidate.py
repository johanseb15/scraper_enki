from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class CandidateType(Enum):
    DIMENSION_EXTRACTION_CANDIDATE = "DIMENSION_EXTRACTION_CANDIDATE"
    PROVIDER_PATTERN_CANDIDATE = "PROVIDER_PATTERN_CANDIDATE"
    ACQUISITION_PATTERN_CANDIDATE = "ACQUISITION_PATTERN_CANDIDATE"
    GAP_PATTERN_CANDIDATE = "GAP_PATTERN_CANDIDATE"


class CandidateEpistemicStatus(Enum):
    SUPPORTED = "SUPPORTED"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT = "INSUFFICIENT"
    QUARANTINED = "QUARANTINED"


class CandidateValidationReadiness(Enum):
    NOT_READY = "NOT_READY"
    EVIDENCE_GATHERING = "EVIDENCE_GATHERING"
    CONFLICTED = "CONFLICTED"
    READY_FOR_SHADOW_VALIDATION = "READY_FOR_SHADOW_VALIDATION"


@dataclass(frozen=True)
class CandidateEvidence:
    evidence_id: str
    evidence_kind: str
    provenance_reference: str
    origin_type: str
    observation_id: str | None = None
    provider_id: str | None = None
    source_id: str | None = None
    raw_document_id: str | None = None
    claim_id: str | None = None
    acquisition_outcome_id: str | None = None
    pair_ids: tuple[str, ...] = ()
    temporal_version: str | None = None
    value: Any = None

    def __post_init__(self) -> None:
        for name in ("evidence_id", "evidence_kind", "provenance_reference", "origin_type"):
            if not str(getattr(self, name) or "").strip():
                raise ValueError(f"CandidateEvidence requires {name}.")


@dataclass(frozen=True)
class CandidateEvidenceSummary:
    observation_count: int
    provider_count: int
    source_count: int
    independent_source_count: int
    temporal_versions: int
    raw_document_count: int
    raw_evidence_count: int
    normalized_evidence_count: int
    contradiction_count: int
    provenance_completeness: str


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    candidate_type: CandidateType
    proposed_knowledge: str
    scope: str
    context: tuple[tuple[str, str], ...]
    supporting_evidence: tuple[CandidateEvidence, ...]
    contradicting_evidence: tuple[CandidateEvidence, ...]
    evidence_summary: CandidateEvidenceSummary
    epistemic_status: CandidateEpistemicStatus
    validation_readiness: CandidateValidationReadiness
    potential_reuse: tuple[str, ...]
    first_seen: str
    last_seen: str
    candidate_version: str = "knowledge-candidate-v1"
    runtime_effect: bool = False
    quarantined_reason: str | None = None

    @classmethod
    def create(
        cls,
        *,
        candidate_type: CandidateType,
        proposed_knowledge: str,
        scope: str,
        context: dict[str, Any],
        supporting_evidence: tuple[CandidateEvidence, ...],
        potential_reuse: tuple[str, ...],
        first_seen: str,
        last_seen: str,
        contradicting_evidence: tuple[CandidateEvidence, ...] = (),
        quarantined_reason: str | None = None,
    ) -> "KnowledgeCandidate":
        if not proposed_knowledge.strip() or not scope.strip():
            raise ValueError("KnowledgeCandidate requires proposed knowledge and scope.")
        ordered_support = tuple(sorted(supporting_evidence, key=lambda item: item.evidence_id))
        ordered_conflicts = tuple(sorted(contradicting_evidence, key=lambda item: item.evidence_id))
        normalized_context = tuple(sorted((str(key), str(value)) for key, value in context.items()))
        reuse = tuple(sorted(set(potential_reuse)))
        summary = _summary(ordered_support, ordered_conflicts)
        epistemic, readiness = _states(summary, quarantined_reason)
        identity = json.dumps(
            {
                "candidate_type": candidate_type.value,
                "proposed_knowledge": proposed_knowledge,
                "scope": scope,
                "context": normalized_context,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        candidate_id = "knowledge-candidate:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        return cls(
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            proposed_knowledge=proposed_knowledge,
            scope=scope,
            context=normalized_context,
            supporting_evidence=ordered_support,
            contradicting_evidence=ordered_conflicts,
            evidence_summary=summary,
            epistemic_status=epistemic,
            validation_readiness=readiness,
            potential_reuse=reuse,
            first_seen=first_seen,
            last_seen=last_seen,
            quarantined_reason=quarantined_reason,
        )


@dataclass(frozen=True)
class CandidateShadowValidationPlan:
    candidate_id: str
    affected_subsystem: str
    current_champion_behavior: str
    challenger_behavior: str
    golden_datasets: tuple[str, ...]
    real_datasets: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    safety_criteria: tuple[str, ...]
    rollback_criterion: str
    champion_remains_active: bool = True
    challenger_mode: str = "SHADOW_ONLY"
    auto_promotion: bool = False


@dataclass(frozen=True)
class CandidateEvidenceRequest:
    request_id: str
    candidate_id: str
    missing_validation_evidence: tuple[str, ...]
    required_provider_diversity: int
    required_source_diversity: int
    contradiction_to_resolve: tuple[str, ...]
    recommended_evidence_type: str
    expected_validation_gain: str
    acquisition_priority: int
    score_breakdown: tuple[tuple[str, int], ...]
    execute_automatically: bool = False


def build_candidate_evidence_request(candidate: KnowledgeCandidate) -> CandidateEvidenceRequest:
    summary = candidate.evidence_summary
    missing = []
    if summary.provider_count < 2:
        missing.append("INDEPENDENT_PROVIDER_SUPPORT")
    if summary.independent_source_count < 2:
        missing.append("INDEPENDENT_SOURCE_SUPPORT")
    if not summary.raw_evidence_count:
        missing.append("RAW_SOURCE_EVIDENCE")
    if summary.contradiction_count:
        missing.append("CONFLICT_RESOLUTION_EVIDENCE")
    breakdown = {
        "REUSE_TARGETS": 3 * len(candidate.potential_reuse),
        "RECURRENT_OBSERVATIONS": min(summary.observation_count, 5),
        "COMPARABILITY_IMPACT": 3 if candidate.candidate_type is CandidateType.GAP_PATTERN_CANDIDATE else 0,
        "MISSING_DIVERSITY": 2 * int(summary.provider_count < 2) + 2 * int(summary.independent_source_count < 2),
        "OPEN_CONFLICT_PENALTY": -4 * summary.contradiction_count,
        "NARROW_PROVIDER_PENALTY": -2 if candidate.scope.startswith("provider:") else 0,
        "TRACEABILITY_PENALTY": -4 if summary.provenance_completeness != "COMPLETE" else 0,
    }
    request_identity = json.dumps(
        {"candidate_id": candidate.candidate_id, "missing": sorted(missing)},
        sort_keys=True,
        separators=(",", ":"),
    )
    return CandidateEvidenceRequest(
        request_id="candidate-evidence-request:" + hashlib.sha256(request_identity.encode()).hexdigest()[:20],
        candidate_id=candidate.candidate_id,
        missing_validation_evidence=tuple(missing),
        required_provider_diversity=max(0, 2 - summary.provider_count),
        required_source_diversity=max(0, 2 - summary.independent_source_count),
        contradiction_to_resolve=tuple(item.evidence_id for item in candidate.contradicting_evidence),
        recommended_evidence_type="OFFER_ATTRIBUTABLE_RAW_SOURCE_EVIDENCE",
        expected_validation_gain="MOVE_TOWARD_SHADOW_VALIDATION",
        acquisition_priority=sum(breakdown.values()),
        score_breakdown=tuple(sorted(breakdown.items())),
    )


def build_shadow_validation_plan(
    candidate: KnowledgeCandidate,
    *,
    affected_subsystem: str,
    golden_datasets: tuple[str, ...],
    real_datasets: tuple[str, ...],
) -> CandidateShadowValidationPlan:
    if candidate.validation_readiness is not CandidateValidationReadiness.READY_FOR_SHADOW_VALIDATION:
        raise ValueError("Only READY_FOR_SHADOW_VALIDATION candidates can receive a shadow plan.")
    return CandidateShadowValidationPlan(
        candidate_id=candidate.candidate_id,
        affected_subsystem=affected_subsystem,
        current_champion_behavior="Current runtime behavior remains authoritative and unchanged.",
        challenger_behavior=f"Evaluate candidate without writes: {candidate.proposed_knowledge}",
        golden_datasets=tuple(sorted(set(golden_datasets))),
        real_datasets=tuple(sorted(set(real_datasets))),
        failure_criteria=("Any new false positive", "Any provenance loss", "Any conflict hidden"),
        safety_criteria=("UNKNOWN remains explicit", "No runtime write", "All evidence traceable"),
        rollback_criterion="Discard challenger artifact on any failure; champion requires no rollback.",
    )


def _summary(
    supporting: tuple[CandidateEvidence, ...],
    contradicting: tuple[CandidateEvidence, ...],
) -> CandidateEvidenceSummary:
    all_evidence = supporting + contradicting
    raw = tuple(item for item in supporting if item.origin_type == "RAW_SOURCE_OBSERVATION" or item.raw_document_id)
    normalized = tuple(item for item in all_evidence if item.origin_type == "NORMALIZED_FIELD")
    return CandidateEvidenceSummary(
        observation_count=len({item.observation_id for item in supporting if item.observation_id}),
        provider_count=len({item.provider_id for item in supporting if item.provider_id}),
        source_count=len({item.source_id for item in supporting if item.source_id}),
        independent_source_count=len({item.source_id for item in supporting if item.source_id}),
        temporal_versions=len({item.temporal_version for item in supporting if item.temporal_version}),
        raw_document_count=len({item.raw_document_id for item in supporting if item.raw_document_id}),
        raw_evidence_count=len(raw),
        normalized_evidence_count=len(normalized),
        contradiction_count=len(contradicting),
        provenance_completeness=(
            "COMPLETE" if all(item.provenance_reference for item in all_evidence) else "INCOMPLETE"
        ),
    )


def _states(summary: CandidateEvidenceSummary, quarantined_reason: str | None):
    if quarantined_reason:
        return CandidateEpistemicStatus.QUARANTINED, CandidateValidationReadiness.NOT_READY
    if summary.contradiction_count:
        return CandidateEpistemicStatus.CONFLICTED, CandidateValidationReadiness.CONFLICTED
    if not summary.observation_count:
        return CandidateEpistemicStatus.INSUFFICIENT, CandidateValidationReadiness.NOT_READY
    if summary.provider_count >= 2 and summary.independent_source_count >= 2 and summary.raw_evidence_count:
        return CandidateEpistemicStatus.SUPPORTED, CandidateValidationReadiness.READY_FOR_SHADOW_VALIDATION
    return CandidateEpistemicStatus.INSUFFICIENT, CandidateValidationReadiness.EVIDENCE_GATHERING
