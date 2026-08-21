from src.aplicacion.provider_semantic_shadow_comparator import (
    ProviderSemanticComparisonStatus,
    ProviderSemanticShadowComparator,
)
from src.aplicacion.semantic_normalization_live import classify_new_observation
from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticAlias,
    SemanticConcept,
    SemanticContext,
    SemanticKnowledgeIndex,
)


def _index(*aliases):
    concepts = tuple(
        SemanticConcept(concept_id, "LOCAL_SERVICE")
        for concept_id in sorted({alias.concept_id for alias in aliases})
    )
    return SemanticKnowledgeIndex(concepts=concepts, aliases=aliases)


def _alias(expression, concept_id, reference="fixture"):
    return SemanticAlias(
        expression=expression,
        concept_id=concept_id,
        context=SemanticContext.PROVIDER_OBSERVATION,
        provenance=KnowledgeProvenance(
            origin_type="TEST_SEED",
            origin_reference=reference,
            origin_version="v1",
        ),
    )


def test_legacy_and_core_same_canonical_is_parity():
    comparator = ProviderSemanticShadowComparator(
        _index(_alias("Instalación de Sistema Operativo Básico MÁS POPULAR", "FORMATEO_INSTALACION_SO"))
    )

    result = comparator.compare(
        "Instalación de Sistema Operativo Básico MÁS POPULAR",
        province="Córdoba",
    )

    assert result.status is ProviderSemanticComparisonStatus.PARITY
    assert result.legacy_canonical_service == "FORMATEO_INSTALACION_SO"
    assert result.core_candidate_concepts == ("FORMATEO_INSTALACION_SO",)


def test_legacy_resolves_and_core_unknown_is_core_unknown():
    comparator = ProviderSemanticShadowComparator(_index())

    result = comparator.compare(
        "Instalación de Sistema Operativo Básico MÁS POPULAR",
        province="Córdoba",
    )

    assert result.status is ProviderSemanticComparisonStatus.CORE_UNKNOWN
    assert result.legacy_canonical_service == "FORMATEO_INSTALACION_SO"
    assert result.core_candidate_concepts == ()


def test_legacy_unknown_and_core_resolves_is_additional_coverage_without_runtime_change():
    comparator = ProviderSemanticShadowComparator(
        _index(_alias("Servicio realizado a distancia.", "SOPORTE_REMOTO"))
    )

    result = comparator.compare("Servicio realizado a distancia.", province="Córdoba")

    assert result.status is ProviderSemanticComparisonStatus.LEGACY_UNKNOWN_CORE_RESOLVED
    assert result.legacy_canonical_service == ""
    assert result.core_candidate_concepts == ("SOPORTE_REMOTO",)


def test_legacy_resolved_core_different_is_explicit_difference():
    comparator = ProviderSemanticShadowComparator(
        _index(_alias("Instalación de Sistema Operativo Básico MÁS POPULAR", "DIAGNOSTICO_REVISION"))
    )

    result = comparator.compare(
        "Instalación de Sistema Operativo Básico MÁS POPULAR",
        province="Córdoba",
    )

    assert result.status is ProviderSemanticComparisonStatus.LEGACY_RESOLVED_CORE_DIFFERENT
    assert result.legacy_canonical_service == "FORMATEO_INSTALACION_SO"
    assert result.core_candidate_concepts == ("DIAGNOSTICO_REVISION",)


def test_core_ambiguous_is_core_ambiguous():
    comparator = ProviderSemanticShadowComparator(
        _index(
            _alias("observacion ambigua", "DIAGNOSTICO_REVISION", "row=a"),
            _alias("observacion ambigua", "REPARACION_HARDWARE", "row=b"),
        )
    )

    result = comparator.compare("observacion ambigua", province="Córdoba")

    assert result.status is ProviderSemanticComparisonStatus.CORE_AMBIGUOUS
    assert result.core_candidate_concepts == (
        "DIAGNOSTICO_REVISION",
        "REPARACION_HARDWARE",
    )


def test_non_single_service_observation_is_not_comparable_when_core_has_no_result():
    comparator = ProviderSemanticShadowComparator(_index())

    result = comparator.compare(
        "Cambio+Clonado de Disco en PC de Escritorio MÁS POPULAR",
        province="Córdoba",
    )

    assert result.status is ProviderSemanticComparisonStatus.NOT_COMPARABLE
    assert result.legacy_semantic_role == "COMPOSITE_SERVICE"


def test_comparison_preserves_core_provenance():
    comparator = ProviderSemanticShadowComparator(
        _index(_alias("Servicio realizado a distancia.", "SOPORTE_REMOTO", "data/semantic_normalization_v4.csv:observation_id=43"))
    )

    result = comparator.compare("Servicio realizado a distancia.", province="Córdoba")

    assert result.core_provenance[0].origin_type == "TEST_SEED"
    assert result.core_provenance[0].origin_reference == "data/semantic_normalization_v4.csv:observation_id=43"
    assert result.core_provenance[0].origin_version == "v1"


def test_challenger_result_cannot_mutate_legacy_result():
    legacy_before = classify_new_observation(
        "Instalación de Sistema Operativo Básico MÁS POPULAR",
        province="Córdoba",
    )
    comparator = ProviderSemanticShadowComparator(
        _index(_alias("Instalación de Sistema Operativo Básico MÁS POPULAR", "DIAGNOSTICO_REVISION"))
    )

    result = comparator.compare(
        "Instalación de Sistema Operativo Básico MÁS POPULAR",
        province="Córdoba",
    )

    assert result.legacy_classification == legacy_before
    assert legacy_before.canonical_service == "FORMATEO_INSTALACION_SO"


def test_dual_read_returns_champion_output_and_does_not_change_production_normalization():
    expression = "Instalación de Sistema Operativo Básico MÁS POPULAR"
    champion_before = classify_new_observation(expression, province="Córdoba")
    comparator = ProviderSemanticShadowComparator(
        _index(_alias(expression, "DIAGNOSTICO_REVISION"))
    )

    champion_after_shadow = comparator.normalize_with_shadow(expression, province="Córdoba")
    champion_after = classify_new_observation(expression, province="Córdoba")

    assert champion_after_shadow == champion_before
    assert champion_after == champion_before
    assert champion_after_shadow.canonical_service == "FORMATEO_INSTALACION_SO"


def test_duplicate_core_candidates_for_same_concept_are_parity_by_unique_concept(monkeypatch):
    from src.aplicacion import provider_semantic_shadow_comparator as shadow_module
    from src.aplicacion.semantic_normalization_live import SemanticClassification

    monkeypatch.setattr(
        shadow_module,
        "classify_new_observation",
        lambda expression, *, province: SemanticClassification(
            semantic_role="SINGLE_SERVICE",
            market_scope="LOCAL_SERVICE",
            canonical_service="DIAGNOSTICO_REVISION",
        ),
    )
    comparator = ProviderSemanticShadowComparator(
        _index(
            _alias("revision pc", "DIAGNOSTICO_REVISION", "row=A"),
            _alias("revision pc", "DIAGNOSTICO_REVISION", "row=B"),
        )
    )

    result = comparator.compare("revision pc", province="Córdoba")

    assert result.status is ProviderSemanticComparisonStatus.PARITY
    assert result.legacy_canonical_service == "DIAGNOSTICO_REVISION"
    assert result.core_candidate_concepts == (
        "DIAGNOSTICO_REVISION",
        "DIAGNOSTICO_REVISION",
    )
    assert [provenance.origin_reference for provenance in result.core_provenance] == [
        "row=A",
        "row=B",
    ]
