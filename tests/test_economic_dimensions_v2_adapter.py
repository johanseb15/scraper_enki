from src.dominio.economic_evidence import DimensionOrigin, DimensionStatus
from src.infraestructura.economic_dimensions_v2_adapter import (
    derive_economic_dimensions_v2,
)


def row(**overrides):
    base = {
        "observation_id": "1",
        "source": "provider_a_page_1",
        "economic_object_raw": "Soporte técnico",
        "price_value": "30000",
        "currency": "ARS",
        "province": "Córdoba",
        "city": "Córdoba",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "semantic_role": "SINGLE_SERVICE",
    }
    base.update(overrides)
    return base


def registry():
    return {
        "provider_a_page_1": {
            "source": "provider_a_page_1",
            "provider": "Provider A",
        }
    }


def test_remote_and_national_are_orthogonal_resolved_dimensions():
    dimensions = derive_economic_dimensions_v2(
        row(economic_object_raw="Soporte remoto en todo el país"), registry()
    )
    assert dimensions.delivery_mode.value == "REMOTE"
    assert dimensions.geographic_reach.value == "NATIONAL"
    assert dimensions.delivery_mode.status is DimensionStatus.OBSERVED
    assert dimensions.geographic_reach.status is DimensionStatus.OBSERVED
    assert not dimensions.conflicted_dimensions


def test_remote_does_not_imply_national_or_any_geographic_reach():
    dimensions = derive_economic_dimensions_v2(
        row(economic_object_raw="Soporte remoto", province="", city=""), registry()
    )
    assert dimensions.delivery_mode.value == "REMOTE"
    assert dimensions.geographic_reach.status is DimensionStatus.UNKNOWN


def test_national_does_not_imply_remote():
    dimensions = derive_economic_dimensions_v2(
        row(economic_object_raw="Cobertura nacional", province="", city=""), registry()
    )
    assert dimensions.geographic_reach.value == "NATIONAL"
    assert dimensions.delivery_mode.status is DimensionStatus.UNKNOWN


def test_onsite_and_normalized_location_coexist_without_conflation():
    dimensions = derive_economic_dimensions_v2(
        row(economic_object_raw="Visita a domicilio"), registry()
    )
    assert dimensions.delivery_mode.value == "ONSITE"
    assert dimensions.location.value.province == "Córdoba"
    assert dimensions.location.value.city == "Córdoba"
    assert dimensions.geographic_reach.status is DimensionStatus.UNKNOWN


def test_commercial_modifiers_are_compatible_multivalue_claims():
    after_hours = derive_economic_dimensions_v2(
        row(economic_object_raw="Urgencia fuera de horario"), registry()
    )
    weekend = derive_economic_dimensions_v2(
        row(economic_object_raw="Urgencias fines de semana y feriados"), registry()
    )
    assert after_hours.commercial_context.value == frozenset({"URGENCY", "AFTER_HOURS"})
    assert weekend.commercial_context.value == frozenset({"URGENCY", "WEEKEND_HOLIDAY"})
    assert after_hours.commercial_context.status is DimensionStatus.OBSERVED
    assert weekend.commercial_context.status is DimensionStatus.OBSERVED


def test_mutually_exclusive_commercial_claims_remain_real_ambiguity():
    dimensions = derive_economic_dimensions_v2(
        row(economic_object_raw="Tarifa estándar urgente"), registry()
    )
    assert dimensions.commercial_context.status is DimensionStatus.AMBIGUOUS
    assert dimensions.commercial_context.value is None


def test_claim_provenance_distinguishes_raw_normalized_registry_and_derived():
    dimensions = derive_economic_dimensions_v2(
        row(
            economic_object_raw="Soporte remoto por hora ARS, hardware incluido",
            extractor_version="v1",
        ),
        registry(),
    )
    assert dimensions.delivery_mode.claims[0].origin is DimensionOrigin.RAW_SOURCE_OBSERVATION
    assert dimensions.price_scope.claims[0].origin is DimensionOrigin.RAW_SOURCE_OBSERVATION
    assert dimensions.location.claims[0].origin is DimensionOrigin.NORMALIZED_FIELD
    assert dimensions.currency.claims[0].origin is DimensionOrigin.NORMALIZED_FIELD
    assert dimensions.provider_identity.claims[0].origin is DimensionOrigin.REGISTRY_CLAIM
    assert dimensions.bundle_status.claims[0].origin is DimensionOrigin.DERIVED_CLAIM
    assert dimensions.delivery_mode.claims[0].provenance.origin_version == "v1"
    assert dimensions.location.claims[0].provenance.origin_version == "semantic-normalization-v4"


def test_true_cadence_conflict_is_preserved():
    dimensions = derive_economic_dimensions_v2(
        row(economic_object_raw="Soporte por hora", price_scope="PER_MONTH"), registry()
    )
    assert dimensions.price_scope.status is DimensionStatus.CONFLICTED
    assert {claim.value for claim in dimensions.price_scope.claims} == {
        "PER_HOUR",
        "PER_MONTH",
    }


def test_unknown_dimensions_receive_no_defaults():
    dimensions = derive_economic_dimensions_v2(
        row(
            economic_object_raw="Servicio técnico",
            currency="",
            province="",
            city="",
            market_scope="UNKNOWN",
            semantic_role="UNMAPPED",
        ),
        {},
    )
    assert dimensions.provider_identity.status is DimensionStatus.UNKNOWN
    assert dimensions.currency.status is DimensionStatus.UNKNOWN
    assert dimensions.delivery_mode.status is DimensionStatus.UNKNOWN
    assert dimensions.geographic_reach.status is DimensionStatus.UNKNOWN
    assert dimensions.location.status is DimensionStatus.UNKNOWN
    assert dimensions.commercial_context.status is DimensionStatus.UNKNOWN
