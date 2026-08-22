from pathlib import Path

import pytest

from src.dominio.offer_evidence import SourceClaimMethod
from src.infraestructura.offer_evidence_extractor import (
    extract_claims_from_explicit_basis,
)


def extract(text: str):
    return extract_claims_from_explicit_basis(
        observation_id="1",
        raw_basis=text,
        raw_document_id="sha256:abc",
        provenance="tests/fixtures/real.html",
    )


def values(text: str, dimension: str) -> set[str]:
    return {claim.value for claim in extract(text) if claim.dimension == dimension}


def test_remote_does_not_imply_national_reach():
    assert values("Servicio remoto", "delivery_mode") == {"REMOTE"}
    assert values("Servicio remoto", "geographic_reach") == set()


def test_explicit_remote_service_national_reach():
    claims = extract("Servicio remoto con cobertura en todo el país")
    assert {c.value for c in claims if c.dimension == "delivery_mode"} == {"REMOTE"}
    assert {c.value for c in claims if c.dimension == "geographic_reach"} == {"NATIONAL"}


def test_product_shipping_does_not_imply_service_reach():
    assert values("Enviamos por correo argentino a todo el país", "geographic_reach") == set()


def test_provider_location_does_not_imply_reach():
    assert values("Estamos en Córdoba Capital", "geographic_reach") == set()


def test_published_service_area_produces_reach():
    assert values("Zona de atención: provincia de Córdoba", "geographic_reach") == {"PROVINCE:Córdoba"}


def test_multiple_compatible_named_areas_coexist_in_one_claim():
    assert values("Zona de atención: Córdoba Capital y Rosario", "geographic_reach") == {
        "NAMED_AREAS:Cordoba Capital|Rosario"
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Soporte por hora", "HOUR"),
        ("Hora adicional", "HOUR"),
        ("Servicio por visita", "VISIT"),
        ("Precio por equipo", "UNIT"),
        ("Abono mensual", "MONTH"),
        ("Implementación por proyecto", "PROJECT"),
    ],
)
def test_charged_units_are_explicit(text, expected):
    assert values(text, "charged_unit") == {expected}


@pytest.mark.parametrize("text", ["Desde $30.000", "A partir de $30.000"])
def test_lower_bound_is_preserved(text):
    assert values(text, "price_bound") == {"LOWER_BOUND"}


def test_price_without_unit_or_bound_gets_no_default():
    claims = extract("Reparación $30.000")
    assert not {c for c in claims if c.dimension in {"charged_unit", "price_bound"}}


def test_quote_required_is_not_exact():
    assert values("Presupuesto a consultar", "price_bound") == {"QUOTE_REQUIRED"}


def test_travel_is_a_qualifier_not_a_service_or_charged_unit():
    claims = extract("Viáticos y traslado fuera de zona")
    assert {c.value for c in claims if c.dimension == "travel_restriction"} == {
        "TRAVEL_EXPENSES", "TRAVEL", "DISTANCE_RESTRICTION"
    }
    assert not {c for c in claims if c.dimension == "charged_unit"}


def test_raw_basis_and_raw_provenance_are_preserved():
    claim = extract("Conexión Remota x 1 HS")[0]
    assert claim.raw_basis == "Conexión Remota x 1 HS"
    assert claim.raw_document_id == "sha256:abc"
    assert claim.provenance == "tests/fixtures/real.html"
    assert claim.extraction_method is SourceClaimMethod.DERIVED_FROM_SOURCE_TEXT


def test_real_bitz_fixture_contains_audited_patterns():
    text = (Path(__file__).parent / "fixtures/bitz_tarifas_servicio_tecnico.html").read_text(
        encoding="utf-8"
    )
    assert "Servicio realizado a distancia" in text
    assert "Precios por equipo" in text


def test_real_baires_fixture_expression_is_extracted_conservatively():
    claims = extract("Conexión Remota x 1 HS PC-Notebook-AIO")
    assert {(c.dimension, c.value) for c in claims} == {
        ("delivery_mode", "REMOTE"),
        ("charged_unit", "HOUR"),
    }
