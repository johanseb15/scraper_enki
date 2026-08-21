import pytest

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    LogisticsMeaningKind,
    LogisticsUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.infraestructura.logistics_meaning_interpreter import (
    interpret_logistics_meaning,
)


def _prov(kind="SEMANTIC_NORMALIZATION", reference="semantic.csv"):
    return KnowledgeProvenance(kind, reference, "v1")


def _logistics(raw):
    return SemanticObservation(
        observation_id="1",
        raw_expression=raw,
        semantic_role=SemanticObservationRole.LOGISTICS_CONTEXT,
        market_scope="NONE",
        source="provider_a",
        provider="Provider A",
        province="Córdoba",
        observation_provenance=_prov("COMMERCIAL_OBSERVATION", "row:1"),
        interpretation_provenance=_prov(),
    )


def test_motorbike_within_circunvalacion_is_local_courier_delivery():
    meaning = interpret_logistics_meaning(
        _logistics("Moto dentro de Circunvalación Córdoba")
    )

    assert meaning.meaning_kind is LogisticsMeaningKind.LOCAL_COURIER_DELIVERY
    assert "MOTORBIKE_COURIER" in meaning.channels
    assert "WITHIN_CIRCUNVALACION" in meaning.coverage_signals
    assert "CORDOBA" in meaning.coverage_signals
    assert meaning.understanding_status is LogisticsUnderstandingStatus.UNDERSTOOD


def test_correo_a_domicilio_is_home_delivery():
    meaning = interpret_logistics_meaning(_logistics("Correo a domicilio"))

    assert meaning.meaning_kind is LogisticsMeaningKind.HOME_DELIVERY
    assert "DELIVERY" in meaning.channels
    assert "POSTAL_COURIER" in meaning.channels
    assert meaning.destinations == ("HOME",)


def test_branch_point_hop_is_pickup_point_not_service():
    obs = _logistics("Sucursal/Punto HOP Andreani")
    meaning = interpret_logistics_meaning(obs)

    assert meaning.meaning_kind is LogisticsMeaningKind.PICKUP_POINT
    assert "BRANCH" in meaning.destinations
    assert "PICKUP_POINT" in meaning.destinations
    assert meaning.carriers == ("ANDREANI",)
    assert obs.canonical_service is None
    assert not hasattr(meaning, "canonical_service")


def test_explicit_delivery_to_branch_is_branch_delivery():
    meaning = interpret_logistics_meaning(
        _logistics("Envío a Sucursal Andreani")
    )

    assert meaning.meaning_kind is LogisticsMeaningKind.BRANCH_DELIVERY
    assert "DELIVERY" in meaning.channels
    assert "BRANCH" in meaning.destinations
    assert meaning.carriers == ("ANDREANI",)


def test_explicit_delivery_to_home_is_home_delivery():
    meaning = interpret_logistics_meaning(
        _logistics("Envío a Domicilio (Andreani)")
    )

    assert meaning.meaning_kind is LogisticsMeaningKind.HOME_DELIVERY
    assert "HOME" in meaning.destinations
    assert meaning.carriers == ("ANDREANI",)


def test_logistics_meaning_never_invents_price_charge_or_free_delivery():
    meaning = interpret_logistics_meaning(_logistics("Correo a domicilio"))

    assert not hasattr(meaning, "price_value")
    assert not hasattr(meaning, "delivery_charge")
    assert not hasattr(meaning, "is_free")


def test_unknown_logistics_stays_unknown():
    meaning = interpret_logistics_meaning(_logistics("modalidad especial"))

    assert meaning.meaning_kind is LogisticsMeaningKind.UNKNOWN
    assert meaning.understanding_status is LogisticsUnderstandingStatus.UNKNOWN


def test_raw_expression_and_provenance_are_preserved():
    raw = "Envío a Sucursal Andreani"
    obs = _logistics(raw)

    meaning = interpret_logistics_meaning(obs)

    assert meaning.source_expression == raw
    assert meaning.provenance == obs.interpretation_provenance


def test_interpreter_rejects_non_logistics_observation():
    obs = _logistics("Correo a domicilio")
    object.__setattr__(obs, "semantic_role", SemanticObservationRole.NON_OBJECT)

    with pytest.raises(ValueError, match="LOGISTICS_CONTEXT"):
        interpret_logistics_meaning(obs)


def test_logistics_meaning_does_not_change_parser_onsite_semantics():
    from src.aplicacion.parser_consulta_pricing import parse_pricing_query

    before = parse_pricing_query("necesito un técnico a domicilio para instalar Windows")
    interpret_logistics_meaning(_logistics("Correo a domicilio"))
    after = parse_pricing_query("necesito un técnico a domicilio para instalar Windows")

    assert after == before
