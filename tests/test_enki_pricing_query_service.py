from decimal import Decimal
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing

def cohort(*,market="AR",service="SOPORTE_REMOTO",n=5,providers=4,min_=28000,q1=30000,median=35000,q3=40000,max_=48000,confidence="MEDIUM",decision_ready=True,range_ready=True,price_scope="UNKNOWN",commercial_context="STANDARD"):
    return CohortePricing(market=market,canonical_service=service,observations_n=n,providers_n=providers,min_ars=Decimal(str(min_)),q1_ars=Decimal(str(q1)),median_ars=Decimal(str(median)),q3_ars=Decimal(str(q3)),max_ars=Decimal(str(max_)),spread_ratio=Decimal(str(max_/min_)),evidence_confidence=confidence,decision_ready=decision_ready,range_ready=range_ready,price_scope=price_scope,commercial_context=commercial_context)

REMOTE=[cohort(price_scope="PER_HOUR")]
def resolve(text,local=(),remote=REMOTE): return resolver_consulta_pricing(text,local_cohortes=local,remote_cohortes=remote)

def test_remote_35k_hourly_is_reasonable_for_medium_fixture():
    r=resolve("me quieren cobrar 35 lucas la hora por soporte remoto, está bien?"); assert r.status=="DECISION_READY" and r.decision_label=="RAZONABLE"; assert r.evidence.observations_n==5 and r.evidence.providers_n==4

def test_remote_10k_hourly_is_low():
    r=resolve("me quieren cobrar 10 lucas la hora por soporte remoto, está bien?"); assert r.status=="DECISION_READY" and r.decision_label=="BAJO"; assert r.evidence.price_position=="BELOW_OBSERVED_RANGE"

def test_remote_60k_hourly_is_high():
    r=resolve("me quieren cobrar 60 lucas la hora por soporte remoto, está bien?"); assert r.status=="DECISION_READY" and r.decision_label=="ALTO"; assert r.evidence.price_position=="ABOVE_OBSERVED_RANGE"

def test_local_insufficient_never_emits_decision():
    local=[cohort(market="Córdoba",service="FORMATEO_INSTALACION_SO",n=3,providers=1,min_=45000,q1=50000,median=55000,q3=59500,max_=64000,confidence="INSUFFICIENT",decision_ready=False,range_ready=False,price_scope="UNKNOWN")]
    r=resolve("me quieren cobrar 55 lucas por formatear en Córdoba, está bien?",local=local); assert r.status=="INSUFFICIENT_EVIDENCE"; assert r.decision_label is None

def test_missing_local_province_requests_clarification():
    r=resolve("me quieren cobrar 55 lucas por formatear, está bien?"); assert r.status=="CLARIFICATION_REQUIRED" and r.evidence is None

def test_bundle_is_not_forced_into_one_cohort():
    r=resolve("me cobran 110 lucas por formateo y backup en Córdoba"); assert r.status=="UNSUPPORTED_QUERY" and r.unsupported_reason=="SINGLE_CANONICAL_SERVICE_REQUIRED" and r.evidence is None

def test_unknown_currency_does_not_reach_evidence():
    r=resolve("80 por soporte remoto está bien?"); assert r.status=="CLARIFICATION_REQUIRED" and r.evidence is None

def test_market_reference_hourly_returns_range_without_decision():
    remote=[cohort(n=3,providers=3,min_=28000,q1=29000,median=30000,q3=35000,max_=40000,confidence="LOW",decision_ready=False,range_ready=True,price_scope="PER_HOUR")]
    r=resolve("cuánto se está cobrando por hora por soporte remoto?",remote=remote); assert r.status=="RANGE_READY"; assert r.decision_label is None; assert r.evidence.median_ars==Decimal("30000")
