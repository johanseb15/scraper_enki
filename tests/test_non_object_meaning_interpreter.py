import pytest

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    NonObjectMeaningKind,
    NonObjectUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.infraestructura.non_object_meaning_interpreter import (
    interpret_non_object_meaning,
)


def _prov(kind="SEMANTIC_NORMALIZATION", reference="semantic.csv"):
    return KnowledgeProvenance(kind, reference, "v1")


def _non_object(raw):
    return SemanticObservation(
        observation_id="1",
        raw_expression=raw,
        semantic_role=SemanticObservationRole.NON_OBJECT,
        market_scope="NONE",
        source="provider_a",
        provider="Provider A",
        province="Buenos Aires",
        observation_provenance=_prov("COMMERCIAL_OBSERVATION", "row:1"),
        interpretation_provenance=_prov(),
    )


def test_price_label_is_context_not_economic_object():
    obs = _non_object("Precio:")
    meaning = interpret_non_object_meaning(obs)
    assert meaning.meaning_kind is NonObjectMeaningKind.PRICE_LABEL
    assert meaning.understanding_status is NonObjectUnderstandingStatus.UNDERSTOOD
    assert obs.canonical_service is None
    assert not hasattr(meaning, "canonical_service")


def test_desde_is_lower_bound_without_inventing_cadence():
    meaning = interpret_non_object_meaning(_non_object("Desde"))
    assert meaning.meaning_kind is NonObjectMeaningKind.PRICING_LOWER_BOUND
    assert "LOWER_BOUND" in meaning.signals
    assert not hasattr(meaning, "price_type")
    assert not hasattr(meaning, "cadence")


def test_zero_value_placeholder_does_not_claim_free_price():
    meaning = interpret_non_object_meaning(_non_object("$0,00"))
    assert meaning.meaning_kind is NonObjectMeaningKind.ZERO_VALUE_PLACEHOLDER
    assert "DO_NOT_OVERRIDE_OBSERVED_PRICE" in meaning.signals
    assert not hasattr(meaning, "price_value")


def test_availability_is_context_only():
    meaning = interpret_non_object_meaning(_non_object("DISPONIBLE"))
    assert meaning.meaning_kind is NonObjectMeaningKind.AVAILABILITY_STATUS
    assert meaning.signals == ("AVAILABLE",)


def test_generic_service_heading_is_not_promoted_to_service():
    meaning = interpret_non_object_meaning(_non_object("Problemas Generales."))
    assert meaning.meaning_kind is NonObjectMeaningKind.GENERIC_SERVICE_HEADING
    assert not hasattr(meaning, "canonical_service")


def test_marketing_service_copy_is_context_not_service_identity():
    meaning = interpret_non_object_meaning(
        _non_object("Lo que hacemos Service técnico con precio claro")
    )
    assert meaning.meaning_kind is NonObjectMeaningKind.MARKETING_SERVICE_COPY
    assert set(meaning.signals) == {"SERVICE_LANGUAGE", "MARKETING_LANGUAGE"}
    assert not hasattr(meaning, "canonical_service")


@pytest.mark.parametrize("raw", ["*", "\u200b"])
def test_unresolved_non_object_remains_explicit_unknown(raw):
    meaning = interpret_non_object_meaning(_non_object(raw))
    assert meaning.meaning_kind is NonObjectMeaningKind.UNKNOWN
    assert meaning.understanding_status is NonObjectUnderstandingStatus.UNKNOWN


def test_raw_expression_and_provenance_are_preserved():
    raw = "$0,00"
    obs = _non_object(raw)
    meaning = interpret_non_object_meaning(obs)
    assert meaning.source_expression == raw
    assert meaning.provenance == obs.interpretation_provenance


def test_interpreter_rejects_non_non_object_observation():
    obs = _non_object("Precio:")
    object.__setattr__(obs, "semantic_role", SemanticObservationRole.PRICE_CONTEXT)
    with pytest.raises(ValueError, match="NON_OBJECT"):
        interpret_non_object_meaning(obs)


def test_non_object_meaning_does_not_change_existing_parser_runtime():
    from src.aplicacion.parser_consulta_pricing import parse_pricing_query
    before = parse_pricing_query("cuánto sale instalar Windows")
    interpret_non_object_meaning(_non_object("Desde"))
    after = parse_pricing_query("cuánto sale instalar Windows")
    assert after == before
