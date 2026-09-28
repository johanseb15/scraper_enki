from decimal import Decimal

import pytest

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_evidence_engine import CohortePricing, evaluar_precio
from src.dominio.commercial_context import (
    CommercialContext,
    CommercialContextOrigin,
    CommercialContextValue,
    PartsScope,
)


def test_current_ssd_offer_includes_part_despite_historical_labor_only():
    query = (
        "Tengo una PC cuyo arreglo anterior fue solo mano de obra. "
        "Ahora me cobran $50.000 por cambiar el SSD e incluye el repuesto en Córdoba"
    )

    parsed = parse_pricing_query(query)

    assert parsed.raw_text == query
    assert parsed.canonical_services == ("UPGRADE_HARDWARE",)
    assert parsed.commercial_context.parts_scope is PartsScope.PARTS_INCLUDED


@pytest.mark.parametrize(
    ("query", "expected"),
    (
        (
            "Me cobran $50.000 solo de mano de obra para cambiar el SSD",
            PartsScope.LABOR_ONLY,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD e incluye el repuesto",
            PartsScope.PARTS_INCLUDED,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD, yo pongo el repuesto",
            PartsScope.USER_PROVIDED,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD, solo mano de obra e incluye el repuesto",
            PartsScope.UNKNOWN,
        ),
        (
            "El arreglo anterior incluía el repuesto. Ahora me cobran $50.000 "
            "solo mano de obra por cambiar el SSD",
            PartsScope.LABOR_ONLY,
        ),
        (
            "El arreglo anterior fue solo mano de obra. Ahora me cobran $50.000 "
            "por cambiar el SSD e incluye el repuesto",
            PartsScope.PARTS_INCLUDED,
        ),
        (
            "El arreglo anterior fue solo mano de obra pero ahora me cobran "
            "$50.000 por cambiar el SSD e incluye el repuesto",
            PartsScope.PARTS_INCLUDED,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD. Incluye el repuesto.",
            PartsScope.PARTS_INCLUDED,
        ),
        (
            "El arreglo anterior fue solo mano de obra, pero actualmente me "
            "cobran $50.000 por cambiar el SSD e incluye el repuesto",
            PartsScope.PARTS_INCLUDED,
        ),
        (
            "El arreglo anterior fue solo mano de obra; hoy me cobran "
            "$50.000 por cambiar el SSD e incluye el repuesto",
            PartsScope.PARTS_INCLUDED,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD y no incluye el repuesto",
            PartsScope.LABOR_ONLY,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD y no me incluye el repuesto",
            PartsScope.LABOR_ONLY,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD y no se incluye el repuesto",
            PartsScope.LABOR_ONLY,
        ),
        (
            "Me cobran $50.000 por cambiar el SSD y no va sin repuesto",
            PartsScope.UNKNOWN,
        ),
    ),
)
def test_parts_scope_belongs_to_current_offer(query, expected):
    parsed = parse_pricing_query(query)

    assert parsed.commercial_context.parts_scope is expected
    if expected is PartsScope.UNKNOWN:
        assert parsed.metadata.clarification_required is True
        assert "UNKNOWN_PARTS_SCOPE" in (parsed.metadata.clarification_reason or "")


def test_parts_incompatible_cohort_cannot_support_decision():
    cohort = CohortePricing(
        market="Córdoba",
        canonical_service="UPGRADE_HARDWARE",
        observations_n=5,
        providers_n=4,
        min_ars=Decimal("20000"),
        q1_ars=Decimal("25000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("40000"),
        max_ars=Decimal("45000"),
        spread_ratio=Decimal("2.25"),
        evidence_confidence="MEDIUM",
        decision_ready=True,
        range_ready=True,
        price_scope="PER_VISIT",
        commercial_context=CommercialContext(
            value=CommercialContextValue.STANDARD,
            origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
            parts_scope=PartsScope.LABOR_ONLY,
        ),
    )
    query_context = CommercialContext(
        value=CommercialContextValue.STANDARD,
        origin=CommercialContextOrigin.USER_CLAIM,
        parts_scope=PartsScope.PARTS_INCLUDED,
    )

    result = evaluar_precio(
        (cohort,),
        market="Córdoba",
        canonical_service="UPGRADE_HARDWARE",
        proposed_price_ars=Decimal("50000"),
        price_scope="PER_VISIT",
        commercial_context=query_context,
    )

    assert result.status == "NO_EVIDENCE"
    assert result.decision_label is None


def test_query_service_rejects_labor_only_cohort_for_current_included_offer():
    cohort = CohortePricing(
        market="Córdoba",
        canonical_service="UPGRADE_HARDWARE",
        observations_n=5,
        providers_n=4,
        min_ars=Decimal("20000"),
        q1_ars=Decimal("25000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("40000"),
        max_ars=Decimal("45000"),
        spread_ratio=Decimal("2.25"),
        evidence_confidence="MEDIUM",
        decision_ready=True,
        range_ready=True,
        price_scope="PER_VISIT",
        commercial_context=CommercialContext(
            value=CommercialContextValue.STANDARD,
            origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
            parts_scope=PartsScope.LABOR_ONLY,
        ),
    )
    query = (
        "El arreglo anterior fue solo mano de obra. Ahora me cobran $50.000 "
        "por visita para cambiar el SSD e incluye el repuesto en Córdoba "
        "en horario habitual"
    )

    result = resolver_consulta_pricing(
        query,
        local_cohortes=(cohort,),
        remote_cohortes=(),
    )

    assert result.parsed.commercial_context.parts_scope is PartsScope.PARTS_INCLUDED
    assert result.status == "NO_EVIDENCE"
    assert result.decision_label is None


@pytest.mark.parametrize(
    "cohort_scope",
    (PartsScope.UNKNOWN, PartsScope.LABOR_ONLY, PartsScope.USER_PROVIDED),
)
def test_sensitive_service_rejects_unknown_or_different_parts(cohort_scope):
    cohort = CohortePricing(
        market="CABA",
        canonical_service="REPARACION_HARDWARE",
        observations_n=5,
        providers_n=4,
        min_ars=Decimal("20000"),
        q1_ars=Decimal("25000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("40000"),
        max_ars=Decimal("45000"),
        spread_ratio=Decimal("2.25"),
        evidence_confidence="MEDIUM",
        decision_ready=True,
        range_ready=True,
        price_scope="PER_VISIT",
        commercial_context=CommercialContext(
            value=CommercialContextValue.STANDARD,
            origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
            parts_scope=cohort_scope,
        ),
    )
    query_context = CommercialContext(
        value=CommercialContextValue.STANDARD,
        origin=CommercialContextOrigin.USER_CLAIM,
        parts_scope=PartsScope.PARTS_INCLUDED,
    )

    result = evaluar_precio(
        (cohort,),
        market="CABA",
        canonical_service="REPARACION_HARDWARE",
        proposed_price_ars=Decimal("50000"),
        price_scope="PER_VISIT",
        commercial_context=query_context,
    )

    assert result.status == "NO_EVIDENCE"
    assert result.decision_label is None


def test_non_sensitive_service_does_not_filter_on_parts_scope():
    cohort = CohortePricing(
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        observations_n=5,
        providers_n=4,
        min_ars=Decimal("20000"),
        q1_ars=Decimal("25000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("40000"),
        max_ars=Decimal("45000"),
        spread_ratio=Decimal("2.25"),
        evidence_confidence="MEDIUM",
        decision_ready=True,
        range_ready=True,
        price_scope="PER_HOUR",
        commercial_context=CommercialContext(
            value=CommercialContextValue.STANDARD,
            origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
            parts_scope=PartsScope.UNKNOWN,
        ),
    )
    query_context = CommercialContext(
        value=CommercialContextValue.STANDARD,
        origin=CommercialContextOrigin.USER_CLAIM,
        parts_scope=PartsScope.PARTS_INCLUDED,
    )

    result = evaluar_precio(
        (cohort,),
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        proposed_price_ars=Decimal("30000"),
        price_scope="PER_HOUR",
        commercial_context=query_context,
    )

    assert result.status == "DECISION_READY"
    assert result.decision_label == "RAZONABLE"


def test_sensitive_service_rejects_colliding_cohort_identities():
    def cohort(parts_scope):
        return CohortePricing(
            market="CABA",
            canonical_service="REPARACION_HARDWARE",
            observations_n=5,
            providers_n=4,
            min_ars=Decimal("20000"),
            q1_ars=Decimal("25000"),
            median_ars=Decimal("30000"),
            q3_ars=Decimal("40000"),
            max_ars=Decimal("45000"),
            spread_ratio=Decimal("2.25"),
            evidence_confidence="MEDIUM",
            decision_ready=True,
            range_ready=True,
            price_scope="PER_VISIT",
            commercial_context=CommercialContext(
                value=CommercialContextValue.STANDARD,
                origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
                parts_scope=parts_scope,
            ),
        )

    included = cohort(PartsScope.PARTS_INCLUDED)
    labor_only = cohort(PartsScope.LABOR_ONLY)
    query_context = CommercialContext(
        value=CommercialContextValue.STANDARD,
        origin=CommercialContextOrigin.USER_CLAIM,
        parts_scope=PartsScope.PARTS_INCLUDED,
    )
    assert included.evidence_id == labor_only.evidence_id

    result = evaluar_precio(
        (included, labor_only),
        market="CABA",
        canonical_service="REPARACION_HARDWARE",
        proposed_price_ars=Decimal("30000"),
        price_scope="PER_VISIT",
        commercial_context=query_context,
    )

    assert result.status == "NO_EVIDENCE"
    assert result.decision_label is None
