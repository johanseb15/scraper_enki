from src.dominio.semantic_knowledge import KnowledgeProvenance, SemanticAlias, SemanticContext
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)


def _provenance(kind="TEST_OBSERVATION", reference="row:1"):
    return KnowledgeProvenance(kind, reference, "v1")


def _observation(**kwargs):
    defaults = {
        "observation_id": "1",
        "raw_expression": "Instalacion de Windows",
        "semantic_role": SemanticObservationRole.SINGLE_SERVICE,
        "market_scope": "LOCAL_SERVICE",
        "source": "provider_a",
        "provider": "Provider A",
        "province": "Córdoba",
        "canonical_service": "FORMATEO_INSTALACION_SO",
        "matched_services": ("FORMATEO_INSTALACION_SO",),
        "observation_provenance": _provenance(),
        "interpretation_provenance": _provenance("SEMANTIC_NORMALIZATION", "rule:v1"),
    }
    defaults.update(kwargs)
    return SemanticObservation(**defaults)


def test_single_service_observation_is_fully_representable():
    observation = _observation()

    assert observation.understanding_status is ObservationUnderstandingStatus.FULLY_REPRESENTED
    assert observation.semantic_role is SemanticObservationRole.SINGLE_SERVICE
    assert observation.canonical_service == "FORMATEO_INSTALACION_SO"


def test_composite_service_is_representable_without_decomposing_price():
    observation = _observation(
        raw_expression="Formateo + backup",
        semantic_role=SemanticObservationRole.COMPOSITE_SERVICE,
        canonical_service=None,
        matched_services=("FORMATEO_INSTALACION_SO", "BACKUP_DATOS"),
        market_scope="MIXED_OR_UNKNOWN",
    )

    assert observation.understanding_status is ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD
    assert observation.matched_services == ("FORMATEO_INSTALACION_SO", "BACKUP_DATOS")
    assert observation.canonical_service is None
    assert not hasattr(observation, "allocated_price")


def test_hardware_product_is_representable_without_becoming_service():
    observation = _observation(
        raw_expression="RYZEN 5700X CPU RTX 3080 GPU",
        semantic_role=SemanticObservationRole.HARDWARE_PRODUCT,
        canonical_service=None,
        matched_services=(),
        market_scope="GOODS_MARKET",
    )

    assert observation.understanding_status is ObservationUnderstandingStatus.CLASSIFIED_ONLY
    assert observation.canonical_service is None
    assert observation.market_scope == "GOODS_MARKET"


def test_price_context_is_representable_without_canonical_service():
    observation = _observation(
        raw_expression="Ticket Básico u$s 12",
        semantic_role=SemanticObservationRole.PRICE_CONTEXT,
        canonical_service=None,
        matched_services=(),
        market_scope="NONE",
    )

    assert observation.understanding_status is ObservationUnderstandingStatus.CLASSIFIED_ONLY
    assert observation.canonical_service is None


def test_scope_device_is_representable_as_scope_not_service():
    observation = _observation(
        raw_expression="PC Gamer gama media",
        semantic_role=SemanticObservationRole.SCOPE_DEVICE,
        canonical_service=None,
        matched_services=(),
        market_scope="NONE",
    )

    assert observation.understanding_status is ObservationUnderstandingStatus.CLASSIFIED_ONLY
    assert observation.canonical_service is None


def test_unknown_remains_explicit_and_traced():
    observation = _observation(
        raw_expression="texto que aun no sabemos interpretar",
        semantic_role=SemanticObservationRole.UNMAPPED,
        canonical_service=None,
        matched_services=(),
        market_scope="UNKNOWN",
    )

    assert observation.understanding_status is ObservationUnderstandingStatus.UNKNOWN
    assert observation.observation_provenance.origin_reference == "row:1"


def test_provenance_is_required():
    try:
        _observation(observation_provenance=None)
    except ValueError as exc:
        assert "provenance" in str(exc).lower()
    else:
        raise AssertionError("SemanticObservation accepted missing provenance")


def test_interpretation_cannot_mutate_raw_expression():
    raw = "Instalación Completa de Sistema Operativo MÁS POPULAR"

    observation = _observation(raw_expression=raw)

    assert observation.raw_expression == raw


def test_observation_representation_does_not_create_alias_automatically():
    observation = _observation()

    assert not isinstance(observation, SemanticAlias)
    assert observation.context is SemanticContext.PROVIDER_OBSERVATION


def test_observation_representation_does_not_affect_pricing_runtime():
    from src.aplicacion.parser_consulta_pricing import parse_pricing_query

    before = parse_pricing_query("cuánto sale instalar Windows")
    _observation(raw_expression="Instalacion de Windows")
    after = parse_pricing_query("cuánto sale instalar Windows")

    assert after == before
