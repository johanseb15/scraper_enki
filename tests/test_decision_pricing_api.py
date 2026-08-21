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


def _local_technical_need_cohorts() -> list[CohortePricing]:
    return [
        CohortePricing(
            market="Córdoba",
            canonical_service="FORMATEO_INSTALACION_SO",
            observations_n=5,
            providers_n=3,
            min_ars=Decimal("45000"),
            q1_ars=Decimal("50000"),
            median_ars=Decimal("55000"),
            q3_ars=Decimal("60000"),
            max_ars=Decimal("70000"),
            spread_ratio=Decimal("1.555"),
            evidence_confidence="MEDIUM",
            decision_ready=False,
            range_ready=True,
        ),
        CohortePricing(
            market="Córdoba",
            canonical_service="DIAGNOSTICO_REVISION",
            observations_n=1,
            providers_n=1,
            min_ars=Decimal("20000"),
            q1_ars=Decimal("22000"),
            median_ars=Decimal("24000"),
            q3_ars=Decimal("26000"),
            max_ars=Decimal("28000"),
            spread_ratio=Decimal("1.4"),
            evidence_confidence="INSUFFICIENT",
            decision_ready=False,
            range_ready=False,
        ),
    ]


def _override_cohortes():
    return [], [_remote_hourly_cohort()]


def _override_technical_need_cohortes():
    return _local_technical_need_cohorts(), [_remote_hourly_cohort()]


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


def test_decision_pricing_returns_technical_need_payload():
    app.dependency_overrides[obtener_cohortes_pricing] = _override_cohortes
    try:
        response = client.post(
            "/decision/pricing",
            json={"query": "Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "TECHNICAL_NEED_ROUTED"
    assert body["evidence"] is None
    assert body["parsed"]["query_kind"] == "TECHNICAL_NEED"
    assert body["parsed"]["technical_need"] == {
        "domain": "PC",
        "technical_problem": "OS_INSTALLATION_FAILURE",
        "economic_intent_explicit": False,
        "candidate_routes": [
            "DIAGNOSTIC_SERVICE",
            "OS_INSTALLATION_SERVICE",
            "HARDWARE_DIAGNOSTIC",
        ],
        "product_purchase_recommendation": "NONE_YET",
        "clarification_required": True,
    }
    assert body["market_resolution"]["clarification_required"] is True
    assert body["market_resolution"]["clarification_reason"] == "MISSING_PROVINCE_FOR_LOCAL_MARKET"
    resolved = {
        item["route"]: item
        for item in body["market_resolution"]["resolutions"]
        if item["status"] == "RESOLVED"
    }
    assert resolved["OS_INSTALLATION_SERVICE"]["canonical_service"] == "FORMATEO_INSTALACION_SO"
    assert resolved["DIAGNOSTIC_SERVICE"]["canonical_service"] == "DIAGNOSTICO_REVISION"
    unresolved = {
        item["route"]: item
        for item in body["market_resolution"]["resolutions"]
        if item["status"] == "UNRESOLVED"
    }
    assert unresolved["HARDWARE_DIAGNOSTIC"]["canonical_service"] is None
    readiness = {
        item["route"]: item
        for item in body["pricing_readiness"]["routes"]
    }
    assert readiness["OS_INSTALLATION_SERVICE"]["status"] == "MISSING_PROVINCE"
    assert readiness["OS_INSTALLATION_SERVICE"]["ready"] is False
    assert readiness["DIAGNOSTIC_SERVICE"]["status"] == "MISSING_PROVINCE"
    assert readiness["HARDWARE_DIAGNOSTIC"]["status"] == "UNRESOLVED_ROUTE"
    assert body["pricing_readiness"]["ready_routes"] == []
    probe={item["route"]: item for item in body["evidence_probe"]["probes"]}
    assert probe["OS_INSTALLATION_SERVICE"]["status"] == "NOT_PROBED"
    assert probe["DIAGNOSTIC_SERVICE"]["status"] == "NOT_PROBED"
    assert probe["HARDWARE_DIAGNOSTIC"]["status"] == "NOT_PROBED"



def test_decision_pricing_technical_need_with_province_has_readiness_but_no_evidence():
    app.dependency_overrides[obtener_cohortes_pricing] = _override_technical_need_cohortes
    try:
        response = client.post(
            "/decision/pricing",
            json={"query": "Estoy instalando Windows 11 y se queda congelado en 10% en Córdoba. ¿Qué puede estar pasando?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "TECHNICAL_NEED_ROUTED"
    assert body["evidence"] is None
    readiness = {
        item["route"]: item
        for item in body["pricing_readiness"]["routes"]
    }
    assert readiness["OS_INSTALLATION_SERVICE"]["status"] == "READY_FOR_PRICING"
    assert readiness["OS_INSTALLATION_SERVICE"]["market_key"] == "Córdoba::FORMATEO_INSTALACION_SO"
    assert readiness["OS_INSTALLATION_SERVICE"]["pricing_status"] is None
    assert readiness["DIAGNOSTIC_SERVICE"]["status"] == "READY_FOR_PRICING"
    assert readiness["HARDWARE_DIAGNOSTIC"]["status"] == "UNRESOLVED_ROUTE"
    probe={item["route"]: item for item in body["evidence_probe"]["probes"]}
    assert probe["OS_INSTALLATION_SERVICE"]["status"] == "EVIDENCE_AVAILABLE"
    assert probe["OS_INSTALLATION_SERVICE"]["observations_n"] == 5
    assert probe["OS_INSTALLATION_SERVICE"]["providers_n"] == 3
    assert probe["OS_INSTALLATION_SERVICE"]["evidence_confidence"] == "MEDIUM"
    assert probe["OS_INSTALLATION_SERVICE"]["observed_min"] == 45000
    assert probe["OS_INSTALLATION_SERVICE"]["observed_max"] == 70000
    assert probe["OS_INSTALLATION_SERVICE"]["median"] == 55000
    assert probe["DIAGNOSTIC_SERVICE"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert probe["HARDWARE_DIAGNOSTIC"]["status"] == "NOT_PROBED"
    assert "decision_label" not in probe["OS_INSTALLATION_SERVICE"]
    assert "recommendation" not in probe["OS_INSTALLATION_SERVICE"]
    assert "suggested_product" not in probe["OS_INSTALLATION_SERVICE"]
    assert "diagnosis" not in probe["OS_INSTALLATION_SERVICE"]
