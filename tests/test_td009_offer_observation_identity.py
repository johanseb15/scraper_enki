from __future__ import annotations

import pytest

from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
)

from src.dominio.offer_observation import (
    OfferObservation,
    OfferObservationIdentityConflict,
    PriceExpressionIdentity,
)


def _observation(
    *,
    observation_id="62",
    source_id="bairescloud_generic",
    logical_offer_key="generic:4:backup-de-datos-cada-100gb-extras-pc-notebook-aio",
    raw_document_id="sha256:raw-a",
    price_value="38000",
    currency="ARS",
):
    return OfferObservation.create(
        source_observation_id=observation_id,
        source_id=source_id,
        logical_offer_key=logical_offer_key,
        raw_document_id=raw_document_id,
        raw_expression="BackUp de Datos cada 100gb Extras PC-Notebook-AIO",
        price_expression=PriceExpressionIdentity(
            price_value=price_value,
            currency=currency,
            charged_unit=ChargedUnitMeaning.UNIT,
            billing_period=BillingPeriodMeaning.UNKNOWN,
            price_bound=PriceBoundMeaning.EXACT,
        ),
    )


def test_logical_offer_identity_is_stable_across_raw_snapshots():
    first = _observation(raw_document_id="sha256:raw-a")
    second = _observation(raw_document_id="sha256:raw-b")

    assert first.logical_offer_id == second.logical_offer_id
    assert first.snapshot_observation_id != second.snapshot_observation_id


def test_price_expression_identity_separates_two_prices_in_same_offer_snapshot():
    first = _observation(
        raw_document_id="sha256:raw-a",
        price_value="38000",
    )
    second = _observation(
        raw_document_id="sha256:raw-a",
        price_value="50000",
    )

    assert first.logical_offer_id == second.logical_offer_id
    assert first.snapshot_observation_id != second.snapshot_observation_id
    assert first.price_expression_id != second.price_expression_id


def test_identical_semantics_are_deterministic():
    first = _observation()
    second = _observation()

    assert first.logical_offer_id == second.logical_offer_id
    assert first.snapshot_observation_id == second.snapshot_observation_id
    assert first.price_expression_id == second.price_expression_id


def test_source_observation_id_is_not_snapshot_identity():
    observation = _observation(
        observation_id="62",
        raw_document_id="sha256:raw-a",
    )

    assert observation.source_observation_id == "62"
    assert observation.snapshot_observation_id != "62"


def test_raw_snapshot_is_required_for_resolved_offer_observation():
    with pytest.raises(ValueError):
        _observation(raw_document_id="")


def test_unknown_logical_offer_key_does_not_fabricate_identity():
    with pytest.raises(ValueError):
        _observation(logical_offer_key="")


def test_conflicting_raw_snapshots_for_same_legacy_observation_are_detectable():
    first = _observation(
        observation_id="62",
        raw_document_id="sha256:historical-fixture",
    )
    second = _observation(
        observation_id="62",
        raw_document_id="sha256:reacquired-page",
    )

    with pytest.raises(OfferObservationIdentityConflict):
        OfferObservation.assert_legacy_identity_compatible(first, second)


def test_logical_offer_identity_does_not_depend_on_price():
    first = _observation(price_value="38000")
    second = _observation(price_value="42000")

    assert first.logical_offer_id == second.logical_offer_id


def test_price_expression_identity_includes_scope_semantics():
    base = _observation()

    other = OfferObservation.create(
        source_observation_id="62",
        source_id="bairescloud_generic",
        logical_offer_key="generic:4:backup-de-datos-cada-100gb-extras-pc-notebook-aio",
        raw_document_id="sha256:raw-a",
        raw_expression="BackUp de Datos cada 100gb Extras PC-Notebook-AIO",
        price_expression=PriceExpressionIdentity(
            price_value="38000",
            currency="ARS",
            charged_unit=ChargedUnitMeaning.HOUR,
            billing_period=BillingPeriodMeaning.UNKNOWN,
            price_bound=PriceBoundMeaning.EXACT,
        ),
    )

    assert base.price_expression_id != other.price_expression_id
