from src.dominio.candidate_shadow_validation import (
    CandidateShadowValidationCase,
    CandidateShadowValidationOutcome,
    DatasetPartition,
    ExpectedCondition,
    validate_candidate_shadow,
)


def case(
    case_id,
    *,
    partition=DatasetPartition.HOLDOUT,
    provider="provider:holdout",
    source="source:holdout",
    raw="raw:holdout",
    expected=ExpectedCondition.NO_EXPLICIT_EVIDENCE,
    in_scope=True,
    explicit=None,
    provenance=True,
    temporal="v1",
    ambiguous=False,
):
    return CandidateShadowValidationCase(
        case_id=case_id,
        candidate_id="candidate:1",
        candidate_version="v1",
        observation_id=case_id,
        provider_id=provider,
        source_id=source,
        raw_document_id=raw,
        raw_document_path=f"{raw}.html",
        raw_document_hash=raw,
        temporal_version=temporal,
        extraction_version="extractor:v1",
        partition=partition,
        expected_condition=expected,
        raw_basis="offer text",
        provenance_reference="artifact.jsonl" if provenance else "",
        in_candidate_scope=in_scope,
        replay_explicit_hardware=explicit,
        ambiguous_attribution=ambiguous,
    )


def validate(*cases, conflicts_preserved=True):
    return validate_candidate_shadow(
        candidate_id="candidate:1",
        candidate_version="v1",
        candidate_scope="targeted_acquisition:v1",
        proposed_knowledge="targeted acquisition yields NO_EXPLICIT_EVIDENCE",
        cases=cases,
        dataset_version="dataset:v1",
        runner_version="runner:v1",
        champion_conflicts_preserved=conflicts_preserved,
    )


def test_support_is_separated_from_holdout_and_same_source_does_not_generalize():
    result = validate(
        case("support", partition=DatasetPartition.SUPPORT, provider="provider:a", source="source:a"),
        case("same", provider="provider:a", source="source:a", raw="raw:new", temporal="v2"),
    )

    assert result.support_cases == 1
    assert result.holdout_cases == 1
    assert result.independent_validation_provider_count == 0
    assert result.independent_validation_source_count == 0
    assert result.outcome is CandidateShadowValidationOutcome.NEEDS_MORE_EVIDENCE


def test_snapshot_versions_do_not_inflate_source_or_provider_diversity():
    result = validate(
        case("support", partition=DatasetPartition.SUPPORT, provider="provider:a", source="source:a"),
        case("v2", provider="provider:a", source="source:a", raw="raw:v2", temporal="v2"),
        case("v3", provider="provider:a", source="source:a", raw="raw:v3", temporal="v3"),
    )

    assert result.temporal_versions_tested == 3
    assert result.independent_validation_source_count == 0
    assert result.independent_validation_provider_count == 0


def test_independent_holdouts_can_pass_without_promoting():
    result = validate(
        case("support", partition=DatasetPartition.SUPPORT, provider="provider:a", source="source:a"),
        case("h1", provider="provider:b", source="source:b"),
        case("h2", provider="provider:c", source="source:c"),
    )

    assert result.outcome is CandidateShadowValidationOutcome.PASS_SHADOW_VALIDATION
    assert result.independent_validation_provider_count == 2
    assert result.independent_validation_source_count == 2
    assert result.runtime_effect is False
    assert result.promotion_authorized is False


def test_unknown_stays_unknown_and_absence_never_becomes_false():
    result = validate(case("unknown", expected=ExpectedCondition.UNKNOWN, explicit=None))
    evaluation = result.evaluations[0]

    assert evaluation.champion_output == "UNKNOWN"
    assert evaluation.economic_dimension_output == "UNKNOWN"
    assert evaluation.unknown_preserved is True
    assert evaluation.challenger_output != "FALSE"


def test_explicit_inclusion_and_exclusion_are_controls_not_absence():
    result = validate(
        case("included", expected=ExpectedCondition.EXPLICIT_INCLUDED, explicit=True),
        case("excluded", expected=ExpectedCondition.EXPLICIT_EXCLUDED, explicit=False),
    )

    assert result.false_positives == 2
    assert result.outcome is CandidateShadowValidationOutcome.FAIL_SHADOW_VALIDATION


def test_partial_ambiguous_or_out_of_scope_case_is_not_applied():
    result = validate(
        case("partial", expected=ExpectedCondition.UNKNOWN, in_scope=False),
        case("ambiguous", expected=ExpectedCondition.AMBIGUOUS_ATTRIBUTION, ambiguous=True),
    )

    assert all(item.challenger_output == "NOT_APPLIED" for item in result.evaluations)
    assert result.scope_violations == 0
    assert result.unknown_safely_preserved == 2


def test_scope_leak_provenance_loss_hidden_conflict_and_temporal_mismatch_fail():
    scope_leak = case("scope", in_scope=False)
    result = validate_candidate_shadow(
        candidate_id="candidate:1", candidate_version="v1", candidate_scope="targeted_acquisition:v1",
        proposed_knowledge="targeted acquisition yields NO_EXPLICIT_EVIDENCE", cases=(scope_leak,),
        dataset_version="dataset:v1", runner_version="runner:v1", champion_conflicts_preserved=False,
        force_apply_out_of_scope=True,
    )
    assert result.outcome is CandidateShadowValidationOutcome.FAIL_SHADOW_VALIDATION
    assert result.scope_violations == 1
    assert "HIDDEN_CONTRADICTION" in result.rejection_reasons

    provenance = validate(case("no-provenance", provenance=False))
    assert provenance.outcome is CandidateShadowValidationOutcome.FAIL_SHADOW_VALIDATION
    assert provenance.provenance_preserved is False

    temporal = validate(case("temporal", temporal="TEMPORAL_MISMATCH"))
    assert temporal.temporal_violations == 1
    assert temporal.outcome is CandidateShadowValidationOutcome.FAIL_SHADOW_VALIDATION


def test_validation_run_and_replay_are_deterministic():
    cases = (case("support", partition=DatasetPartition.SUPPORT), case("holdout"))
    first = validate(*cases)
    second = validate(*reversed(cases))

    assert first.validation_run_id == second.validation_run_id
    assert first.evaluations == second.evaluations


def test_support_only_requires_more_evidence_and_creates_exact_request():
    result = validate(case("support", partition=DatasetPartition.SUPPORT))

    assert result.outcome is CandidateShadowValidationOutcome.NEEDS_MORE_EVIDENCE
    assert result.evidence_request is not None
    assert result.evidence_request.required_independent_providers == 2
    assert result.evidence_request.required_independent_sources == 2
    assert result.evidence_request.execute_automatically is False
    assert not hasattr(result, "promote")
