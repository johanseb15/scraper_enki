from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticAlias,
    SemanticConcept,
    SemanticContext,
    SemanticKnowledgeIndex,
    SemanticResolutionStatus,
)


def _origin(reference: str = "tests") -> KnowledgeProvenance:
    return KnowledgeProvenance(
        origin_type="TEST_FIXTURE",
        origin_reference=reference,
        origin_version="v1",
    )


def test_known_semantic_concept_can_be_represented():
    concept = SemanticConcept(
        concept_id="FORMATEO_INSTALACION_SO",
        concept_type="LOCAL_SERVICE",
        canonical_name="Formateo e instalacion de SO",
    )

    assert concept.concept_id == "FORMATEO_INSTALACION_SO"
    assert concept.concept_type == "LOCAL_SERVICE"


def test_alias_resolves_to_canonical_concept_with_provenance():
    provenance = _origin("parser_consulta_pricing.RULES")
    concept = SemanticConcept("FORMATEO_INSTALACION_SO", "LOCAL_SERVICE")
    alias = SemanticAlias(
        expression="instalar windows",
        concept_id=concept.concept_id,
        context=SemanticContext.USER_QUERY,
        provenance=provenance,
    )
    index = SemanticKnowledgeIndex(concepts=(concept,), aliases=(alias,))

    resolution = index.resolve("Instalar Windows", context=SemanticContext.USER_QUERY)

    assert resolution.status is SemanticResolutionStatus.RESOLVED
    assert resolution.candidates[0].concept == concept
    assert resolution.candidates[0].provenance == provenance


def test_unknown_expression_returns_unknown_not_false_or_exception():
    index = SemanticKnowledgeIndex(concepts=(), aliases=())

    resolution = index.resolve(
        "servicio que todavia no conocemos",
        context=SemanticContext.USER_QUERY,
    )

    assert resolution.status is SemanticResolutionStatus.UNKNOWN
    assert resolution.candidates == ()
    assert resolution.status is not False


def test_ambiguous_alias_preserves_all_candidates():
    provenance = _origin("ambiguous_fixture")
    concepts = (
        SemanticConcept("DIAGNOSTICO_REVISION", "LOCAL_SERVICE"),
        SemanticConcept("REPARACION_INICIO_WINDOWS", "LOCAL_SERVICE"),
    )
    aliases = (
        SemanticAlias(
            "no inicia",
            "DIAGNOSTICO_REVISION",
            SemanticContext.USER_QUERY,
            provenance,
        ),
        SemanticAlias(
            "no inicia",
            "REPARACION_INICIO_WINDOWS",
            SemanticContext.USER_QUERY,
            provenance,
        ),
    )
    index = SemanticKnowledgeIndex(concepts=concepts, aliases=aliases)

    resolution = index.resolve("No inicia", context=SemanticContext.USER_QUERY)

    assert resolution.status is SemanticResolutionStatus.AMBIGUOUS
    assert {candidate.concept.concept_id for candidate in resolution.candidates} == {
        "DIAGNOSTICO_REVISION",
        "REPARACION_INICIO_WINDOWS",
    }


def test_alias_requires_explicit_provenance():
    try:
        SemanticAlias(
            expression="diagnostico",
            concept_id="DIAGNOSTICO_REVISION",
            context=SemanticContext.USER_QUERY,
            provenance=None,
        )
    except ValueError as exc:
        assert "provenance" in str(exc).lower()
    else:
        raise AssertionError("SemanticAlias accepted missing provenance")


def test_no_pricing_data_is_required_to_build_or_resolve_index():
    concept = SemanticConcept("DIAGNOSTICO_REVISION", "LOCAL_SERVICE")
    alias = SemanticAlias(
        "revision pc",
        concept.concept_id,
        SemanticContext.PROVIDER_OBSERVATION,
        _origin("semantic_normalization_v4.csv"),
    )

    resolution = SemanticKnowledgeIndex(concepts=(concept,), aliases=(alias,)).resolve(
        "revision pc",
        context=SemanticContext.PROVIDER_OBSERVATION,
    )

    assert resolution.status is SemanticResolutionStatus.RESOLVED
    assert not hasattr(resolution, "price")
    assert not hasattr(resolution, "pricing_evidence")


def test_same_concept_accepts_context_specific_aliases():
    concept = SemanticConcept("SOPORTE_REMOTO", "REMOTE_NATIONAL_SERVICE")
    index = SemanticKnowledgeIndex(
        concepts=(concept,),
        aliases=(
            SemanticAlias(
                "soporte remoto",
                concept.concept_id,
                SemanticContext.USER_QUERY,
                _origin("parser"),
            ),
            SemanticAlias(
                "servicio realizado a distancia",
                concept.concept_id,
                SemanticContext.PROVIDER_OBSERVATION,
                _origin("provider_csv"),
            ),
        ),
    )

    user_resolution = index.resolve("soporte remoto", context=SemanticContext.USER_QUERY)
    provider_resolution = index.resolve(
        "servicio realizado a distancia",
        context=SemanticContext.PROVIDER_OBSERVATION,
    )

    assert user_resolution.status is SemanticResolutionStatus.RESOLVED
    assert provider_resolution.status is SemanticResolutionStatus.RESOLVED
    assert user_resolution.candidates[0].concept == provider_resolution.candidates[0].concept


def test_provider_and_user_contexts_can_coexist_without_assuming_identical_semantics():
    concepts = (
        SemanticConcept("FORMATEO_INSTALACION_SO", "LOCAL_SERVICE"),
        SemanticConcept("SOPORTE_TECNICO", "LEGACY_SERVICE"),
    )
    index = SemanticKnowledgeIndex(
        concepts=concepts,
        aliases=(
            SemanticAlias(
                "windows 11",
                "FORMATEO_INSTALACION_SO",
                SemanticContext.USER_QUERY,
                _origin("language_parser"),
            ),
            SemanticAlias(
                "windows 11",
                "SOPORTE_TECNICO",
                SemanticContext.PROVIDER_OBSERVATION,
                _origin("legacy_catalog"),
            ),
        ),
    )

    user_resolution = index.resolve("Windows 11", context=SemanticContext.USER_QUERY)
    provider_resolution = index.resolve("Windows 11", context=SemanticContext.PROVIDER_OBSERVATION)

    assert user_resolution.status is SemanticResolutionStatus.RESOLVED
    assert provider_resolution.status is SemanticResolutionStatus.RESOLVED
    assert user_resolution.candidates[0].concept.concept_id == "FORMATEO_INSTALACION_SO"
    assert provider_resolution.candidates[0].concept.concept_id == "SOPORTE_TECNICO"
