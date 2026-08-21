from decimal import Decimal

from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.aplicacion.technical_need_evidence_probe import (
    probe_pricing_evidence,
    probe_technical_need_evidence,
)
from src.aplicacion.technical_need_market_resolution import (
    TechnicalNeedPricingReadiness,
    TechnicalRoutePricingReadiness,
)


def cohort(*,market="Córdoba",service="FORMATEO_INSTALACION_SO",n=5,providers=3,confidence="MEDIUM",range_ready=True,decision_ready=False):
    return CohortePricing(
        market=market,
        canonical_service=service,
        observations_n=n,
        providers_n=providers,
        min_ars=Decimal("45000"),
        q1_ars=Decimal("50000"),
        median_ars=Decimal("55000"),
        q3_ars=Decimal("60000"),
        max_ars=Decimal("70000"),
        spread_ratio=Decimal("1.555"),
        evidence_confidence=confidence,
        decision_ready=decision_ready,
        range_ready=range_ready,
    )


def ready(route="OS_INSTALLATION_SERVICE",service="FORMATEO_INSTALACION_SO",market="Córdoba"):
    return TechnicalRoutePricingReadiness(
        route=route,
        status="READY_FOR_PRICING",
        ready=True,
        canonical_service=service,
        market_scope="LOCAL",
        market=market,
        market_key=f"{market}::{service}",
    )


def blocked(route="OS_INSTALLATION_SERVICE",status="MISSING_PROVINCE"):
    return TechnicalRoutePricingReadiness(
        route=route,
        status=status,
        ready=False,
        canonical_service="FORMATEO_INSTALACION_SO" if status != "UNRESOLVED_ROUTE" else None,
        market_scope="LOCAL" if status != "UNRESOLVED_ROUTE" else None,
    )


def test_ready_route_with_existing_evidence_reports_evidence_available_without_decision():
    result=probe_pricing_evidence(ready(), local_cohortes=[cohort()], remote_cohortes=[])

    assert result.status=="EVIDENCE_AVAILABLE"
    assert result.route=="OS_INSTALLATION_SERVICE"
    assert result.market=="Córdoba"
    assert result.canonical_service=="FORMATEO_INSTALACION_SO"
    assert result.observations_n==5
    assert result.providers_n==3
    assert result.evidence_confidence=="MEDIUM"
    assert result.observed_min==Decimal("45000")
    assert result.observed_max==Decimal("70000")
    assert result.median==Decimal("55000")
    assert not hasattr(result,"decision_label")
    assert not hasattr(result,"recommendation")
    assert not hasattr(result,"suggested_product")
    assert not hasattr(result,"diagnosis")


def test_ready_route_without_matching_evidence_reports_no_evidence():
    result=probe_pricing_evidence(ready(market="Mendoza"), local_cohortes=[cohort()], remote_cohortes=[])

    assert result.status=="NO_EVIDENCE"
    assert result.market=="Mendoza"
    assert result.canonical_service=="FORMATEO_INSTALACION_SO"
    assert result.observations_n==0
    assert result.providers_n==0


def test_ready_route_with_insufficient_engine_result_preserves_insufficient_evidence():
    result=probe_pricing_evidence(
        ready(route="DIAGNOSTIC_SERVICE",service="DIAGNOSTICO_REVISION"),
        local_cohortes=[cohort(service="DIAGNOSTICO_REVISION",n=1,providers=1,confidence="INSUFFICIENT",range_ready=False)],
        remote_cohortes=[],
    )

    assert result.status=="INSUFFICIENT_EVIDENCE"
    assert result.route=="DIAGNOSTIC_SERVICE"
    assert result.canonical_service=="DIAGNOSTICO_REVISION"
    assert result.observations_n==1
    assert result.providers_n==1
    assert result.evidence_confidence=="INSUFFICIENT"


def test_missing_province_route_is_not_probed():
    result=probe_pricing_evidence(blocked("OS_INSTALLATION_SERVICE","MISSING_PROVINCE"), local_cohortes=[cohort()], remote_cohortes=[])

    assert result.status=="NOT_PROBED"
    assert result.reason=="MISSING_PROVINCE"
    assert result.observations_n==0


def test_unresolved_hardware_route_is_not_probed():
    result=probe_pricing_evidence(blocked("HARDWARE_DIAGNOSTIC","UNRESOLVED_ROUTE"), local_cohortes=[cohort()], remote_cohortes=[])

    assert result.status=="NOT_PROBED"
    assert result.reason=="UNRESOLVED_ROUTE"
    assert result.canonical_service is None


def test_probe_collection_only_executes_ready_routes():
    readiness=TechnicalNeedPricingReadiness(
        routes=(ready(), blocked("HARDWARE_DIAGNOSTIC","UNRESOLVED_ROUTE")),
        ready_routes=(ready(),),
        blocked_routes=(blocked("HARDWARE_DIAGNOSTIC","UNRESOLVED_ROUTE"),),
    )

    result=probe_technical_need_evidence(readiness, local_cohortes=[cohort()], remote_cohortes=[])

    assert [item.route for item in result.probes]==["OS_INSTALLATION_SERVICE","HARDWARE_DIAGNOSTIC"]
    by_route={item.route: item for item in result.probes}
    assert by_route["OS_INSTALLATION_SERVICE"].status=="EVIDENCE_AVAILABLE"
    assert by_route["HARDWARE_DIAGNOSTIC"].status=="NOT_PROBED"
