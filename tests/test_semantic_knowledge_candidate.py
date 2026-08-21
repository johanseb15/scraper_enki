from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticAlias,
    SemanticConcept,
    SemanticContext,
    SemanticKnowledgeIndex,
    SemanticResolutionStatus,
)
from src.dominio.semantic_knowledge_candidate import (
    KnowledgeCandidateObservation,
    KnowledgeCandidateStatus,
    aggregate_knowledge_candidates,
    unknown_interpretation_provenance,
)


def _provenance(kind="TEST", reference="fixture"):
    return KnowledgeProvenance(kind, reference, "v1")


def _observation(
    expression="Instalacion de Sistema Operativo Basico",
    concept="FORMATEO_INSTALACION_SO",
    provider="provider_a",
    observation_id="1",
    province="Córdoba",
):
    return KnowledgeCandidateObservation(
        expression=expression,
        context=SemanticContext.PROVIDER_OBSERVATION,
        proposed_concept_id=concept,
        observation_id=observation_id,
        source=provider,
        provider=provider,
        province=province,
        observation_provenance=_provenance("FRESH_PROVIDER_OBSERVATION", observation_id),
        interpretation_provenance=_provenance("SEMANTIC_NORMALIZATION_LIVE", "rule:v1"),
    )


def test_fresh_unseen_semantic_result_can_become_knowledge_candidate():
    candidate = _observation()

    assert candidate.status is KnowledgeCandidateStatus.OBSERVED
    assert candidate.context is SemanticContext.PROVIDER_OBSERVATION


def test_candidate_preserves_original_expression():
    candidate = _observation(expression="Instalación Completa de Sistema Operativo MÁS POPULAR")

    assert candidate.expression == "Instalación Completa de Sistema Operativo MÁS POPULAR"


def test_candidate_preserves_proposed_concept():
    candidate = _observation(concept="REPARACION_INICIO_WINDOWS")

    assert candidate.proposed_concept_id == "REPARACION_INICIO_WINDOWS"


def test_candidate_preserves_observation_provenance():
    candidate = _observation(observation_id="235", provider="tecnicopc_alta_cordoba")

    assert candidate.observation_provenance.origin_type == "FRESH_PROVIDER_OBSERVATION"
    assert candidate.observation_provenance.origin_reference == "235"
    assert candidate.provider == "tecnicopc_alta_cordoba"


def test_candidate_preserves_interpretation_provenance():
    candidate = _observation()

    assert candidate.interpretation_provenance.origin_type == "SEMANTIC_NORMALIZATION_LIVE"
    assert candidate.interpretation_provenance.origin_reference == "rule:v1"


def test_candidate_can_represent_unknown_interpretation_provenance_explicitly():
    candidate = KnowledgeCandidateObservation(
        expression="observed expression",
        context=SemanticContext.PROVIDER_OBSERVATION,
        proposed_concept_id="FORMATEO_INSTALACION_SO",
        observation_id="1",
        source="provider_a",
        provider="provider_a",
        province="Córdoba",
        observation_provenance=_provenance("FRESH_PROVIDER_OBSERVATION", "1"),
        interpretation_provenance=unknown_interpretation_provenance(),
    )

    assert candidate.interpretation_provenance.origin_type == "UNKNOWN"
    assert candidate.interpretation_provenance.origin_reference == "UNKNOWN_INTERPRETATION_PROVENANCE"


def test_candidate_is_not_visible_through_semantic_knowledge_index_resolve():
    candidate = _observation()
    concept = SemanticConcept(candidate.proposed_concept_id, "LOCAL_SERVICE")
    index = SemanticKnowledgeIndex(concepts=(concept,), aliases=())

    resolution = index.resolve(candidate.expression, context=candidate.context)

    assert resolution.status is SemanticResolutionStatus.UNKNOWN


def test_candidate_does_not_create_semantic_alias():
    candidate = _observation()

    assert not isinstance(candidate, SemanticAlias)


def test_candidate_does_not_change_runtime_normalization():
    from src.aplicacion.semantic_normalization_live import classify_new_observation

    expression = "Instalación de Sistema Operativo Básico MÁS POPULAR"
    before = classify_new_observation(expression, province="Córdoba")
    _observation(expression=expression)
    after = classify_new_observation(expression, province="Córdoba")

    assert after == before


def test_same_candidate_twice_from_same_provider_records_two_observations_one_provider():
    aggregate = aggregate_knowledge_candidates((
        _observation(observation_id="235", provider="tecnicopc_alta_cordoba"),
        _observation(observation_id="236", provider="tecnicopc_alta_cordoba"),
    ))[0]

    assert aggregate.observations_n == 2
    assert aggregate.providers_n == 1


def test_same_candidate_from_two_providers_records_two_providers():
    aggregate = aggregate_knowledge_candidates((
        _observation(observation_id="1", provider="provider_a"),
        _observation(observation_id="2", provider="provider_b"),
    ))[0]

    assert aggregate.observations_n == 2
    assert aggregate.providers_n == 2


def test_same_normalized_expression_and_concept_can_aggregate():
    aggregates = aggregate_knowledge_candidates((
        _observation(expression="Instalación completa", observation_id="1"),
        _observation(expression="instalacion   completa", observation_id="2"),
    ))

    assert len(aggregates) == 1
    assert aggregates[0].observations_n == 2


def test_same_expression_different_concepts_do_not_merge():
    aggregates = aggregate_knowledge_candidates((
        _observation(expression="revision pc", concept="DIAGNOSTICO_REVISION"),
        _observation(expression="revision pc", concept="REPARACION_HARDWARE"),
    ))

    assert len(aggregates) == 2
    assert {a.proposed_concept_id for a in aggregates} == {
        "DIAGNOSTICO_REVISION",
        "REPARACION_HARDWARE",
    }
