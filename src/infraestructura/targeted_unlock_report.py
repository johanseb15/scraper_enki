from __future__ import annotations

import json
from pathlib import Path


TARGET_IDS = ("62", "68", "69", "70", "234")


def build_targeted_unlock_report(
    before_shadow_path, after_shadow_path, before_gap_path, after_gap_path,
    claims_path, outcomes_path, report_path,
):
    before = _by_id(before_shadow_path); after = _by_id(after_shadow_path)
    before_gaps = _by_id(before_gap_path); after_gaps = _by_id(after_gap_path)
    claims = [json.loads(line) for line in Path(claims_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    outcomes = [json.loads(line) for line in Path(outcomes_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    target_reports = []
    for observation_id in TARGET_IDS:
        b, a = before[observation_id], after[observation_id]
        target_claims = [claim for claim in claims if claim["observation_id"] == observation_id]
        target_reports.append({
            "observation_id": observation_id,
            "before_blockers": before_gaps[observation_id]["blockers"],
            "after_blockers": after_gaps[observation_id]["blockers"],
            "before_comparable_candidates": len(b["comparable_evidence"]),
            "after_comparable_candidates": len(a["comparable_evidence"]),
            "before_independent_providers": b["independent_provider_count"],
            "after_independent_providers": a["independent_provider_count"],
            "before_readiness": b["readiness"], "after_readiness": a["readiness"],
            "new_evidence": target_claims,
            "remaining_missing_dimensions": a["missing_dimensions"],
        })
    for outcome in outcomes:
        observation_id = outcome["observation_id"]
        actual = len(after[observation_id]["comparable_evidence"]) - len(before[observation_id]["comparable_evidence"])
        outcome["actual_unlock"] = actual
        outcome["unlock_delta"] = actual - outcome["expected_unlock"]
        outcome["remaining_gaps"] = after_gaps[observation_id]["blockers"]
        if outcome["expected_unlock"] != actual:
            outcome["reason"] += f" Expected {outcome['expected_unlock']}, actual {actual}; peer-side blockers remain."
    _write_jsonl(outcomes_path, outcomes)
    before_summary = json.loads(Path(before_shadow_path).with_suffix(".summary.json").read_text(encoding="utf-8"))["metrics"]
    after_summary = json.loads(Path(after_shadow_path).with_suffix(".summary.json").read_text(encoding="utf-8"))["metrics"]
    keys = (
        "TOTAL_OBSERVATIONS", "EVIDENCE_RESOLVED", "NO_EVIDENCE", "READY", "PARTIAL",
        "INSUFFICIENT", "AMBIGUOUS", "UNKNOWN", "TOTAL_COMPARABLE_EVIDENCE",
    )
    global_before = {key: before_summary[key] for key in keys}
    global_after = {key: after_summary[key] for key in keys}
    global_before.update({
        "REACH_UNKNOWN": before_summary["UNKNOWN_DIMENSIONS"]["geographic_reach"],
        "PRICE_SCOPE_UNKNOWN": before_summary["UNKNOWN_DIMENSIONS"]["price_scope"],
        "MATERIALS_UNKNOWN": before_summary["UNKNOWN_DIMENSIONS"]["materials_included"],
        "HARDWARE_UNKNOWN": before_summary["UNKNOWN_DIMENSIONS"]["hardware_included"],
        "SOURCE_EXPLICIT_CLAIMS": 0,
    })
    global_after.update({
        "REACH_UNKNOWN": after_summary["UNKNOWN_DIMENSIONS"]["geographic_reach"],
        "PRICE_SCOPE_UNKNOWN": after_summary["UNKNOWN_DIMENSIONS"]["price_scope"],
        "MATERIALS_UNKNOWN": after_summary["UNKNOWN_DIMENSIONS"]["materials_included"],
        "HARDWARE_UNKNOWN": after_summary["UNKNOWN_DIMENSIONS"]["hardware_included"],
        "SOURCE_EXPLICIT_CLAIMS": len(claims),
    })
    new_pairs = sum(item["after_comparable_candidates"] - item["before_comparable_candidates"] for item in target_reports)
    payload = {
        "schema_version": "targeted-economic-unlock-report-v1",
        "targets": target_reports,
        "global_before": global_before,
        "global_after": global_after,
        "global_delta": {key: global_after[key] - global_before[key] for key in global_before},
        "new_comparable_pairs": new_pairs,
        "new_partial_observations": global_after["PARTIAL"] - global_before["PARTIAL"],
        "new_ready_observations": global_after["READY"] - global_before["READY"],
        "comparable_quality_audit": [],
    }
    Path(report_path).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"TARGETS": 5, "NEW_COMPARABLE_PAIRS": new_pairs, "NEW_PARTIAL": payload["new_partial_observations"], "NEW_READY": payload["new_ready_observations"]}


def _by_id(path):
    return {item["observation_id"]: item for item in (json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())}


def _write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows: handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
