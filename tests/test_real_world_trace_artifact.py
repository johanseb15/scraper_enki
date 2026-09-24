import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.infraestructura.real_world_query_tracer import trace_real_world_query
from src.infraestructura.real_world_trace_artifact import adjudicate_trace, build_real_world_trace_artifacts


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("case_id", ("rq001", "rq003", "rq012", "rq032", "rq048"))
def test_unknown_national_reach_is_expected_safety_change_in_audit(case_id):
    records = (
        json.loads(line)
        for line in (ROOT / "data/language/real_query_corpus_v1.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    )
    record = next(row for row in records if row["id"] == case_id)
    local, remote = cargar_cohortes_pricing_runtime()
    trace = trace_real_world_query(
        record["query_raw"], local_cohortes=local, remote_cohortes=remote,
        source_case_id=case_id, case_origin=record["provenance"],
    )

    assert trace.parser_result["modality"] == "REMOTE"
    assert trace.parser_result["market_scope"] == "UNKNOWN"
    assert adjudicate_trace(record, trace) == ("EXPECTED_SAFETY_CHANGE", [])
    if case_id == "rq003":
        record["adjudication"]["expected_fields"]["price_value"] = 123
        outcome, errors = adjudicate_trace(record, trace)
        assert outcome == "WRONG_INTERPRETATION"
        assert any(error.startswith("price_value:") for error in errors)


def test_new_remote_scope_failure_is_not_a_historical_safety_change():
    query = "quiero cobrar 30 lucas la hora por soporte remoto, me quedo corto?"
    record = {
        "id": "rq_future_remote",
        "query_raw": query,
        "adjudication": {
            "expected_behavior": "PARSE",
            "expected_resolution_status": "RANGE_READY",
            "expected_fields": {"modality": "REMOTE", "price_value": 30000},
        },
    }
    local, remote = cargar_cohortes_pricing_runtime()
    trace = trace_real_world_query(
        query, local_cohortes=local, remote_cohortes=remote,
        source_case_id=record["id"], case_origin="CURATED_ENKI",
    )

    assert trace.parser_result["market_scope"] == "UNKNOWN"
    assert trace.readiness == "UNSUPPORTED_QUERY"
    assert trace.public_response["caveat"] == "UNSUPPORTED_MARKET_SCOPE"
    outcome, errors = adjudicate_trace(record, trace)
    assert outcome == "WRONG_INTERPRETATION"
    assert "expected evidence path, got UNSUPPORTED_QUERY" in errors


def test_explicit_national_reach_misparsed_as_unknown_is_wrong_interpretation():
    query = "quiero cobrar 30 lucas la hora por soporte remoto a todo el país, me quedo corto?"
    record = {
        "id": "rq003",
        "query_raw": query,
        "adjudication": {
            "expected_behavior": "PARSE",
            "expected_resolution_status": "RANGE_READY",
            "expected_fields": {"market_scope": "REMOTE_NATIONAL", "modality": "REMOTE"},
        },
    }
    local, remote = cargar_cohortes_pricing_runtime()
    correct_trace = trace_real_world_query(
        query, local_cohortes=local, remote_cohortes=remote,
        source_case_id=record["id"], case_origin="CURATED_ENKI",
    )
    assert correct_trace.parser_result["market_scope"] == "REMOTE_NATIONAL"
    broken_trace = replace(
        correct_trace,
        parser_result={**correct_trace.parser_result, "market_scope": "UNKNOWN"},
        readiness="UNSUPPORTED_QUERY",
        public_response={**correct_trace.public_response, "caveat": "UNSUPPORTED_MARKET_SCOPE"},
    )

    outcome, errors = adjudicate_trace(record, broken_trace)
    assert outcome == "WRONG_INTERPRETATION"
    assert any(error.startswith("market_scope:") for error in errors)


def test_real_pipeline_corpus_builds_labeled_append_only_traces(tmp_path):
    metrics = build_real_world_trace_artifacts(ROOT, tmp_path)
    traces = [json.loads(line) for line in (tmp_path / "real_world_query_traces_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    assert metrics["TOTAL_TRACES"] == 50
    assert metrics["TOTAL_REAL_TRACES"] == 0
    assert metrics["TRACE_ORIGINS"] == {
        "CURATED_ENKI": 37, "SYNTHETIC_DEEPSEEK": 5, "SYNTHETIC_GEMINI": 3, "SYNTHETIC_GROK": 5,
    }
    assert len(traces) == 50
    assert len({item["trace_id"] for item in traces}) == 50
    assert all(item["real_world_outcome"] == {"status": "UNKNOWN", "feedback": None} for item in traces)
    build_real_world_trace_artifacts(ROOT, tmp_path)
    assert len((tmp_path / "real_world_query_traces_v2.jsonl").read_text(encoding="utf-8").splitlines()) == 50


def test_summary_uses_percentiles_only_with_sufficient_sample_and_no_promotion(tmp_path):
    metrics = build_real_world_trace_artifacts(ROOT, tmp_path)
    summary = json.loads((tmp_path / "real_world_performance_summary_v1.json").read_text(encoding="utf-8"))
    intake = [json.loads(line) for line in (tmp_path / "real_world_learning_intake_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert summary["performance"]["sample_size"] == 50
    assert summary["performance"]["sufficient_for_percentiles"] is True
    assert set(summary["performance"]["total_latency_ms"]) == {"p50", "p95", "max"}
    assert metrics["AUTO_PROMOTIONS"] == 0
    assert metrics["NEW_KNOWLEDGE_CANDIDATES"] == 0
    assert metrics["REGRESSION_OUTCOMES"].get("WRONG_INTERPRETATION", 0) == 0
    assert metrics["PREVIOUS_AUDIT_WRONG_INTERPRETATION"] == 19
    assert metrics["REGRESSION_AUDIT_DRIFT"] == -19
    assert all(item["promotion_authorized"] is False for item in intake)


def test_audit_names_real_public_flow_and_honestly_declares_granularity(tmp_path):
    build_real_world_trace_artifacts(ROOT, tmp_path)
    audit = json.loads((tmp_path / "real_world_runtime_flow_audit_v1.json").read_text(encoding="utf-8"))
    assert audit["public_entrypoint"] == "POST /decision/pricing"
    assert len(audit["stages"]) == 10
    assert audit["evidence_granularity"] == "AGGREGATED_PRICING_COHORT"
    assert audit["offer_level_runtime_evidence_available"] is False
    assert audit["runtime_mutation"] is False


def test_execution_preserves_parser_pricing_api_validation_and_currency_conflicts(tmp_path):
    protected = (
        ROOT / "src/aplicacion/parser_consulta_pricing.py",
        ROOT / "src/aplicacion/pricing_evidence_engine.py",
        ROOT / "src/api/main.py",
        ROOT / "data/candidate_shadow_validation_results_v2.jsonl",
        ROOT / "data/knowledge_candidates_v1.jsonl",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    build_real_world_trace_artifacts(ROOT, tmp_path)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected} == before
    result = json.loads((ROOT / "data/candidate_shadow_validation_results_v2.jsonl").read_text(encoding="utf-8"))
    assert result["outcome"] == "FAIL_SHADOW_VALIDATION"
    dimensions = [json.loads(line) for line in (ROOT / "data/economic_dimensions_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(dimensions[index - 1]["dimensions"]["currency"]["status"] == "CONFLICTED" for index in (159, 160, 161))
