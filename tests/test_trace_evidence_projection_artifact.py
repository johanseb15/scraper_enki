import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_trace_projection_reconciliation_artifact_reports_exact_parity():
    artifact = json.loads(
        (ROOT / "data/evaluation/trace_evidence_projection_reconciliation_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert artifact["engine_accepted_before"] == 3
    assert artifact["trace_accepted_before"] == 5
    assert artifact["mismatches_before"] == 2
    assert artifact["engine_accepted_after"] == artifact["trace_accepted_after"] == 3
    assert artifact["mismatches_after"] == 0
    assert artifact["trace_engine_evidence_parity"] is True
    assert artifact["public_decision_drift"] == artifact["readiness_drift"] == 0
    assert artifact["human_real_001"]["accepted_evidence"] == []
    assert artifact["corpus_50_summary"]["affected_cases"] == ["rq003", "rq032"]
    assert artifact["corpus_50_summary"]["wrong_interpretation_after"] == 21
    assert artifact["runtime_effect"] is False
    assert artifact["promotion_authorized"] is False
