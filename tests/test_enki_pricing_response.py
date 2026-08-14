from decimal import Decimal
from types import SimpleNamespace

from src.aplicacion.enki_pricing_response import presentar_resultado_pricing
from src.aplicacion.pricing_evidence_engine import ResultadoEvidenciaPrecio


def result(status, evidence=None, **kwargs):
    return SimpleNamespace(
        status=status,
        evidence=evidence,
        clarification_question=kwargs.get("clarification_question"),
        clarification_reason=kwargs.get("clarification_reason"),
        unsupported_reason=kwargs.get("unsupported_reason"),
    )


def evidence(*, decision=None, confidence="MEDIUM", n=5, providers=4):
    return ResultadoEvidenciaPrecio(
        status="DECISION_READY" if decision else "RANGE_READY",
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        observations_n=n,
        providers_n=providers,
        min_ars=Decimal("28000"),
        q1_ars=Decimal("30000"),
        median_ars=Decimal("35000"),
        q3_ars=Decimal("40000"),
        max_ars=Decimal("48000"),
        evidence_confidence=confidence,
        decision_label=decision,
    )


def test_reasonable_response_exposes_authorized_range():
    r = presentar_resultado_pricing(
        result("DECISION_READY", evidence(decision="RAZONABLE"))
    )
    assert r.headline == "RAZONABLE"
    assert "$30.000–$40.000" in r.summary
    assert "5 precios de 4 proveedores" in r.evidence_line


def test_low_response():
    r = presentar_resultado_pricing(
        result("DECISION_READY", evidence(decision="BAJO"))
    )
    assert r.headline == "BAJO"
    assert "$30.000" in r.summary


def test_high_response():
    r = presentar_resultado_pricing(
        result("DECISION_READY", evidence(decision="ALTO"))
    )
    assert r.headline == "ALTO"
    assert "$40.000" in r.summary


def test_insufficient_never_invents_decision():
    e = evidence(decision=None, confidence="INSUFFICIENT", n=3, providers=1)
    r = presentar_resultado_pricing(result("INSUFFICIENT_EVIDENCE", e))
    assert r.headline == "Evidencia insuficiente"
    assert "retiene la decisión" in r.caveat


def test_clarification_uses_parser_question():
    r = presentar_resultado_pricing(
        result(
            "CLARIFICATION_REQUIRED",
            clarification_question="¿En qué provincia?",
            clarification_reason="MISSING_PROVINCE",
        )
    )
    assert r.headline == "Necesito una aclaración"
    assert r.summary == "¿En qué provincia?"


def test_unsupported_is_explicit():
    r = presentar_resultado_pricing(
        result(
            "UNSUPPORTED_QUERY",
            unsupported_reason="SINGLE_CANONICAL_SERVICE_REQUIRED",
        )
    )
    assert "Todavía no puedo" in r.headline
    assert r.caveat == "SINGLE_CANONICAL_SERVICE_REQUIRED"
