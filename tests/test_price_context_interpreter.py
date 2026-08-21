import pytest

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    PriceContextKind,
    PriceContextUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.infraestructura.price_context_interpreter import interpret_price_context


def _provenance(kind="TEST", reference="fixture"):
    return KnowledgeProvenance(kind, reference, "v1")


def _price_context(raw, *, currency="ARS"):
    return SemanticObservation(
        observation_id="1",
        raw_expression=raw,
        semantic_role=SemanticObservationRole.PRICE_CONTEXT,
        market_scope="NONE",
        source="provider_a",
        provider="Provider A",
        province="Córdoba",
        observation_provenance=_provenance("COMMERCIAL_OBSERVATION", "row:1"),
        interpretation_provenance=_provenance("SEMANTIC_NORMALIZATION", "semantic.csv"),
    ), {"currency": currency}


def test_price_context_remains_price_context_and_never_service():
    observation, row = _price_context("Ticket Básico u$s 12,-")

    meaning = interpret_price_context(observation, row=row)

    assert observation.semantic_role is SemanticObservationRole.PRICE_CONTEXT
    assert observation.canonical_service is None
    assert not hasattr(meaning, "canonical_service")


def test_ticket_tier_with_explicit_currency_marker_is_represented():
    observation, row = _price_context("Ticket Básico u$s 12,-")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.context_kind is PriceContextKind.TICKET_TIER
    assert meaning.raw_currency_markers == ("USD",)
    assert meaning.published_currency == "ARS"
    assert meaning.price_scope == "UNKNOWN"
    assert meaning.understanding_status is PriceContextUnderstandingStatus.PARTIAL


def test_explicit_known_price_unit_can_be_represented():
    observation, row = _price_context("Precio por hora")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.price_scope == "PER_HOUR"
    assert meaning.understanding_status is PriceContextUnderstandingStatus.UNDERSTOOD


def test_absent_unit_remains_unknown():
    observation, row = _price_context("Precio especial transferencia")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.context_kind is PriceContextKind.PAYMENT_SPECIFIC_PRICE
    assert meaning.price_scope == "UNKNOWN"
    assert meaning.understanding_status is PriceContextUnderstandingStatus.PARTIAL


def test_duration_without_price_unit_does_not_invent_price_meaning():
    observation, row = _price_context("72hs de Demora")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.context_kind is PriceContextKind.TURNAROUND_TIME
    assert meaning.price_scope == "UNKNOWN"


def test_currency_is_preserved_from_row_without_conversion():
    observation, row = _price_context("Ticket Básico u$s 12,-", currency="USD")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.published_currency == "USD"
    assert meaning.raw_currency_markers == ("USD",)


def test_raw_expression_and_provenance_are_preserved():
    raw = "El precio original era: $ 2.880.000. El precio actual es: $ 2.800.000."
    observation, row = _price_context(raw)

    meaning = interpret_price_context(observation, row=row)

    assert meaning.source_expression == raw
    assert meaning.context_kind is PriceContextKind.PRICE_CHANGE
    assert meaning.provenance == observation.interpretation_provenance


def test_minimum_or_from_context_requires_explicit_language():
    observation, row = _price_context("Precio especial transferencia")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.context_kind is not PriceContextKind.UNKNOWN
    assert not hasattr(meaning, "minimum_price")


def test_unknown_price_context_stays_unknown():
    observation, row = _price_context("contexto de precio sin patron seguro")

    meaning = interpret_price_context(observation, row=row)

    assert meaning.context_kind is PriceContextKind.UNKNOWN
    assert meaning.understanding_status is PriceContextUnderstandingStatus.UNKNOWN


def test_interpretation_does_not_modify_pricing_runtime():
    from src.aplicacion.parser_consulta_pricing import parse_pricing_query

    before = parse_pricing_query("me quieren cobrar 35 lucas por soporte remoto, está bien?")
    observation, row = _price_context("Precio especial transferencia")
    interpret_price_context(observation, row=row)
    after = parse_pricing_query("me quieren cobrar 35 lucas por soporte remoto, está bien?")

    assert after == before


def test_non_price_context_observation_is_rejected():
    observation = SemanticObservation(
        observation_id="2",
        raw_expression="PC Gamer",
        semantic_role=SemanticObservationRole.SCOPE_DEVICE,
        market_scope="NONE",
        source="provider_a",
        provider="Provider A",
        province="Córdoba",
        observation_provenance=_provenance("COMMERCIAL_OBSERVATION", "row:2"),
        interpretation_provenance=_provenance("SEMANTIC_NORMALIZATION", "semantic.csv"),
    )

    with pytest.raises(ValueError):
        interpret_price_context(observation)
