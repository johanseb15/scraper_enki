from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from scripts.audit_real_query_corpus import classify
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.infraestructura.real_world_trace_artifact import adjudicate_trace


def cohort(*, scope: str = "PER_HOUR", context: str = "STANDARD"):
    return CohortePricing(
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        observations_n=3,
        providers_n=3,
        min_ars=Decimal("10000"),
        q1_ars=Decimal("15000"),
        median_ars=Decimal("20000"),
        q3_ars=Decimal("25000"),
        max_ars=Decimal("30000"),
        spread_ratio=Decimal("2"),
        evidence_confidence="LOW",
        decision_ready=False,
        range_ready=False,
        price_scope=scope,
        commercial_context=context,
    )


def test_remote_support_missing_scope_clarifies_without_any_evidence():
    result = resolver_consulta_pricing(
        "cu\u00e1nto deber\u00eda cobrar por soporte remoto?",
        local_cohortes=(),
        remote_cohortes=(),
    )

    assert result.status == "CLARIFICATION_REQUIRED"
    assert result.clarification_reason == "PRICE_SCOPE_REQUIRED"


def test_onsite_visit_missing_scope_clarifies_without_any_evidence():
    result = resolver_consulta_pricing(
        "cu\u00e1nto se cobra una visita t\u00e9cnica a domicilio en Buenos Aires?",
        local_cohortes=(),
        remote_cohortes=(),
    )

    assert result.status == "CLARIFICATION_REQUIRED"
    assert result.clarification_reason == "PRICE_SCOPE_REQUIRED"


def test_formateo_unknown_scope_does_not_gain_fake_cadence_requirement():
    result = resolver_consulta_pricing(
        "cuanto se esta cobrando un formateo en C\u00f3rdoba?",
        local_cohortes=(),
        remote_cohortes=(),
    )

    assert result.parsed.price_scope.comparison_scope == "UNKNOWN"
    assert "PRICE_SCOPE_REQUIRED" not in (
        result.parsed.metadata.clarification_reason or ""
    )
    assert result.status == "NO_EVIDENCE"


def test_insufficient_to_no_evidence_is_expected_safety_change_in_direct_audit():
    record = {
        "adjudication": {
            "expected_behavior": "PARSE",
            "expected_resolution_status": "INSUFFICIENT_EVIDENCE",
            "allow_decision": False,
            "expected_fields": {},
        }
    }

    result = SimpleNamespace(
        status="NO_EVIDENCE",
        parsed=SimpleNamespace(),
    )

    outcome, errors = classify(record, result)

    assert outcome == "EXPECTED_SAFETY_CHANGE"
    assert errors == []


def test_insufficient_to_no_evidence_is_expected_safety_change_in_trace_audit():
    record = {
        "adjudication": {
            "expected_behavior": "PARSE",
            "expected_resolution_status": "INSUFFICIENT_EVIDENCE",
            "expected_fields": {},
        }
    }

    trace = SimpleNamespace(
        readiness="NO_EVIDENCE",
        intent_result={
            "action": "UNKNOWN",
            "side": "UNKNOWN",
        },
        parser_result={
            "economic_object_kind": "SERVICE",
            "canonical_services": [],
            "market_scope": "UNKNOWN",
            "modality": "UNKNOWN",
            "price": {
                "value": None,
                "currency": "UNKNOWN",
            },
            "geography": {
                "province": None,
                "city": None,
            },
        },
        economic_dimensions={
            "price_scope": {
                "value": "UNKNOWN",
            },
        },
    )

    outcome, errors = adjudicate_trace(record, trace)

    assert outcome == "EXPECTED_SAFETY_CHANGE"
    assert errors == []

def test_remote_service_fragment_without_pricing_intent_stays_unsupported():
    result = resolver_consulta_pricing(
        "remoto por TeamViewer",
        local_cohortes=(),
        remote_cohortes=(cohort(),),
    )

    assert result.parsed.canonical_services == ("SOPORTE_REMOTO",)
    assert result.parsed.intent_action.value == "UNKNOWN"
    assert result.status == "UNSUPPORTED_QUERY"
    assert result.unsupported_reason == "UNSUPPORTED_INTENT"
