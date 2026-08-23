from __future__ import annotations

from decimal import Decimal

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing, evaluar_precio


def cohort(
    *,
    price_scope: str,
    commercial_context: str = "STANDARD",
    market: str = "AR",
    service: str = "SOPORTE_REMOTO",
    n: int = 3,
    providers: int = 3,
    min_: int = 28000,
    q1: int = 29000,
    median: int = 30000,
    q3: int = 35000,
    max_: int = 40000,
    confidence: str = "LOW",
    decision_ready: bool = False,
    range_ready: bool = True,
) -> CohortePricing:
    return CohortePricing(
        market=market,
        canonical_service=service,
        price_scope=price_scope,
        commercial_context=commercial_context,
        observations_n=n,
        providers_n=providers,
        min_ars=Decimal(str(min_)),
        q1_ars=Decimal(str(q1)),
        median_ars=Decimal(str(median)),
        q3_ars=Decimal(str(q3)),
        max_ars=Decimal(str(max_)),
        spread_ratio=Decimal(str(max_ / min_)),
        evidence_confidence=confidence,
        decision_ready=decision_ready,
        range_ready=range_ready,
    )


def test_evidence_engine_matches_price_scope_and_standard_context():
    hourly = cohort(price_scope="PER_HOUR")
    monthly = cohort(
        price_scope="PER_MONTH",
        n=1,
        providers=1,
        min_=90000,
        q1=90000,
        median=90000,
        q3=90000,
        max_=90000,
        confidence="INSUFFICIENT",
        range_ready=False,
    )

    r = evaluar_precio(
        [monthly, hourly],
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        price_scope="PER_HOUR",
        commercial_context="STANDARD",
        proposed_price_ars=Decimal("35000"),
    )

    assert r.status == "RANGE_READY"
    assert r.evidence_confidence == "LOW"
    assert r.observations_n == 3
    assert r.providers_n == 3
    assert r.median_ars == Decimal("30000")
    assert r.decision_label is None


def test_evidence_engine_does_not_fallback_from_monthly_to_hourly():
    hourly = cohort(price_scope="PER_HOUR")

    r = evaluar_precio(
        [hourly],
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        price_scope="PER_MONTH",
        commercial_context="STANDARD",
        proposed_price_ars=Decimal("35000"),
    )

    assert r.status == "NO_EVIDENCE"


def test_generic_remote_price_requires_cadence_clarification():
    hourly = cohort(price_scope="PER_HOUR")

    r = resolver_consulta_pricing(
        "me quieren cobrar 35 lucas por soporte remoto en horario habitual, está bien?",
        local_cohortes=(),
        remote_cohortes=[hourly],
    )

    assert r.status == "CLARIFICATION_REQUIRED"
    assert r.evidence is None
    assert r.clarification_reason == "PRICE_SCOPE_REQUIRED"
    assert r.clarification_question
    assert "hora" in r.clarification_question.lower()


def test_hourly_remote_query_uses_only_hourly_standard_cohort():
    hourly = cohort(price_scope="PER_HOUR")
    urgency = cohort(
        price_scope="PER_HOUR",
        commercial_context="URGENCY",
        n=1,
        providers=1,
        min_=48000,
        q1=48000,
        median=48000,
        q3=48000,
        max_=48000,
        confidence="INSUFFICIENT",
        range_ready=False,
    )

    r = resolver_consulta_pricing(
        "me quieren cobrar 35 lucas la hora por soporte remoto en horario habitual, está bien?",
        local_cohortes=(),
        remote_cohortes=[urgency, hourly],
    )

    assert r.status == "RANGE_READY"
    assert r.evidence is not None
    assert r.evidence.observations_n == 3
    assert r.evidence.providers_n == 3
    assert r.evidence.median_ars == Decimal("30000")
    assert r.decision_label is None


def test_monthly_remote_query_does_not_use_hourly_evidence():
    hourly = cohort(price_scope="PER_HOUR")

    r = resolver_consulta_pricing(
        "me quieren cobrar 35 lucas al mes por soporte remoto en horario habitual, está bien?",
        local_cohortes=(),
        remote_cohortes=[hourly],
    )

    assert r.status == "NO_EVIDENCE"
    assert r.evidence is not None
    assert r.decision_label is None


def test_standard_query_never_uses_urgency_cohort():
    urgency = cohort(
        price_scope="PER_HOUR",
        commercial_context="URGENCY",
        n=5,
        providers=4,
        min_=40000,
        q1=45000,
        median=48000,
        q3=52000,
        max_=60000,
        confidence="MEDIUM",
        decision_ready=True,
        range_ready=True,
    )

    r = resolver_consulta_pricing(
        "me quieren cobrar 35 lucas la hora por soporte remoto en horario habitual, está bien?",
        local_cohortes=(),
        remote_cohortes=[urgency],
    )

    assert r.status == "NO_EVIDENCE"
    assert r.decision_label is None
