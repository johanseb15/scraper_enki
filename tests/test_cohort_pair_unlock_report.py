import json
from pathlib import Path

from src.infraestructura.cohort_pair_unlock_report import build_cohort_pair_unlock_report


ROOT = Path(__file__).parents[1]


def test_real_pair_report_records_no_acquisition_and_only_ontology_delta(tmp_path):
    output = tmp_path / "report.json"
    metrics = build_cohort_pair_unlock_report(
        ROOT / "data/cohort_pair_shadow_before.summary.json",
        ROOT / "data/cohort_pair_shadow_after.summary.json",
        ROOT / "data/cohort_pair_planner_summary_v1.json",
        ROOT / "data/economic_evidence_pairs_v1.jsonl",
        ROOT / "data/cohort_pair_acquisition_outcomes_v1.jsonl",
        output,
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert metrics == {
        "NEW_COMPARABLE_PAIRS": 0, "NETWORK_ACTIONS": 0,
        "LOCATION_FALSE_BLOCKERS_REMOVED": 26, "GLOBAL_READINESS_DELTA": 0,
    }
    assert report["pair_metrics_before"] == report["pair_metrics_after"]
    assert report["exclusion_reason_delta"]["LOCATION_MISMATCH"] == -26
    assert all(value == 0 for value in report["global_shadow_delta"].values())
    assert report["quality_audit"] == []
    assert all(item["status"] == "SKIPPED_ZERO_COUNTERFACTUAL_VALUE" for item in report["information_gain_outcomes"])
