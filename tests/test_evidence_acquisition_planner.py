import json
from pathlib import Path

from scripts.build_semantic_economic_shadow import build_semantic_economic_shadow
from src.infraestructura.economic_dimensions_v2_adapter import derive_economic_dimensions_v2
from src.infraestructura.evidence_acquisition_planner import (
    _counterfactual,
    build_target_dossier_and_plan,
)


ROOT = Path(__file__).parents[1]


def baseline_shadow(tmp_path):
    output = tmp_path / "baseline-shadow.jsonl"
    build_semantic_economic_shadow(
        ROOT / "data/semantic_normalization_v4.csv",
        output,
        dimensions_path=ROOT / "data/acquisition_baseline_dimensions_v2.jsonl",
    )
    return output


def test_real_targets_have_two_core_blockers_and_counterfactuals_do_not_invent_unlock(tmp_path):
    shadow = baseline_shadow(tmp_path)
    dossier = tmp_path / "dossier.jsonl"; unlock = tmp_path / "unlock.jsonl"; plan = tmp_path / "plan.jsonl"
    metrics = build_target_dossier_and_plan(
        ROOT / "data/semantic_normalization_v4.csv", ROOT / "data/pricing_sources.csv",
        ROOT / "data/acquisition_baseline_dimensions_v2.jsonl", ROOT / "data/acquisition_baseline_gap_register_v1.jsonl",
        shadow, dossier, unlock, plan,
    )
    rows = [json.loads(line) for line in dossier.read_text(encoding="utf-8").splitlines()]
    assert [row["observation_id"] for row in rows] == ["62", "68", "69", "70", "234"]
    assert all({"geographic_reach", "hardware_included"}.issubset(row["missing_core_dimensions"]) for row in rows)
    assert metrics == {"TARGETS_AUDITED": 5, "COUNTERFACTUAL_SCENARIOS": 15, "ACQUISITION_ACTIONS": 10, "UNIQUE_SOURCES": 2, "UNIQUE_URLS": 2, "POTENTIALLY_UNLOCKED_PAIRS": 0}
    scenarios = [json.loads(line) for line in unlock.read_text(encoding="utf-8").splitlines()]
    assert all(item["potentially_unlocked_pairs"] == 0 for item in scenarios)
    assert all(item["remaining_blockers"] for item in scenarios)


def test_planner_is_deterministic_and_score_breakdown_sums_exactly(tmp_path):
    shadow = baseline_shadow(tmp_path)
    outputs = []
    for name in ("a", "b"):
        folder = tmp_path / name; folder.mkdir()
        paths = [folder / f"{kind}.jsonl" for kind in ("dossier", "unlock", "plan")]
        build_target_dossier_and_plan(
            ROOT / "data/semantic_normalization_v4.csv", ROOT / "data/pricing_sources.csv",
            ROOT / "data/acquisition_baseline_dimensions_v2.jsonl", ROOT / "data/acquisition_baseline_gap_register_v1.jsonl",
            shadow, *paths,
        )
        outputs.append([path.read_bytes() for path in paths])
    assert outputs[0] == outputs[1]
    actions = [json.loads(line) for line in (tmp_path / "a/plan.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [item["rank"] for item in actions] == list(range(1, 11))
    assert all(sum(item["score_breakdown"].values()) == item["expected_economic_value"] for item in actions)
    assert all("HARDWARE_SERVICE_BOUNDARY_PENALTY" in item["score_breakdown"] for item in actions)


def test_one_counterfactual_blocker_is_insufficient_but_both_can_unlock():
    rows = {
        observation_id: {
            "observation_id": observation_id,
            "source": source,
            "canonical_service": "SOPORTE_REMOTO",
            "economic_object_raw": "urgencia",
            "semantic_role": "SINGLE_SERVICE",
            "currency": "ARS",
            "price_scope": "PER_HOUR",
        }
        for observation_id, source in (("1", "a"), ("2", "b"))
    }
    dimensions = {
        observation_id: derive_economic_dimensions_v2(row, {})
        for observation_id, row in rows.items()
    }
    reach_only = _counterfactual(rows["1"], dimensions["1"], rows, dimensions, ("geographic_reach",))
    both = _counterfactual(
        rows["1"], dimensions["1"], rows, dimensions,
        ("geographic_reach", "delivery_mode"),
    )
    assert reach_only["potentially_unlocked_pairs"] == 0
    assert "UNKNOWN_DELIVERY_MODE" in reach_only["remaining_blockers"]
    assert both["potentially_unlocked_pairs"] == 1
    assert both["potentially_unlocked_independent_providers"] == 1
