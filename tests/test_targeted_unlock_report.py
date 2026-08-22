import json
from pathlib import Path

from scripts.build_semantic_economic_shadow import build_semantic_economic_shadow
from src.dominio.economic_evidence import DimensionStatus
from src.infraestructura.economic_dimensions_v2_artifact import load_economic_dimensions_v2_sidecar
from src.infraestructura.targeted_unlock_report import build_targeted_unlock_report


ROOT = Path(__file__).parents[1]


def test_real_before_after_reports_only_the_safe_reach_gain(tmp_path):
    before = tmp_path / "before.jsonl"
    after = tmp_path / "after.jsonl"
    build_semantic_economic_shadow(
        ROOT / "data/semantic_normalization_v4.csv", before,
        dimensions_path=ROOT / "data/acquisition_baseline_dimensions_v2.jsonl",
    )
    build_semantic_economic_shadow(
        ROOT / "data/semantic_normalization_v4.csv", after,
        dimensions_path=ROOT / "data/economic_dimensions_v2.jsonl",
    )
    outcomes = tmp_path / "outcomes.jsonl"
    outcomes.write_bytes((ROOT / "data/acquisition_outcomes_v1.jsonl").read_bytes())
    report = tmp_path / "report.json"
    metrics = build_targeted_unlock_report(
        before, after,
        ROOT / "data/acquisition_baseline_gap_register_v1.jsonl",
        ROOT / "data/economic_evidence_gap_register_v1.jsonl",
        ROOT / "data/targeted_source_claims_v1.jsonl",
        outcomes, report,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert metrics == {"TARGETS": 5, "NEW_COMPARABLE_PAIRS": 0, "NEW_PARTIAL": 0, "NEW_READY": 0}
    assert payload["global_delta"]["REACH_UNKNOWN"] == -1
    assert payload["global_delta"]["SOURCE_EXPLICIT_CLAIMS"] == 1
    assert payload["global_delta"]["TOTAL_COMPARABLE_EVIDENCE"] == 0
    target = next(item for item in payload["targets"] if item["observation_id"] == "234")
    assert "MISSING_REACH" in target["before_blockers"]
    assert "MISSING_REACH" not in target["after_blockers"]
    assert target["after_readiness"] == "INSUFFICIENT"
    assert payload["comparable_quality_audit"] == []
    updated_outcomes = [json.loads(line) for line in outcomes.read_text(encoding="utf-8").splitlines()]
    assert all(item["unlock_delta"] == item["actual_unlock"] - item["expected_unlock"] for item in updated_outcomes)


def test_targeted_enrichment_preserves_known_currency_conflicts():
    dimensions = load_economic_dimensions_v2_sidecar(ROOT / "data/economic_dimensions_v2.jsonl")
    assert all(dimensions[item].currency.status is DimensionStatus.CONFLICTED for item in ("159", "160", "161"))
