from src.dominio.knowledge_candidate import (
    CandidateEvidence,
    CandidateEpistemicStatus,
    CandidateType,
    CandidateValidationReadiness,
    KnowledgeCandidate,
    build_shadow_validation_plan,
)


def evidence(
    evidence_id="e:1",
    *,
    observation="1",
    provider="provider:a",
    source="source:a",
    origin="RAW_SOURCE_OBSERVATION",
    value="PER_HOUR",
):
    return CandidateEvidence(
        evidence_id=evidence_id,
        evidence_kind="DIMENSION_CLAIM",
        observation_id=observation,
        provider_id=provider,
        source_id=source,
        origin_type=origin,
        provenance_reference=f"artifact:{evidence_id}",
        temporal_version="v1",
        value=value,
    )


def candidate(*supports, contradictions=(), quarantined_reason=None):
    return KnowledgeCandidate.create(
        candidate_type=CandidateType.DIMENSION_EXTRACTION_CANDIDATE,
        proposed_knowledge="phrase 'por hora' may indicate price_scope=PER_HOUR",
        scope="economic_dimension:price_scope",
        context={"language": "es-AR"},
        supporting_evidence=supports,
        contradicting_evidence=contradictions,
        potential_reuse=("economic_dimensions", "pricing_evidence"),
        first_seen="v1",
        last_seen="v1",
        quarantined_reason=quarantined_reason,
    )


def test_candidate_id_and_readiness_are_deterministic():
    supports = (
        evidence("e:1", provider="provider:a", source="source:a"),
        evidence("e:2", observation="2", provider="provider:b", source="source:b"),
    )
    first = candidate(*supports)
    second = candidate(*reversed(supports))

    assert first.candidate_id == second.candidate_id
    assert first.validation_readiness is CandidateValidationReadiness.READY_FOR_SHADOW_VALIDATION
    assert first.epistemic_status is CandidateEpistemicStatus.SUPPORTED


def test_repetition_does_not_inflate_provider_or_source_independence():
    item = candidate(
        evidence("e:1"),
        evidence("e:2", observation="2"),
    )

    assert item.evidence_summary.observation_count == 2
    assert item.evidence_summary.provider_count == 1
    assert item.evidence_summary.independent_source_count == 1
    assert item.validation_readiness is CandidateValidationReadiness.EVIDENCE_GATHERING


def test_normalized_only_support_is_distinct_and_insufficient():
    item = candidate(evidence(origin="NORMALIZED_FIELD"))

    assert item.evidence_summary.raw_document_count == 0
    assert item.evidence_summary.normalized_evidence_count == 1
    assert item.epistemic_status is CandidateEpistemicStatus.INSUFFICIENT


def test_contradiction_is_preserved_and_prevents_ready_even_with_frequency():
    supports = tuple(
        evidence(f"e:{index}", observation=str(index), provider=f"provider:{index}", source=f"source:{index}")
        for index in range(5)
    )
    contradiction = evidence("c:1", value="PER_VISIT")
    item = candidate(*supports, contradictions=(contradiction,))

    assert item.contradicting_evidence == (contradiction,)
    assert item.epistemic_status is CandidateEpistemicStatus.CONFLICTED
    assert item.validation_readiness is CandidateValidationReadiness.CONFLICTED


def test_unknown_or_absent_evidence_is_not_a_contradiction():
    item = candidate(evidence(value=None))

    assert item.evidence_summary.contradiction_count == 0
    assert item.validation_readiness is CandidateValidationReadiness.EVIDENCE_GATHERING


def test_candidate_can_be_quarantined_and_cannot_self_promote():
    item = candidate(evidence(), quarantined_reason="scope ambiguous")

    assert item.epistemic_status is CandidateEpistemicStatus.QUARANTINED
    assert item.validation_readiness is CandidateValidationReadiness.NOT_READY
    assert not hasattr(item, "promote")
    assert item.runtime_effect is False


def test_provider_specific_scope_and_potential_reuse_remain_declarative():
    item = KnowledgeCandidate.create(
        candidate_type=CandidateType.PROVIDER_PATTERN_CANDIDATE,
        proposed_knowledge="source may omit explicit reach",
        scope="provider:source:a",
        context={"provider_id": "provider:a"},
        supporting_evidence=(evidence(),),
        potential_reuse=("acquisition", "economic_dimensions"),
        first_seen="v1",
        last_seen="v1",
    )

    assert item.scope == "provider:source:a"
    assert item.potential_reuse == ("acquisition", "economic_dimensions")
    assert item.runtime_effect is False


def test_shadow_plan_keeps_champion_active_and_defines_rollback():
    item = candidate(
        evidence("e:1", provider="provider:a", source="source:a"),
        evidence("e:2", observation="2", provider="provider:b", source="source:b"),
    )
    plan = build_shadow_validation_plan(
        item,
        affected_subsystem="economic_dimensions",
        golden_datasets=("data/language/golden_corpus_v1.jsonl",),
        real_datasets=("data/semantic_normalization_v4.csv",),
    )

    assert plan.champion_remains_active is True
    assert plan.challenger_mode == "SHADOW_ONLY"
    assert plan.failure_criteria
    assert plan.rollback_criterion
    assert plan.auto_promotion is False
