import hashlib
import json
from pathlib import Path

from src.infraestructura.real_world_trace_artifact import build_real_world_trace_artifacts


ROOT = Path(__file__).parents[1]


def test_real_pipeline_corpus_builds_labeled_append_only_traces(tmp_path):
    metrics = build_real_world_trace_artifacts(ROOT, tmp_path)
    traces = [json.loads(line) for line in (tmp_path / "real_world_query_traces_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert metrics["TOTAL_TRACES"] == 50
    assert metrics["TOTAL_REAL_TRACES"] == 0
    assert metrics["TRACE_ORIGINS"] == {
        "CURATED_ENKI": 37, "SYNTHETIC_DEEPSEEK": 5, "SYNTHETIC_GEMINI": 3, "SYNTHETIC_GROK": 5,
    }
    assert len(traces) == 50
    assert len({item["trace_id"] for item in traces}) == 50
    assert all(item["real_world_outcome"] == {"status": "UNKNOWN", "feedback": None} for item in traces)
    build_real_world_trace_artifacts(ROOT, tmp_path)
    assert len((tmp_path / "real_world_query_traces_v1.jsonl").read_text(encoding="utf-8").splitlines()) == 50


def test_summary_uses_percentiles_only_with_sufficient_sample_and_no_promotion(tmp_path):
    metrics = build_real_world_trace_artifacts(ROOT, tmp_path)
    summary = json.loads((tmp_path / "real_world_performance_summary_v1.json").read_text(encoding="utf-8"))
    intake = [json.loads(line) for line in (tmp_path / "real_world_learning_intake_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert summary["performance"]["sample_size"] == 50
    assert summary["performance"]["sufficient_for_percentiles"] is True
    assert set(summary["performance"]["total_latency_ms"]) == {"p50", "p95", "max"}
    assert metrics["AUTO_PROMOTIONS"] == 0
    assert metrics["NEW_KNOWLEDGE_CANDIDATES"] == 0
    assert metrics["REGRESSION_OUTCOMES"]["WRONG_INTERPRETATION"] == 5
    assert metrics["PREVIOUS_AUDIT_WRONG_INTERPRETATION"] == 19
    assert metrics["REGRESSION_AUDIT_DRIFT"] == -14
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
