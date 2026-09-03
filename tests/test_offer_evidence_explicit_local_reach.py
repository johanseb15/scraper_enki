from src.infraestructura.offer_evidence_extractor import (
    extract_claims_from_explicit_basis,
)


def _values(claims, dimension):
    return {
        claim.value
        for claim in claims
        if claim.dimension == dimension
    }


def test_explicit_service_in_caba_is_named_area_reach_not_provider_location():
    raw_basis = (
        "Soporte Técnico de PC y Notebook en CABA"
    )

    claims = extract_claims_from_explicit_basis(
        observation_id="140",
        raw_basis=raw_basis,
        raw_document_id="sha256:fixture",
        provenance="fixture:taja-service-real-raw-language",
    )

    assert _values(
        claims,
        "geographic_reach",
    ) == {
        "NAMED_AREA:CABA",
    }

    # Merely naming a provider/location must remain insufficient.
    location_only = extract_claims_from_explicit_basis(
        observation_id="fixture-location-only",
        raw_basis="Taja Service - CABA",
        raw_document_id="sha256:fixture-location",
        provenance="fixture:provider-location-negative",
    )

    assert _values(
        location_only,
        "geographic_reach",
    ) == set()


def test_explicit_service_throughout_caba_is_named_area_reach():
    raw_basis = "Servicio en toda CABA"

    claims = extract_claims_from_explicit_basis(
        observation_id="115",
        raw_basis=raw_basis,
        raw_document_id="sha256:fixture-masterfix",
        provenance="fixture:masterfix-real-raw-language",
    )

    assert _values(
        claims,
        "geographic_reach",
    ) == {
        "NAMED_AREA:CABA",
    }


def test_location_or_shipping_in_caba_does_not_establish_service_reach():
    for raw_basis in (
        "TecnoSoluciones - CABA",
        "Oficina ubicada en CABA",
        "Envíos de productos en toda CABA",
    ):
        claims = extract_claims_from_explicit_basis(
            observation_id="fixture-negative",
            raw_basis=raw_basis,
            raw_document_id="sha256:fixture-negative",
            provenance="fixture:non-service-caba-negative",
        )

        assert _values(
            claims,
            "geographic_reach",
        ) == set()
