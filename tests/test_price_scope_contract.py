from decimal import Decimal

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.aplicacion.pricing_evidence_engine import evaluar_precio
from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
    ScopeCompatibility,
    compare_price_scopes,
    normalize_price_scope,
)
from src.infraestructura.real_world_query_tracer import trace_real_world_query


def cohort(scope):
    return CohortePricing(
        market="AR", canonical_service="SOPORTE_REMOTO", observations_n=3, providers_n=3,
        min_ars=Decimal("20000"), q1_ars=Decimal("25000"), median_ars=Decimal("30000"),
        q3_ars=Decimal("35000"), max_ars=Decimal("40000"), spread_ratio=Decimal("2"),
        evidence_confidence="LOW", decision_ready=False, range_ready=True, price_scope=scope,
    )


def test_explicit_hour_visit_and_month_are_orthogonal_and_preserved():
    hour = normalize_price_scope("30 lucas por hora", has_price=True)
    visit = normalize_price_scope("30 lucas por visita", has_price=True)
    month = normalize_price_scope("30 lucas mensual", has_price=True)
    assert hour.charged_unit is ChargedUnitMeaning.HOUR and hour.comparison_scope == "PER_HOUR"
    assert visit.charged_unit is ChargedUnitMeaning.VISIT and visit.comparison_scope == "PER_VISIT"
    assert month.billing_period is BillingPeriodMeaning.MONTH and month.comparison_scope == "PER_MONTH"


def test_from_price_remains_orthogonal_to_charged_unit_with_raw_and_provenance():
    scope = normalize_price_scope("desde 30 lucas por hora", has_price=True)
    assert scope.charged_unit is ChargedUnitMeaning.HOUR
    assert scope.price_bound is PriceBoundMeaning.FROM
    assert scope.comparison_scope == "PER_HOUR"
    assert scope.raw_basis == "por hora | desde"
    assert scope.provenance == "raw_user_input"


def test_unknown_is_insufficient_not_mismatch_and_numeric_price_adds_no_scope():
    unknown = normalize_price_scope("me cobran 30000", has_price=True)
    hour = normalize_price_scope("me cobran 30000 por hora", has_price=True)
    assert unknown.comparison_scope == "UNKNOWN"
    assert compare_price_scopes(unknown, hour) is ScopeCompatibility.INSUFFICIENT_EVIDENCE
    assert compare_price_scopes(hour, hour) is ScopeCompatibility.COMPATIBLE
    assert compare_price_scopes(hour, "PER_VISIT") is ScopeCompatibility.INCOMPATIBLE
    assert evaluar_precio((cohort("UNKNOWN"),), market="AR", canonical_service="SOPORTE_REMOTO", price_scope="UNKNOWN").status == "NO_EVIDENCE"


def test_real_corpus_each_100gb_loss_is_recovered_without_changing_intent():
    parsed = parse_pricing_query("backup de 500GB, cada 100GB extras 38k, cuánto cobro?")
    assert parsed.price_scope.charged_unit is ChargedUnitMeaning.UNIT
    assert parsed.price_scope.comparison_scope == "PER_UNIT"
    assert parsed.intent_action.value == "UNKNOWN"  # Existing unrelated intent behavior is not changed here.


def test_explicit_scope_propagates_parser_runtime_comparability_and_trace():
    text = "quiero cobrar 30 lucas la hora de soporte remoto, me quedo corto?"
    cohorts = (cohort("PER_HOUR"), cohort("PER_VISIT"))
    result = resolver_consulta_pricing(text, local_cohortes=(), remote_cohortes=cohorts)
    trace = trace_real_world_query(text, local_cohortes=(), remote_cohortes=cohorts, source_case_id="scope:e2e", case_origin="CURATED_ENKI")
    assert result.evidence.price_scope == "PER_HOUR"
    assert trace.economic_dimensions["price_scope"]["value"] == "PER_HOUR"
    assert len(trace.accepted_evidence) == 1
    excluded = next(item for item in trace.evidence_candidates if item.decision == "EXCLUDED")
    assert excluded.exclusion_reasons == ("PRICE_SCOPE_MISMATCH",)
