from decimal import Decimal

from fastapi.testclient import TestClient

from src.api.main import app, obtener_cohortes_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing


client = TestClient(app)


def _remote_hourly_cohort() -> CohortePricing:
    return CohortePricing(
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        observations_n=3,
        providers_n=3,
        min_ars=Decimal("28000"),
        q1_ars=Decimal("29000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("35000"),
        max_ars=Decimal("40000"),
        spread_ratio=Decimal("1.428571"),
        evidence_confidence="LOW",
        decision_ready=False,
        range_ready=True,
        price_scope="PER_HOUR",
        commercial_context="STANDARD",
    )


def _override_cohortes():
    return [], [_remote_hourly_cohort()]


def test_decision_pricing_returns_real_range_payload():
    app.dependency_overrides[obtener_cohortes_pricing] = _override_cohortes
    try:
        response = client.post(
            "/decision/pricing",
            json={"query": "me quieren cobrar 35 lucas la hora por soporte remoto, está bien?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RANGE_READY"
    assert body["headline"] == "Rango de mercado disponible"
    assert body["parsed"]["canonical_services"] == ["SOPORTE_REMOTO"]
    assert body["parsed"]["price"]["value"] == 35000
    assert body["parsed"]["price"]["type"] == "PER_HOUR"
    assert body["evidence"]["min_ars"] == 28000
    assert body["evidence"]["median_ars"] == 30000
    assert body["evidence"]["max_ars"] == 40000
    assert body["evidence"]["observations_n"] == 3
    assert body["evidence"]["providers_n"] == 3
    assert body["evidence"]["evidence_confidence"] == "LOW"
    assert body["evidence"]["price_scope"] == "PER_HOUR"


def test_decision_pricing_returns_clarification_payload():
    app.dependency_overrides[obtener_cohortes_pricing] = _override_cohortes
    try:
        response = client.post(
            "/decision/pricing",
            json={"query": "me quieren cobrar 35 lucas por soporte remoto, está bien?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CLARIFICATION_REQUIRED"
    assert body["headline"] == "Necesito una aclaración"
    assert body["clarification_reason"] == "PRICE_SCOPE_REQUIRED"
    assert "hora" in body["clarification_question"].lower()
    assert body["evidence"] is None


def test_decision_pricing_rejects_empty_query():
    response = client.post("/decision/pricing", json={"query": ""})
    assert response.status_code == 422
