from decimal import Decimal
from src.aplicacion.pricing_evidence_engine import CohortePricing,evaluar_precio

def c(*,market="AR",service="SOPORTE_REMOTO",conf="MEDIUM",decision=True,range_ready=True):
    return CohortePricing(
        market=market,canonical_service=service,observations_n=5,providers_n=4,
        min_ars=Decimal("28000"),q1_ars=Decimal("30000"),median_ars=Decimal("35000"),
        q3_ars=Decimal("40000"),max_ars=Decimal("48000"),spread_ratio=Decimal("1.714"),
        evidence_confidence=conf,decision_ready=decision,range_ready=range_ready,
    )

def test_medium_below_q1_is_bajo():
    r=evaluar_precio([c()],market="AR",canonical_service="SOPORTE_REMOTO",proposed_price_ars=Decimal("29000"))
    assert r.status=="DECISION_READY" and r.decision_label=="BAJO"

def test_medium_iqr_is_razonable():
    r=evaluar_precio([c()],market="AR",canonical_service="SOPORTE_REMOTO",proposed_price_ars=Decimal("35000"))
    assert r.decision_label=="RAZONABLE"

def test_medium_above_q3_is_alto():
    r=evaluar_precio([c()],market="AR",canonical_service="SOPORTE_REMOTO",proposed_price_ars=Decimal("45000"))
    assert r.decision_label=="ALTO"

def test_low_confidence_withholds_decision():
    x=c(conf="LOW",decision=False)
    r=evaluar_precio([x],market="AR",canonical_service="SOPORTE_REMOTO",proposed_price_ars=Decimal("45000"))
    assert r.status=="RANGE_READY"
    assert r.decision_label is None
    assert r.price_position=="WITHIN_OBSERVED_RANGE"

def test_insufficient_withholds_everything():
    x=c(conf="INSUFFICIENT",decision=False,range_ready=False)
    r=evaluar_precio([x],market="AR",canonical_service="SOPORTE_REMOTO",proposed_price_ars=Decimal("45000"))
    assert r.status=="INSUFFICIENT_EVIDENCE"
    assert r.price_position is None
    assert r.decision_label is None

def test_market_mismatch_is_no_evidence():
    r=evaluar_precio([c()],market="Córdoba",canonical_service="SOPORTE_REMOTO")
    assert r.status=="NO_EVIDENCE"
