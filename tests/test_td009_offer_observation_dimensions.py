from __future__ import annotations

from src.dominio.economic_evidence import (
    DimensionStatus,
    EconomicEvidenceDimensionsV2,
)
from src.dominio.offer_observation import (
    OfferObservation,
    PriceExpressionIdentity,
)
from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
)


def _price():
    return PriceExpressionIdentity(
        price_value="50000",
        currency="ARS",
        charged_unit=ChargedUnitMeaning.HOUR,
        billing_period=BillingPeriodMeaning.UNKNOWN,
        price_bound=PriceBoundMeaning.EXACT,
    )


def _dimensions():
    return EconomicEvidenceDimensionsV2()


def _observation(*, dimensions):
    return OfferObservation.create(
        source_observation_id="69",
        source_id="bairescloud_generic",
        logical_offer_key=(
            "generic:4:"
            "visita-a-domicilio-x-1-hs-pc-notebook-aio"
        ),
        raw_document_id="sha256:historical",
        raw_expression=(
            "Visita a domicilio x 1 HS PC-Notebook-AIO"
        ),
        price_expression=_price(),
        economic_dimensions=dimensions,
    )


def test_offer_observation_composes_economic_dimensions_v2():
    observation = _observation(
        dimensions=_dimensions(),
    )

    assert (
        observation.economic_dimensions
        is not None
    )
    assert isinstance(
        observation.economic_dimensions,
        EconomicEvidenceDimensionsV2,
    )


def test_offer_observation_dimension_shape_is_available_from_aggregate():
    observation = _observation(
        dimensions=_dimensions(),
    )

    assert set(
        observation.economic_dimensions.all_dimensions()
    ) == {
        "provider_identity",
        "price_scope",
        "currency",
        "delivery_mode",
        "geographic_reach",
        "location",
        "commercial_context",
        "bundle_status",
        "hardware_included",
        "materials_included",
        "device_scope",
    }


def test_offer_identity_does_not_depend_on_dimensions():
    first = _observation(
        dimensions=_dimensions(),
    )

    second = _observation(
        dimensions=EconomicEvidenceDimensionsV2(),
    )

    assert first.logical_offer_id == second.logical_offer_id
    assert (
        first.price_expression_id
        == second.price_expression_id
    )
    assert (
        first.snapshot_observation_id
        == second.snapshot_observation_id
    )


def test_aggregate_preserves_unknown_dimensions():
    observation = _observation(
        dimensions=_dimensions(),
    )

    assert (
        observation.economic_dimensions.delivery_mode.status
        is DimensionStatus.UNKNOWN
    )
    assert (
        observation.economic_dimensions.commercial_context.status
        is DimensionStatus.UNKNOWN
    )
    assert (
        observation.economic_dimensions.device_scope.status
        is DimensionStatus.UNKNOWN
    )
