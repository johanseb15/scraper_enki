import csv
import hashlib
import json
from pathlib import Path

import pytest

from src.infraestructura.price_scope_reconciliation_artifact import (
    build_price_scope_reconciliation,
)


ROOT = Path(__file__).resolve().parents[1]


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@pytest.fixture(scope="module")
def reconciliation(tmp_path_factory):
    output = tmp_path_factory.mktemp("price_scope_reconciliation")
    protected = (
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/local_pricing_stats_v1.csv",
        ROOT / "data/remote_pricing_stats_v1.csv",
        ROOT / "data/real_world_query_traces_v1.jsonl",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    metrics = build_price_scope_reconciliation(ROOT, output)
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    assert after == before
    return output, metrics


def test_all_44_unknowns_are_classified_without_guessing(reconciliation):
    output, metrics = reconciliation
    rows = jsonl(output / "price_scope_unknown_classification_v1.jsonl")
    classes = {name: sum(row["classification"] == name for row in rows) for name in {row["classification"] for row in rows}}
    assert len(rows) == 44
    assert classes == {
        "A_LEGITIMATE_UNKNOWN_INPUT_OMITTED_SCOPE": 43,
        "B_EXPLICIT_INPUT_PARSER_LOSS": 1,
    }
    assert next(row for row in rows if row["classification"].startswith("B_"))["query_id"] == "rq037"
    assert metrics["PRICE_SCOPE_LOST_BEFORE"] == 1
    assert metrics["PRICE_SCOPE_LOST_AFTER"] == 0


def test_versioned_cohorts_and_sidecar_use_only_observed_raw_evidence(reconciliation):
    output, _ = reconciliation
    for name in ("local_pricing_stats_v2.csv", "remote_pricing_stats_v2.csv"):
        with (output / name).open(encoding="utf-8-sig", newline="") as handle:
            assert "price_scope" in next(csv.reader(handle))
    rows = jsonl(output / "pricing_cohort_scope_evidence_v1.jsonl")
    observed = [row for row in rows if row["status"] == "OBSERVED"]
    assert len(observed) == 9
    assert sum(len(row["observations"]) for row in observed) == 14
    assert all(row["raw_rewritten"] is False for row in rows)
    assert all(item["raw_basis"] and item["provenance"] for row in observed for item in row["observations"])


def test_before_after_and_net_drift_are_reproducible(reconciliation):
    output, metrics = reconciliation
    drift = jsonl(output / "price_scope_drift_audit_v1.jsonl")
    assert len(drift) == 19  # 13 regressions and 5 recoveries, plus one changed status with net zero.
    assert sum(row["wrong_interpretation_net_delta"] for row in drift) == 8
    assert metrics["WRONG_INTERPRETATION_BEFORE"] == 27
    assert metrics["WRONG_INTERPRETATION_AFTER"] == 0
    assert metrics["PRICE_SCOPE_MISMATCHES_BEFORE"] == 5
    assert metrics["PRICE_SCOPE_MISMATCHES_AFTER"] == 2
    assert metrics["PRICE_SCOPE_UNKNOWN_SIDE_AFTER"] == 35
    assert metrics["EXPLICIT_NORMALIZATION_RECALL"] == {"numerator": 7, "denominator": 7, "value": 1.0}
    assert metrics["AUTO_PROMOTIONS"] == metrics["NETWORK_REQUESTS"] == metrics["RUNTIME_WRITES"] == 0
