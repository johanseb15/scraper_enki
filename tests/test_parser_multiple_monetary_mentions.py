from decimal import Decimal

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_evidence_engine import CohortePricing


def hourly_remote_cohort() -> CohortePricing:
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


def test_mixed_currency_multiple_prices_requires_clarification():
    parsed = parse_pricing_query(
        "me cobran 50K la jornada más 10 USD por hora de soporte remoto"
    )

    assert parsed.metadata.clarification_required is True
    assert "MULTIPLE_MONETARY_MENTIONS" in (
        parsed.metadata.clarification_reason or ""
    )


def test_same_currency_independent_prices_requires_clarification():
    parsed = parse_pricing_query(
        "me cobran 15 lucas de viático más 20k por hora de soporte remoto"
    )

    assert parsed.metadata.clarification_required is True
    assert "MULTIPLE_MONETARY_MENTIONS" in (
        parsed.metadata.clarification_reason or ""
    )


def test_multiple_money_query_never_reaches_empirical_range():
    result = resolver_consulta_pricing(
        "me cobran 50K la jornada más 10 USD por hora de soporte remoto",
        local_cohortes=[],
        remote_cohortes=[hourly_remote_cohort()],
    )

    assert result.status == "CLARIFICATION_REQUIRED"
    assert result.evidence is None
    assert result.decision_label is None


def test_true_range_is_not_treated_as_multiple_independent_prices():
    parsed = parse_pricing_query(
        "me quieren cobrar entre 80 y 90k por armar una pc en Córdoba"
    )

    assert "MULTIPLE_MONETARY_MENTIONS" not in (
        parsed.metadata.clarification_reason or ""
    )
    assert parsed.price.type.value == "RANGE"
    assert parsed.price.min == 80000
    assert parsed.price.max == 90000


def test_single_price_plus_technical_number_is_not_multiple_money():
    parsed = parse_pricing_query(
        "me cobran 38k por hacer backup de 100GB"
    )

    assert "MULTIPLE_MONETARY_MENTIONS" not in (
        parsed.metadata.clarification_reason or ""
    )


def test_single_hourly_price_remains_valid():
    parsed = parse_pricing_query(
        "me quieren cobrar 35 lucas la hora por soporte remoto, está bien?"
    )

    assert parsed.metadata.clarification_required is False
    assert parsed.price.type.value == "PER_HOUR"
    assert parsed.price.value == 35000
