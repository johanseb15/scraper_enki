from src.aplicacion.parser_consulta_pricing import (
    parse_pricing_query,
)
from src.aplicacion.user_query_understanding_projector import (
    project_user_query_understanding,
)
from src.dominio.semantic_knowledge import SemanticContext
from src.dominio.user_query_understanding import (
    UserQueryFactOrigin,
    UserQueryUnderstandingStatus,
)


def _fact(envelope, field):
    return next(
        item
        for item in envelope.facts
        if item.field == field
    )


def test_complete_user_query_projects_typed_semantic_envelope():
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    envelope = project_user_query_understanding(
        parsed,
    )

    assert envelope.raw_text == raw
    assert envelope.context is SemanticContext.USER_QUERY
    assert (
        envelope.status
        is UserQueryUnderstandingStatus.REPRESENTED
    )

    assert _fact(
        envelope,
        "canonical_services",
    ).value == ("FORMATEO_INSTALACION_SO",)

    assert _fact(
        envelope,
        "market_scope",
    ).value == "LOCAL"

    assert _fact(
        envelope,
        "modality",
    ).value == "ONSITE"

    assert _fact(
        envelope,
        "geography.province",
    ).value == "CABA"

    assert envelope.unknowns == ()

    relations = {
        (
            item.subject,
            item.predicate,
            item.object,
        )
        for item in envelope.relations
    }

    assert (
        "QUERY",
        "HAS_SERVICE",
        "FORMATEO_INSTALACION_SO",
    ) in relations

    assert (
        "QUERY",
        "HAS_MODALITY",
        "ONSITE",
    ) in relations

    assert (
        "QUERY",
        "LOCATED_IN",
        "CABA",
    ) in relations


def test_missing_province_remains_unknown_and_is_not_invented():
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio"
    )

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    assert parsed.geography.province is None
    assert parsed.metadata.clarification_required is True

    envelope = project_user_query_understanding(
        parsed,
    )

    assert (
        envelope.status
        is UserQueryUnderstandingStatus.PARTIAL
    )

    assert "geography.province" in envelope.unknowns

    assert all(
        item.predicate != "LOCATED_IN"
        for item in envelope.relations
    )

    assert not any(
        item.field == "geography.province"
        for item in envelope.facts
    )

    assert (
        "MISSING_PROVINCE"
        in envelope.clarification_reasons
    )


def test_parser_evidence_strength_is_preserved_not_upgraded():
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    envelope = project_user_query_understanding(
        parsed,
    )

    assert _fact(
        envelope,
        "modality",
    ).origin is UserQueryFactOrigin.EXPLICIT

    assert _fact(
        envelope,
        "canonical_services",
    ).origin is UserQueryFactOrigin.DERIVED

    assert _fact(
        envelope,
        "intent_action",
    ).origin is UserQueryFactOrigin.PARSER_CLASSIFICATION

    assert (
        envelope.raw_provenance.origin_type
        == "OBSERVED_USER"
    )

    assert (
        envelope.interpretation_provenance.origin_type
        == "PRICING_QUERY_PARSER"
    )


def test_projection_is_deterministic_and_does_not_mutate_parser_result():
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    before = parsed

    first = project_user_query_understanding(
        parsed,
    )

    second = project_user_query_understanding(
        parsed,
    )

    assert parsed == before
    assert first == second
    assert first.raw_text == parsed.raw_text


def test_multiple_money_ambiguity_is_preserved_fail_closed():
    raw = (
        "me cobran $30000 por instalacion de windows "
        "y $50000 con backup en caba"
    )

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    envelope = project_user_query_understanding(
        parsed,
    )

    assert (
        "MULTIPLE_MONETARY_MENTIONS"
        in envelope.clarification_reasons
    )

    assert (
        envelope.status
        is UserQueryUnderstandingStatus.AMBIGUOUS
    )


def test_unknown_values_are_not_materialized_as_semantic_facts():
    raw = "necesito ayuda con algo"

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    envelope = project_user_query_understanding(
        parsed,
    )

    fact_values = {
        item.value
        for item in envelope.facts
    }

    assert "UNKNOWN" not in fact_values

    assert (
        "economic_object_kind"
        in envelope.unknowns
    )

    assert (
        envelope.status
        is UserQueryUnderstandingStatus.UNKNOWN
    )


def test_projection_provenance_is_explicit_and_stable():
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    first = project_user_query_understanding(
        parsed,
    )

    second = project_user_query_understanding(
        parsed,
    )

    assert (
        first.projection_provenance.origin_type
        == "USER_QUERY_UNDERSTANDING_PROJECTOR"
    )

    assert (
        first.projection_provenance.origin_version
        == "user-query-understanding-v1"
    )

    assert (
        first.projection_provenance.origin_reference
        == first.raw_provenance.origin_reference
    )

    assert (
        first.projection_provenance
        == second.projection_provenance
    )
