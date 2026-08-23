import json
from pathlib import Path

from scripts.build_commercial_context_single_truth import build_artifact


ROOT = Path(__file__).resolve().parents[1]


def test_commercial_context_artifact_is_deterministic_and_closes_td004():
    generated = build_artifact(ROOT)
    committed = json.loads(
        (ROOT / "data/evaluation/commercial_context_single_truth_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert generated["debt_id"] == "TD-004"
    assert generated["boundary_mismatches_before"] > 0
    assert generated["boundary_mismatches_after"] == 0
    assert generated["trace_engine_parity"]["value"] is True
    assert generated["semantic_drift"]["unexpected_count"] == 0
    assert generated["historical_rows_rewritten"] is False
    assert generated["promotion_authorized"] is False
    assert generated["runtime_learning_writes"] == 0
