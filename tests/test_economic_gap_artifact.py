import json
from pathlib import Path

from src.infraestructura.economic_gap_artifact import build_gap_register


ROOT = Path(__file__).parents[1]


def test_gap_register_is_deterministic_explainable_and_cardinality_safe(tmp_path):
    one = tmp_path / "one.jsonl"
    two = tmp_path / "two.jsonl"
    metrics = build_gap_register(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        ROOT / "data/economic_dimensions_v2.jsonl",
        one,
    )
    build_gap_register(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        ROOT / "data/economic_dimensions_v2.jsonl",
        two,
    )
    assert one.read_bytes() == two.read_bytes()
    assert metrics["TOTAL_OBSERVATIONS"] == 273
    assert metrics["BLOCKERS"]["MISSING_REACH"] == 272
    assert metrics["PRIORITY_FORMULA"]["HAS_PRICE"] == 2
    rows = [json.loads(line) for line in one.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 273
    assert all("priority_reasons" in row for row in rows)
    assert [int(row["observation_id"]) for row in rows] == list(range(1, 274))
    assert "MISSING_REACH" not in rows[233]["blockers"]
