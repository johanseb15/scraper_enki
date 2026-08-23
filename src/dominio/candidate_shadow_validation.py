from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class CandidateShadowValidationOutcome(Enum):
    PASS_SHADOW_VALIDATION = "PASS_SHADOW_VALIDATION"
    FAIL_SHADOW_VALIDATION = "FAIL_SHADOW_VALIDATION"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    CONFLICTED = "CONFLICTED"
    QUARANTINED = "QUARANTINED"


class DatasetPartition(Enum):
    SUPPORT = "SUPPORT"
    HOLDOUT = "HOLDOUT"


class ExpectedCondition(Enum):
    NO_EXPLICIT_EVIDENCE = "NO_EXPLICIT_EVIDENCE"
    EXPLICIT_INCLUDED = "EXPLICIT_INCLUDED"
    EXPLICIT_EXCLUDED = "EXPLICIT_EXCLUDED"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS_ATTRIBUTION = "AMBIGUOUS_ATTRIBUTION"


@dataclass(frozen=True)
class CandidateShadowValidationCase:
    case_id: str
    candidate_id: str
    candidate_version: str
    observation_id: str
    provider_id: str
    source_id: str
    raw_document_id: str | None
    raw_document_path: str | None
    raw_document_hash: str | None
    temporal_version: str
    extraction_version: str
    partition: DatasetPartition
    expected_condition: ExpectedCondition
    raw_basis: str
    provenance_reference: str
    in_candidate_scope: bool
    replay_explicit_hardware: bool | None
    ambiguous_attribution: bool = False


@dataclass(frozen=True)
class CandidateReplayEvaluation:
    case_id: str
    champion_output: str
    challenger_output: str
    economic_dimension_output: str
    evaluation_classification: str
    safety_result: str
    explanation: str
    unknown_preserved: bool
    provenance_preserved: bool
    scope_violation: bool
    temporal_violation: bool


@dataclass(frozen=True)
class ValidationEvidenceRequest:
    candidate_id: str
    validation_run_id: str
    missing_context: str
    required_independent_providers: int
    required_independent_sources: int
    required_evidence_type: str
    contradiction_to_test: str
    negative_control_needed: str
    expected_validation_gain: str
    execute_automatically: bool = False


@dataclass(frozen=True)
class CandidateShadowValidationResult:
    candidate_id: str
    candidate_version: str
    validation_run_id: str
    dataset_version: str
    runner_version: str
    validation_dataset: str
    champion_behavior: str
    challenger_behavior: str
    evaluations: tuple[CandidateReplayEvaluation, ...]
    total_validation_cases: int
    support_cases: int
    holdout_cases: int
    independent_validation_provider_count: int
    independent_validation_source_count: int
    independent_validation_raw_document_count: int
    temporal_versions_tested: int
    champion_unknown: int
    challenger_unknown: int
    challenger_supported: int
    false_positives: int
    false_negatives: int
    unknown_safely_preserved: int
    conflicts_preserved: bool
    provenance_preserved: bool
    scope_violations: int
    temporal_violations: int
    outcome: CandidateShadowValidationOutcome
    rejection_reasons: tuple[str, ...]
    evidence_request: ValidationEvidenceRequest | None
    provenance: tuple[str, ...]
    runtime_effect: bool = False
    promotion_authorized: bool = False


def validate_candidate_shadow(
    *,
    candidate_id: str,
    candidate_version: str,
    candidate_scope: str,
    proposed_knowledge: str,
    cases: tuple[CandidateShadowValidationCase, ...],
    dataset_version: str,
    runner_version: str,
    champion_conflicts_preserved: bool,
    validation_dataset: str = "candidate_shadow_validation_dataset_v1.jsonl",
    force_apply_out_of_scope: bool = False,
) -> CandidateShadowValidationResult:
    ordered = tuple(sorted(cases, key=lambda item: item.case_id))
    run_id = _run_id(candidate_id, candidate_version, dataset_version, runner_version, ordered)
    evaluations = tuple(
        _evaluate(item, force_apply_out_of_scope=force_apply_out_of_scope)
        for item in ordered
    )
    support = tuple(item for item in ordered if item.partition is DatasetPartition.SUPPORT)
    holdout = tuple(item for item in ordered if item.partition is DatasetPartition.HOLDOUT)
    support_providers = {item.provider_id for item in support}
    support_sources = {item.source_id for item in support}
    independent = tuple(
        item for item in holdout
        if item.in_candidate_scope
        and item.provider_id not in support_providers
        and item.source_id not in support_sources
    )
    independent_providers = {item.provider_id for item in independent}
    independent_sources = {item.source_id for item in independent}
    reasons = []
    false_positives = sum(item.evaluation_classification == "FALSE_POSITIVE" for item in evaluations)
    false_negatives = sum(item.evaluation_classification == "FALSE_NEGATIVE" for item in evaluations)
    scope_violations = sum(item.scope_violation for item in evaluations)
    temporal_violations = sum(item.temporal_violation for item in evaluations)
    provenance_preserved = all(item.provenance_preserved for item in evaluations)
    if false_positives:
        reasons.append("FALSE_POSITIVE")
    if scope_violations:
        reasons.append("SCOPE_LEAK")
    if temporal_violations:
        reasons.append("TEMPORAL_MISMATCH")
    if not provenance_preserved:
        reasons.append("PROVENANCE_LOSS")
    if not champion_conflicts_preserved:
        reasons.append("HIDDEN_CONTRADICTION")
    if any(item.economic_dimension_output == "FALSE" and item.champion_output == "UNKNOWN" for item in evaluations):
        reasons.append("SILENT_UNKNOWN_TO_FALSE")
    critical = bool(reasons)
    if critical:
        outcome = CandidateShadowValidationOutcome.FAIL_SHADOW_VALIDATION
    elif len(independent_providers) < 2 or len(independent_sources) < 2:
        outcome = CandidateShadowValidationOutcome.NEEDS_MORE_EVIDENCE
        reasons.append("INSUFFICIENT_IN_SCOPE_INDEPENDENT_HOLDOUT")
    else:
        outcome = CandidateShadowValidationOutcome.PASS_SHADOW_VALIDATION
    request = None
    if outcome is CandidateShadowValidationOutcome.NEEDS_MORE_EVIDENCE:
        request = ValidationEvidenceRequest(
            candidate_id=candidate_id,
            validation_run_id=run_id,
            missing_context=candidate_scope,
            required_independent_providers=max(0, 2 - len(independent_providers)),
            required_independent_sources=max(0, 2 - len(independent_sources)),
            required_evidence_type="NEW_TARGETED_ACQUISITION_OUTCOME_WITH_REPRODUCIBLE_RAW",
            contradiction_to_test="Explicit offer-attributable hardware inclusion/exclusion must override NO_EXPLICIT_EVIDENCE.",
            negative_control_needed="One in-scope explicit claim and one in-scope genuinely unknown outcome.",
            expected_validation_gain="TEST_CROSS_SOURCE_GENERALIZATION",
        )
    return CandidateShadowValidationResult(
        candidate_id=candidate_id, candidate_version=candidate_version,
        validation_run_id=run_id, dataset_version=dataset_version, runner_version=runner_version,
        validation_dataset=validation_dataset,
        champion_behavior="No explicit offer-attributable claim keeps hardware_included=UNKNOWN.",
        challenger_behavior=proposed_knowledge,
        evaluations=evaluations, total_validation_cases=len(ordered), support_cases=len(support),
        holdout_cases=len(holdout),
        independent_validation_provider_count=len(independent_providers),
        independent_validation_source_count=len(independent_sources),
        independent_validation_raw_document_count=len({item.raw_document_id for item in independent if item.raw_document_id}),
        temporal_versions_tested=len({item.temporal_version for item in ordered}),
        champion_unknown=sum(item.champion_output == "UNKNOWN" for item in evaluations),
        challenger_unknown=sum(item.economic_dimension_output == "UNKNOWN" for item in evaluations),
        challenger_supported=sum(item.evaluation_classification == "SUPPORTED" for item in evaluations),
        false_positives=false_positives, false_negatives=false_negatives,
        unknown_safely_preserved=sum(
            item.champion_output == "UNKNOWN" and item.unknown_preserved
            for item in evaluations
        ),
        conflicts_preserved=champion_conflicts_preserved,
        provenance_preserved=provenance_preserved,
        scope_violations=scope_violations, temporal_violations=temporal_violations,
        outcome=outcome, rejection_reasons=tuple(reasons), evidence_request=request,
        provenance=tuple(sorted({item.provenance_reference for item in ordered if item.provenance_reference})),
    )


def _evaluate(case: CandidateShadowValidationCase, *, force_apply_out_of_scope: bool):
    champion = (
        "TRUE" if case.expected_condition is ExpectedCondition.EXPLICIT_INCLUDED
        else "FALSE" if case.expected_condition is ExpectedCondition.EXPLICIT_EXCLUDED
        else "UNKNOWN"
    )
    temporal_violation = case.temporal_version == "TEMPORAL_MISMATCH"
    provenance_ok = bool(case.provenance_reference and case.raw_document_id and case.raw_document_hash)
    must_decline = not case.in_candidate_scope or case.ambiguous_attribution
    scope_violation = force_apply_out_of_scope and not case.in_candidate_scope
    if must_decline and not force_apply_out_of_scope:
        challenger = "NOT_APPLIED"
        classification = "SAFE_CONTROL"
    elif case.replay_explicit_hardware is not None:
        challenger = "NO_EXPLICIT_EVIDENCE"
        classification = "FALSE_POSITIVE"
    else:
        challenger = "NO_EXPLICIT_EVIDENCE"
        classification = "SUPPORTED" if case.expected_condition is ExpectedCondition.NO_EXPLICIT_EVIDENCE else "SAFE_UNKNOWN"
    economic = champion if champion in {"TRUE", "FALSE"} else "UNKNOWN"
    unknown_preserved = champion != "UNKNOWN" or economic == "UNKNOWN"
    safety = "PASS" if provenance_ok and not scope_violation and not temporal_violation and unknown_preserved else "FAIL"
    return CandidateReplayEvaluation(
        case_id=case.case_id, champion_output=champion, challenger_output=challenger,
        economic_dimension_output=economic, evaluation_classification=classification,
        safety_result=safety,
        explanation="Challenger is observational only; it never writes the economic dimension.",
        unknown_preserved=unknown_preserved, provenance_preserved=provenance_ok,
        scope_violation=scope_violation, temporal_violation=temporal_violation,
    )


def _run_id(candidate_id, candidate_version, dataset_version, runner_version, cases):
    identity = json.dumps({
        "candidate_id": candidate_id, "candidate_version": candidate_version,
        "dataset_version": dataset_version, "runner_version": runner_version,
        "cases": [item.case_id for item in cases],
    }, sort_keys=True, separators=(",", ":"))
    return "candidate-shadow-validation:" + hashlib.sha256(identity.encode()).hexdigest()[:20]
