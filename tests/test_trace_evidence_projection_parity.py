from decimal import Decimal

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.infraestructura.real_world_query_tracer import trace_real_world_query


def cohort(*, market="AR", scope="PER_HOUR", context="STANDARD"):
    return CohortePricing(
        market=market,
        canonical_service="SOPORTE_REMOTO",
        observations_n=3,
        providers_n=3,
        min_ars=Decimal("28000"),
        q1_ars=Decimal("29000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("35000"),
        max_ars=Decimal("40000"),
        spread_ratio=Decimal("1.428"),
        evidence_confidence="LOW",
        decision_ready=False,
        range_ready=True,
        price_scope=scope,
        commercial_context=context,
    )


def evidence_id(evidence):
    return (
        f"pricing-cohort:{evidence.market}:{evidence.canonical_service}:"
        f"{evidence.price_scope}:{evidence.commercial_context.value.value}"
    )


def assert_engine_trace_parity(query, cohorts, *, case_id):
    engine = resolver_consulta_pricing(query, local_cohortes=(), remote_cohortes=cohorts)
    trace = trace_real_world_query(
        query,
        local_cohortes=(),
        remote_cohortes=cohorts,
        source_case_id=case_id,
        case_origin="CURATED_ENKI",
    )
    engine_ids = (engine.evidence.evidence_id,) if engine.evidence and engine.evidence.evidence_id else ()
    assert trace.accepted_evidence == engine_ids
    assert len(trace.accepted_evidence) == len(engine_ids)
    return engine, trace


def test_standard_engine_selection_does_not_project_urgency_as_accepted():
    query = "quiero cobrar 30 lucas la hora de soporte remoto en horario habitual, me quedo corto?"
    cohorts = (cohort(context="STANDARD"), cohort(context="URGENCY"))
    engine, trace = assert_engine_trace_parity(
        query, cohorts, case_id="projection:standard"
    )

    assert engine.evidence.commercial_context.value.value == "STANDARD"
    assert trace.accepted_evidence == (evidence_id(engine.evidence),)
    assert len(trace.accepted_evidence) == 1
    urgency = next(item for item in trace.evidence_candidates if item.evidence_id.endswith(":URGENCY"))
    assert urgency.decision == "EXCLUDED"
    assert urgency.exclusion_reasons == ("COMMERCIAL_CONTEXT_MISMATCH",)


def test_urgency_engine_selection_does_not_project_standard_as_accepted():
    query = "quiero cobrar 30 lucas por hora de soporte remoto de urgencia"
    cohorts = (cohort(context="STANDARD"), cohort(context="URGENCY"))
    engine, trace = assert_engine_trace_parity(query, cohorts, case_id="projection:urgency")
    assert engine.evidence.commercial_context.value.value == "URGENCY"
    standard = next(item for item in trace.evidence_candidates if item.evidence_id.endswith(":STANDARD"))
    assert standard.decision == "EXCLUDED"
    assert standard.exclusion_reasons == ("COMMERCIAL_CONTEXT_MISMATCH",)


def test_market_mismatch_keeps_exact_exclusion_and_engine_parity():
    query = "cuanto se cobra por hora por soporte remoto en horario habitual?"
    cohorts = (cohort(), cohort(market="Córdoba"))
    _, trace = assert_engine_trace_parity(query, cohorts, case_id="projection:market")
    mismatch = next(item for item in trace.evidence_candidates if ":Córdoba:" in item.evidence_id)
    assert mismatch.exclusion_reasons == ("MARKET_MISMATCH",)


def test_price_scope_mismatch_keeps_exact_exclusion_and_engine_parity():
    query = "cuanto se cobra por hora por soporte remoto en horario habitual?"
    cohorts = (cohort(scope="PER_HOUR"), cohort(scope="PER_MONTH"))
    _, trace = assert_engine_trace_parity(query, cohorts, case_id="projection:scope")
    mismatch = next(item for item in trace.evidence_candidates if ":PER_MONTH:" in item.evidence_id)
    assert mismatch.exclusion_reasons == ("PRICE_SCOPE_MISMATCH",)


def test_unknown_side_is_excluded_not_mismatch_or_accepted():
    query = "cuanto se cobra por hora por soporte remoto en horario habitual?"
    cohorts = (cohort(scope="PER_HOUR"), cohort(scope="UNKNOWN"))
    _, trace = assert_engine_trace_parity(query, cohorts, case_id="projection:unknown")
    unknown = next(item for item in trace.evidence_candidates if ":UNKNOWN:" in item.evidence_id)
    assert unknown.exclusion_reasons == ("PRICE_SCOPE_UNKNOWN_SIDE",)


def test_single_comparable_evidence_has_exact_engine_trace_parity():
    query = "cuanto se cobra por hora por soporte remoto en horario habitual?"
    engine, trace = assert_engine_trace_parity(query, (cohort(),), case_id="projection:comparable")
    assert trace.accepted_evidence == (engine.evidence.evidence_id,)
    assert trace.excluded_evidence == ()


def test_zero_engine_evidence_never_projects_candidate_as_accepted():
    query = "cuanto se cobra por hora por soporte remoto en horario habitual?"
    engine, trace = assert_engine_trace_parity(
        query, (cohort(scope="PER_MONTH"),), case_id="projection:zero"
    )
    assert engine.evidence.evidence_id is None
    assert trace.accepted_evidence == ()
    assert len(trace.excluded_evidence) == 1


def test_human_real_001_replay_has_no_phantom_accepted_evidence():
    query = "Cuánto puedo cobrar por formatear una notebook?"
    local, remote = cargar_cohortes_pricing_runtime()
    trace = trace_real_world_query(
        query,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="projection:human-real-001-replay",
        case_origin="HUMAN_REAL",
    )
    assert trace.intent_result == {"action": "SUGGEST_PRICE", "side": "SELL"}
    assert trace.parser_result["canonical_services"] == ["FORMATEO_INSTALACION_SO"]
    assert trace.economic_dimensions["device"]["value"] == "NOTEBOOK"
    assert trace.economic_dimensions["location"]["value"] is None
    assert trace.economic_dimensions["currency"]["value"] == "UNKNOWN"
    assert trace.economic_dimensions["price_scope"]["value"] == "UNKNOWN"
    assert trace.readiness == "CLARIFICATION_REQUIRED"
    assert trace.accepted_evidence == ()
