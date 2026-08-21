from src.aplicacion.fresh_provider_knowledge_reuse_evaluation import (
    FreshKnowledgeReuseClass,
    FreshProviderKnowledgeReuseEvaluator,
)
from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticAlias,
    SemanticConcept,
    SemanticContext,
    SemanticKnowledgeIndex,
)


def _alias(expression, concept_id, reference="fixture"):
    return SemanticAlias(
        expression=expression,
        concept_id=concept_id,
        context=SemanticContext.PROVIDER_OBSERVATION,
        provenance=KnowledgeProvenance("TEST", reference, "v1"),
    )


def _evaluator(
    *aliases,
    seed_expressions=None,
    seed_corpus_expressions=None,
    legacy_interpreter="semantic_normalization_live",
):
    concepts = tuple(
        SemanticConcept(concept_id, "LOCAL_SERVICE")
        for concept_id in sorted({alias.concept_id for alias in aliases})
    )
    index = SemanticKnowledgeIndex(concepts=concepts, aliases=aliases)
    return FreshProviderKnowledgeReuseEvaluator(
        index,
        seed_expressions=seed_expressions or {alias.expression for alias in aliases},
        seed_corpus_expressions=seed_corpus_expressions,
        legacy_interpreter=legacy_interpreter,
    )


def _row(expression, canonical="", role="UNMAPPED", source="provider_a", province="Córdoba", observation_id="1"):
    return {
        "observation_id": observation_id,
        "source": source,
        "provider": source,
        "province": province,
        "economic_object_raw": expression,
        "semantic_role": role,
        "canonical_service": canonical,
    }


def test_exact_historical_alias_reused():
    evaluator = _evaluator(_alias("revision pc", "DIAGNOSTICO_REVISION"))

    result = evaluator.evaluate_row(
        _row("revision pc", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.EXACT_MEMORY_REUSE


def test_unseen_expression_resolved_by_live_only_is_live_generalization():
    evaluator = _evaluator(
        seed_expressions={"revision pc"},
        seed_corpus_expressions={"revision pc"},
    )

    result = evaluator.evaluate_row(
        _row("diagnostico notebook", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.LIVE_GENERALIZATION


def test_unseen_expression_resolved_by_unverified_legacy_is_fresh_unseen_core_unknown():
    evaluator = _evaluator(
        seed_expressions={"revision pc"},
        seed_corpus_expressions={"revision pc"},
        legacy_interpreter="UNKNOWN",
    )

    result = evaluator.evaluate_row(
        _row("diagnostico notebook", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.FRESH_UNSEEN_CANONICAL_CORE_UNKNOWN


def test_seed_seen_non_alias_core_unknown_is_not_fresh_generalization():
    evaluator = _evaluator(
        seed_expressions={"revision pc"},
        seed_corpus_expressions={"combo historico"},
    )

    result = evaluator.evaluate_row(
        _row("combo historico", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.SEED_SEEN_NON_ALIAS_CORE_UNKNOWN


def test_unseen_expression_resolved_by_both_same_is_shared_parity_on_fresh():
    evaluator = _evaluator(
        _alias("diagnostico notebook", "DIAGNOSTICO_REVISION"),
        seed_expressions={"revision pc"},
        seed_corpus_expressions={"revision pc"},
    )

    result = evaluator.evaluate_row(
        _row("diagnostico notebook", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.SHARED_PARITY_ON_FRESH


def test_both_resolve_different_is_semantic_disagreement():
    evaluator = _evaluator(_alias("revision pc", "REPARACION_HARDWARE"))

    result = evaluator.evaluate_row(
        _row("revision pc", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.SEMANTIC_DISAGREEMENT


def test_both_unknown_is_both_unknown():
    evaluator = _evaluator()

    result = evaluator.evaluate_row(_row("servicio raro", "", "UNMAPPED"))

    assert result.reuse_class is FreshKnowledgeReuseClass.BOTH_UNKNOWN


def test_non_service_is_not_comparable():
    evaluator = _evaluator(_alias("combo", "DIAGNOSTICO_REVISION"))

    result = evaluator.evaluate_row(_row("combo", "", "COMPOSITE_SERVICE"))

    assert result.reuse_class is FreshKnowledgeReuseClass.NOT_COMPARABLE


def test_multiple_same_concept_provenance_does_not_create_disagreement():
    evaluator = _evaluator(
        _alias("revision pc", "DIAGNOSTICO_REVISION", "row=A"),
        _alias("revision pc", "DIAGNOSTICO_REVISION", "row=B"),
    )

    result = evaluator.evaluate_row(
        _row("revision pc", "DIAGNOSTICO_REVISION", "SINGLE_SERVICE")
    )

    assert result.reuse_class is FreshKnowledgeReuseClass.EXACT_MEMORY_REUSE
    assert result.core_candidate_concepts == (
        "DIAGNOSTICO_REVISION",
        "DIAGNOSTICO_REVISION",
    )
    assert [p.origin_reference for p in result.core_provenance] == ["row=A", "row=B"]
