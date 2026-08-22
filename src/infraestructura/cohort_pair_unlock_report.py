from __future__ import annotations

import json
from pathlib import Path


GLOBAL_KEYS = (
    "TOTAL_OBSERVATIONS", "EVIDENCE_RESOLVED", "NO_EVIDENCE", "READY", "PARTIAL",
    "INSUFFICIENT", "AMBIGUOUS", "UNKNOWN", "TOTAL_COMPARABLE_EVIDENCE",
    "TOTAL_EXCLUDED_EVIDENCE",
)


def build_cohort_pair_unlock_report(
    before_shadow_summary_path,
    after_shadow_summary_path,
    planner_summary_path,
    pairs_path,
    outcomes_path,
    report_path,
):
    before = json.loads(Path(before_shadow_summary_path).read_text(encoding="utf-8"))["metrics"]
    after = json.loads(Path(after_shadow_summary_path).read_text(encoding="utf-8"))["metrics"]
    planner = json.loads(Path(planner_summary_path).read_text(encoding="utf-8"))
    pairs = _jsonl(pairs_path)
    outcomes = _jsonl(outcomes_path)
    global_before = {key: before[key] for key in GLOBAL_KEYS}
    global_after = {key: after[key] for key in GLOBAL_KEYS}
    reasons = sorted(set(before["EXCLUSION_REASONS"]) | set(after["EXCLUSION_REASONS"]))
    pair_snapshot = [
        {
            "pair_id": item["pair_id"],
            "state": item["compatibility_state"],
            "hard_blockers": item["hard_blockers"],
            "explicit_mismatches": item["explicit_mismatches"],
            "missing_evidence": item["missing_evidence"],
        }
        for item in pairs
    ]
    payload = {
        "schema_version": "cohort-pair-before-after-v1",
        "cohort": planner["cohort"],
        "pair_metrics_before": planner["pair_metrics"],
        "pair_metrics_after": planner["pair_metrics"],
        "cohort_metrics_before": planner["cohort_metrics"],
        "cohort_metrics_after": planner["cohort_metrics"],
        "pair_blockers_before": pair_snapshot,
        "pair_blockers_after": pair_snapshot,
        "global_shadow_before": global_before,
        "global_shadow_after": global_after,
        "global_shadow_delta": {key: global_after[key] - global_before[key] for key in GLOBAL_KEYS},
        "exclusion_reason_delta": {
            reason: after["EXCLUSION_REASONS"].get(reason, 0) - before["EXCLUSION_REASONS"].get(reason, 0)
            for reason in reasons
        },
        "information_gain_outcomes": outcomes,
        "new_comparable_pairs": 0,
        "new_independent_providers": 0,
        "claims_found": 0,
        "claims_rejected": 0,
        "temporal_mismatches": 0,
        "new_raw_snapshots": 0,
        "quality_audit": [],
        "dimensions_changed": False,
        "gap_register_changed": False,
    }
    Path(report_path).write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "NEW_COMPARABLE_PAIRS": 0,
        "NETWORK_ACTIONS": sum(item["status"] == "EXECUTED" for item in outcomes),
        "LOCATION_FALSE_BLOCKERS_REMOVED": -payload["exclusion_reason_delta"].get("LOCATION_MISMATCH", 0),
        "GLOBAL_READINESS_DELTA": global_after["READY"] - global_before["READY"],
    }


def _jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
