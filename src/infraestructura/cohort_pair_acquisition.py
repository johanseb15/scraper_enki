from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def execute_positive_pair_actions(
    plan_path: str | Path,
    outcomes_path: str | Path,
    *,
    acquirer: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None,
) -> dict[str, int]:
    actions = [
        json.loads(line)
        for line in Path(plan_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    positive = [
        item for item in actions
        if item["expected_pairs_unlocked"] > 0 or item["expected_cohort_unlock"] > 0
    ]
    skipped = [item for item in actions if item not in positive]
    if positive and acquirer is None:
        raise RuntimeError("Positive pair actions require an explicit versioned acquirer.")
    acquisition_metrics = acquirer(positive) if positive and acquirer else {}
    outcomes = []
    for action in actions:
        executed = action in positive
        outcomes.append({
            "schema_version": "cohort-pair-acquisition-outcome-v1",
            "action_id": action["action_id"],
            "source": action["source"],
            "status": "EXECUTED" if executed else "SKIPPED_ZERO_COUNTERFACTUAL_VALUE",
            "expected_pair_unlock": action["expected_pairs_unlocked"],
            "actual_pair_unlock": 0,
            "expected_provider_gain": action["expected_independent_providers_gained"],
            "actual_provider_gain": 0,
            "expected_readiness_gain": "NONE",
            "actual_readiness_gain": "NONE",
            "reason": (
                "Positive counterfactual value authorized acquisition."
                if executed else
                "No network: action cannot complete any bilateral minimal unlock set by itself."
            ),
        })
    _write(outcomes_path, outcomes)
    return {
        "PLANNED_ACTIONS": len(actions),
        "EXECUTED_ACTIONS": len(positive),
        "SKIPPED_ZERO_VALUE_ACTIONS": len(skipped),
        "NETWORK_REQUESTS": int(acquisition_metrics.get("NETWORK_REQUESTS", 0)),
        "SOURCES_SUCCEEDED": int(acquisition_metrics.get("SOURCES_SUCCEEDED", 0)),
        "SOURCES_FAILED": int(acquisition_metrics.get("SOURCES_FAILED", 0)),
        "BLOCKED": int(acquisition_metrics.get("BLOCKED", 0)),
    }


def _write(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
