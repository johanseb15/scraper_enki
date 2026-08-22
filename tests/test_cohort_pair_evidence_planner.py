import hashlib
import json
from pathlib import Path

from src.dominio.economic_evidence import DimensionStatus
from src.infraestructura.cohort_pair_evidence_planner import build_cohort_pair_evidence_plan
from src.infraestructura.economic_dimensions_v2_artifact import load_economic_dimensions_v2_sidecar


ROOT = Path(__file__).parents[1]


def build(folder):
    folder.mkdir(parents=True, exist_ok=True)
    outputs = [folder / name for name in (
        "audit.jsonl", "pairs.jsonl", "unlocks.jsonl", "counterfactuals.jsonl",
        "plan.jsonl", "summary.json",
    )]
    metrics = build_cohort_pair_evidence_plan(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        ROOT / "data/economic_dimensions_v2.jsonl",
        ROOT / "data/offer_evidence_v1.jsonl",
        ROOT / "data/offer_evidence_identities_v1.jsonl",
        ROOT / "data/targeted_acquisition_manifest_v1.jsonl",
        *outputs,
    )
    return metrics, outputs


def test_real_visita_cohort_builds_all_bilateral_candidates_and_routes(tmp_path):
    metrics, outputs = build(tmp_path / "one")
    assert metrics["cohort_metrics"] == {
        "OBSERVATIONS": 8, "PROVIDERS": 6, "PAIRS": 28,
        "COMPARABLE_PAIRS": 0, "POTENTIALLY_UNLOCKABLE_PAIRS": 21,
        "CURRENT_PROVIDER_COVERAGE": 0,
        "MAX_PROVIDER_COVERAGE_IF_TOP_ACTIONS_SUCCEED": 6,
        "CURRENT_READINESS": "INSUFFICIENT", "MAX_COUNTERFACTUAL_READINESS": "READY",
    }
    pair_metrics = metrics["pair_metrics"]
    assert pair_metrics["PAIR_HARD_BLOCKED"] == 2
    assert pair_metrics["PAIR_EXPLICIT_MISMATCH"] == 5
    assert pair_metrics["PAIR_MISSING_EVIDENCE"] == 21
    assert pair_metrics["PAIR_COMPARABLE"] == 0
    assert pair_metrics["MIN_UNLOCK_SIZE_4_PLUS"] == 21
    assert metrics["routes"]["FIRST_PAIR"]["pair_ids"] == ["pair:69:146"]
    assert metrics["routes"]["FIRST_PAIR"]["claim_count"] == 8
    assert metrics["routes"]["PARTIAL"]["claim_count"] == 17
    assert metrics["routes"]["READY"]["claim_count"] == 29
    audits = [json.loads(line) for line in outputs[0].read_text(encoding="utf-8").splitlines()]
    assert [item["observation_id"] for item in audits] == ["69", "70", "126", "136", "137", "145", "146", "234"]


def test_real_plan_is_deterministic_reuses_sources_and_has_no_false_positive_network_value(tmp_path):
    first, first_outputs = build(tmp_path / "first")
    second, second_outputs = build(tmp_path / "second")
    assert first == second
    assert [path.read_bytes() for path in first_outputs] == [path.read_bytes() for path in second_outputs]
    plan = [json.loads(line) for line in first_outputs[4].read_text(encoding="utf-8").splitlines()]
    assert len(plan) == 6
    assert all(item["expected_pairs_unlocked"] == 0 for item in plan)
    baires = next(item for item in plan if item["source"] == "bairescloud_generic")
    assert baires["target_observations"] == ["69", "70"]
    assert len(baires["pair_ids_affected"]) > 1
    assert sum(first["cohort_ranking"][0]["score_breakdown"].values()) == first["cohort_ranking"][0]["score"]


def test_planner_preserves_inputs_and_currency_conflicts(tmp_path):
    inputs = [
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/economic_dimensions_v2.jsonl",
        ROOT / "data/offer_evidence_v1.jsonl",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    build(tmp_path / "out")
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    dimensions = load_economic_dimensions_v2_sidecar(ROOT / "data/economic_dimensions_v2.jsonl")
    assert all(dimensions[item].currency.status is DimensionStatus.CONFLICTED for item in ("159", "160", "161"))
