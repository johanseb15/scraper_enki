from src.dominio.economic_evidence import DimensionStatus
from src.infraestructura.economic_dimensions_adapter import derive_economic_dimensions


def row(**overrides):
    base = {
        "observation_id": "1",
        "source": "provider_a_page_1",
        "economic_object_raw": "Soporte técnico",
        "price_value": "30000",
        "currency": "ARS",
        "province": "",
        "city": "",
        "market_scope": "UNKNOWN",
        "semantic_role": "SINGLE_SERVICE",
    }
    base.update(overrides)
    return base


def registry(provider="Provider A"):
    return {
        "provider_a_page_1": {
            "source": "provider_a_page_1",
            "provider": provider,
            "url": "https://example.test/prices",
        }
    }


def test_provider_identity_is_deterministic_across_runs_and_source_url_independent():
    first = derive_economic_dimensions(row(), registry())
    second = derive_economic_dimensions(row(), registry())

    assert first.provider_identity == second.provider_identity
    assert first.provider_identity.value.provider_id == "provider:provider-a"
    assert first.provider_identity.status is DimensionStatus.INFERRED


def test_unknown_provider_is_not_fabricated():
    dimensions = derive_economic_dimensions(row(source="unregistered"), registry())

    assert dimensions.provider_identity.status is DimensionStatus.UNKNOWN
    assert dimensions.provider_identity.value is None


def test_explicit_hour_month_and_absent_cadence_are_distinguished():
    hourly = derive_economic_dimensions(row(economic_object_raw="Soporte por hora"), registry())
    monthly = derive_economic_dimensions(row(economic_object_raw="Abono mensual"), registry())
    absent = derive_economic_dimensions(row(economic_object_raw="Soporte técnico"), registry())

    assert hourly.price_scope.value == "PER_HOUR"
    assert hourly.price_scope.status is DimensionStatus.OBSERVED
    assert monthly.price_scope.value == "PER_MONTH"
    assert absent.price_scope.status is DimensionStatus.UNKNOWN


def test_explicit_price_scope_conflicting_with_normalized_column_is_preserved():
    dimensions = derive_economic_dimensions(
        row(economic_object_raw="Soporte por hora", price_scope="PER_MONTH"), registry()
    )

    assert dimensions.price_scope.status is DimensionStatus.CONFLICTED
    assert {claim.value for claim in dimensions.price_scope.claims} == {"PER_HOUR", "PER_MONTH"}


def test_currency_markers_are_observed_and_never_converted():
    ars = derive_economic_dimensions(row(economic_object_raw="ARS 30.000", currency="ARS"), registry())
    usd = derive_economic_dimensions(row(economic_object_raw="USD 30", currency="USD"), registry())
    conflict = derive_economic_dimensions(row(economic_object_raw="USD 30", currency="ARS"), registry())

    assert ars.currency.value == "ARS"
    assert usd.currency.value == "USD"
    assert conflict.currency.status is DimensionStatus.CONFLICTED
    assert {claim.value for claim in conflict.currency.claims} == {"ARS", "USD"}


def test_geography_has_no_default_and_remote_does_not_invent_province():
    local = derive_economic_dimensions(row(province="Córdoba", city="Córdoba"), registry())
    remote = derive_economic_dimensions(row(economic_object_raw="Soporte remoto"), registry())
    unknown = derive_economic_dimensions(row(), registry())

    assert local.geography.value.province == "Córdoba"
    assert remote.geography.value.coverage == "REMOTE"
    assert remote.geography.value.province is None
    assert unknown.geography.status is DimensionStatus.UNKNOWN


def test_every_inferred_dimension_has_provenance():
    dimensions = derive_economic_dimensions(row(), registry())

    for dimension in dimensions.all_dimensions().values():
        for claim in dimension.claims:
            if claim.origin.value == "INFERRED":
                assert claim.provenance is not None
                assert claim.raw_basis
