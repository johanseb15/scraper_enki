from dataclasses import asdict
from decimal import Decimal
import json

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.enki_pricing_response import presentar_resultado_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.dominio.real_world_query_trace import FailureType, InputModality, stable_trace_id
from src.infraestructura.real_world_query_tracer import (
    append_trace,
    build_learning_intake,
    trace_real_world_query,
)


def cohort():
    return CohortePricing(
        market="AR", canonical_service="SOPORTE_REMOTO", observations_n=5, providers_n=4,
        min_ars=Decimal("28000"), q1_ars=Decimal("30000"), median_ars=Decimal("35000"),
        q3_ars=Decimal("40000"), max_ars=Decimal("48000"), spread_ratio=Decimal("1.714"),
        evidence_confidence="MEDIUM", decision_ready=True, range_ready=True,
    )


def run(text="me quieren cobrar 35 lucas por soporte remoto, está bien?"):
    return trace_real_world_query(
        text, local_cohortes=(), remote_cohortes=(cohort(),), source_case_id="human:1",
        case_origin="HUMAN_REAL", input_modality=InputModality.TEXT,
        provenance=("founder-session:test",), received_at="2026-08-23T00:00:00-03:00",
    )


def test_tracing_on_off_preserves_result_and_public_response():
    text = "me quieren cobrar 35 lucas por soporte remoto, está bien?"
    direct = resolver_consulta_pricing(text, local_cohortes=(), remote_cohortes=(cohort(),))
    trace = run(text)
    assert trace.parser_result["raw_text"] == direct.parsed.raw_text
    assert trace.readiness == direct.status
    assert trace.public_response == asdict(presentar_resultado_pricing(direct))


def test_raw_input_parser_intent_unknown_and_normalization_are_traceable():
    trace = run()
    assert trace.raw_user_input == "me quieren cobrar 35 lucas por soporte remoto, está bien?"
    assert trace.intent_result == {"action": "EVALUATE_PRICE", "side": "BUY"}
    price = next(item for item in trace.normalized_entities if item.field == "price.value")
    assert price.raw_value == " 35 lucas"
    assert price.normalized_value == 35000
    assert price.provenance == "raw_user_input"
    assert "price_scope" in trace.unknown_dimensions


def test_every_stage_has_real_nonnegative_timing_and_total_latency():
    trace = run()
    assert len(trace.stages) == 10
    assert all(item.elapsed_ms >= 0 for item in trace.stages)
    assert trace.total_latency_ms >= sum(item.elapsed_ms for item in trace.stages)
    assert trace.trace_overhead_ms >= 0


def test_evidence_exclusions_and_reasons_are_preserved():
    matching = CohortePricing(**{
        **asdict(cohort()),
        "price_scope": "PER_HOUR",
        "commercial_context": "STANDARD",
    })
    other = CohortePricing(**{**asdict(matching), "price_scope": "PER_MONTH"})
    trace = trace_real_world_query(
        "quiero cobrar 30 lucas la hora de soporte remoto en horario habitual, me quedo corto?",
        local_cohortes=(), remote_cohortes=(matching, other), source_case_id="case:2",
        case_origin="CURATED_ENKI", input_modality=InputModality.TEXT,
    )
    assert trace.accepted_evidence
    assert trace.excluded_evidence
    excluded = next(item for item in trace.evidence_candidates if item.decision == "EXCLUDED")
    assert "PRICE_SCOPE_MISMATCH" in excluded.exclusion_reasons


def test_replay_is_deterministic_except_measured_timing():
    first, second = run(), run()
    assert first.trace_id == second.trace_id
    assert first.replay_fingerprint == second.replay_fingerprint
    assert first.public_response == second.public_response


def test_trace_ids_are_stable_and_noncolliding():
    first = stable_trace_id(source_case_id="1", raw_user_input="a", case_origin="HUMAN_REAL")
    assert first == stable_trace_id(source_case_id="1", raw_user_input="a", case_origin="HUMAN_REAL")
    assert first != stable_trace_id(source_case_id="2", raw_user_input="a", case_origin="HUMAN_REAL")


def test_append_only_history_is_idempotent_and_never_overwrites(tmp_path):
    path = tmp_path / "traces.jsonl"
    trace = run()
    append_trace(path, trace)
    append_trace(path, trace)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["raw_user_input"] == trace.raw_user_input


def test_real_origin_is_not_synthetic_and_golden_candidate_is_not_truth():
    human = run()
    synthetic = trace_real_world_query(
        "texto", local_cohortes=(), remote_cohortes=(), source_case_id="synthetic:1",
        case_origin="SYNTHETIC_GROK", input_modality=InputModality.TEXT,
    )
    assert human.case_origin == "HUMAN_REAL"
    assert synthetic.case_origin == "SYNTHETIC_GROK"
    assert human.case_origin != synthetic.case_origin
    assert human.promotion_authorized is False


def test_multiple_failure_types_and_learning_intake_without_promotion():
    trace = trace_real_world_query(
        "quiero un precio", local_cohortes=(), remote_cohortes=(), source_case_id="human:bad",
        case_origin="HUMAN_REAL", input_modality=InputModality.TEXT,
    )
    assert FailureType.SEMANTIC_MAPPING_FAILURE in trace.failures
    assert FailureType.MISSING_USER_INFORMATION in trace.failures
    intake = build_learning_intake(trace)
    assert intake["promotion_authorized"] is False
    assert intake["candidate_status"] == "CANDIDATE_ONLY"


def test_no_network_or_runtime_mutation_and_one_input_yields_multiple_claims():
    trace = run("quiero cobrar 30 lucas la hora de soporte remoto, me quedo corto?")
    assert trace.runtime_mutation is False
    assert trace.learning_yield["network_requests"] == 0
    assert trace.learning_yield["normalized_claims"] >= 3
    assert trace.learning_yield["claims_extracted"] >= trace.learning_yield["normalized_claims"]
